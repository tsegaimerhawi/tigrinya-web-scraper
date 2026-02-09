"""
LlamaIndex ingestion: load processed raw_data.json, chunk into sentences,
embed with Google GenAI, store in Qdrant.
"""
import json
import os
from typing import List, Optional

from app.config import (
    BASE_DIR,
    RAW_DATA_PATH,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
)
from app.services.preprocessor import split_into_sentences


def _get_api_key() -> Optional[str]:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, "config.env"))
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def load_raw_data(path: Optional[str] = None) -> List[dict]:
    """Load processed articles from raw_data.json."""
    path = path or RAW_DATA_PATH
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_documents_from_raw(
    raw_data: List[dict],
    limit: Optional[int] = None,
    min_words_per_sentence: int = 5,
) -> List["Document"]:
    """Build LlamaIndex Documents from raw_data (one doc per sentence with metadata)."""
    from llama_index.core import Document

    articles = raw_data[:limit] if limit else raw_data
    documents = []
    for item in articles:
        text = item.get("extracted_text") or ""
        if not text.strip():
            continue
        sentences = split_into_sentences(text, min_words=min_words_per_sentence)
        for i, sent in enumerate(sentences):
            if not sent.strip():
                continue
            meta = {
                "article_index": item.get("index", 0),
                "news_title": item.get("news_title", ""),
                "article_url": item.get("article_url", ""),
                "publication_date": item.get("publication_date", ""),
                "pdf_filename": item.get("pdf_filename", ""),
                "sentence_index": i,
            }
            documents.append(Document(text=sent, metadata=meta))
    return documents


def run_ingestion(
    raw_data_path: Optional[str] = None,
    collection_name: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
    limit: Optional[int] = None,
    batch_size: int = 50,
    batch_delay_seconds: int = 60,
) -> dict:
    """
    Run full LlamaIndex ingestion: load raw_data -> build documents -> embed -> store in Qdrant.
    Returns summary dict with ok, count, error.
    """
    raw_data_path = raw_data_path or RAW_DATA_PATH
    collection_name = collection_name or QDRANT_COLLECTION
    qdrant_host = qdrant_host or QDRANT_HOST
    qdrant_port = qdrant_port or QDRANT_PORT

    api_key = _get_api_key()
    if not api_key or api_key == "your_api_key_here":
        return {"ok": False, "error": "GOOGLE_API_KEY (or GEMINI_API_KEY) not set", "count": 0}

    raw_data = load_raw_data(raw_data_path)
    if not raw_data:
        return {"ok": False, "error": "No raw_data.json found or empty. Run scraper and process first.", "count": 0}

    try:
        from llama_index.core import Document, VectorStoreIndex, Settings
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
    except ImportError as e:
        return {"ok": False, "error": f"Missing dependency: {e}", "count": 0}

    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
    except Exception as e:
        return {"ok": False, "error": f"Cannot connect to Qdrant at {qdrant_host}:{qdrant_port}: {e}", "count": 0}

    embed_model = GoogleGenAIEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=api_key,
    )
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

    try:
        test_embedding = embed_model.get_text_embedding("test")
        actual_dim = len(test_embedding)
    except Exception:
        actual_dim = 3072

    collections = client.get_collections()
    if collection_name not in [c.name for c in collections.collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=actual_dim, distance=Distance.COSINE),
        )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        enable_hybrid=False,
    )

    documents = build_documents_from_raw(raw_data, limit=limit)
    if not documents:
        return {"ok": False, "error": "No documents to ingest (no valid sentences)", "count": 0}

    total_batches = (len(documents) + batch_size - 1) // batch_size
    import time
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(documents))
        batch_docs = documents[start_idx:end_idx]
        try:
            VectorStoreIndex.from_documents(
                batch_docs,
                vector_store=vector_store,
                show_progress=False,
            )
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(batch_delay_seconds)
                try:
                    VectorStoreIndex.from_documents(
                        batch_docs,
                        vector_store=vector_store,
                        show_progress=False,
                    )
                except Exception as e2:
                    return {"ok": False, "error": str(e2), "count": start_idx}
            else:
                return {"ok": False, "error": str(e), "count": start_idx}
        if batch_num < total_batches - 1:
            time.sleep(batch_delay_seconds)

    info = client.get_collection(collection_name)
    return {
        "ok": True,
        "count": len(documents),
        "points_count": info.points_count,
        "collection": collection_name,
    }
