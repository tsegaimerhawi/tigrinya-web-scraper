"""
Tigrinya retriever: semantic search over Qdrant using Gemini embeddings.
Compatible with LlamaIndex-stored payloads (text in node content).
"""
import os
from typing import List, Dict, Any, Optional

from app.config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION


def _get_api_key() -> Optional[str]:
    from dotenv import load_dotenv
    from app.config import BASE_DIR
    load_dotenv(os.path.join(BASE_DIR, "config.env"))
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def search(
    query: str,
    k: int = 5,
    collection_name: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search: embed query, search Qdrant, return list of {text, score, metadata}.
    """
    from qdrant_client import QdrantClient
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    api_key = _get_api_key()
    if not api_key:
        return []

    collection_name = collection_name or QDRANT_COLLECTION
    qdrant_host = qdrant_host or QDRANT_HOST
    qdrant_port = qdrant_port or QDRANT_PORT

    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key,
        )
        query_vector = embeddings.embed_query(query)
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=k,
        ).points
    except Exception:
        return []

    out = []
    for point in results:
        payload = point.payload or {}
        # LlamaIndex stores text in different ways; support common keys
        text = (
            payload.get("text")
            or payload.get("original_text")
            or (payload.get("_node_content") and _node_content_to_text(payload["_node_content"]))
            or ""
        )
        out.append({
            "score": getattr(point, "score", 0.0),
            "text": text,
            "metadata": {k: v for k, v in payload.items() if not k.startswith("_")},
            "id": str(point.id),
        })
    return out


def _node_content_to_text(node_content: str) -> str:
    """Extract text from LlamaIndex node content JSON if present."""
    try:
        import json
        data = json.loads(node_content)
        return data.get("text", data.get("content", ""))
    except Exception:
        return ""
