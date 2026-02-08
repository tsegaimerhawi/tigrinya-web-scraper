"""Pipeline API: Qdrant status and validation for the integrated UI."""
import json
import os

from fastapi import APIRouter

from app.config import METADATA_PATH, RAW_DATA_PATH, QDRANT_HOST, QDRANT_PORT

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/qdrant-status")
def qdrant_status():
    """Check Qdrant connection and return collections with point counts."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        collections = client.get_collections()
        result = []
        for c in collections.collections:
            info = client.get_collection(c.name)
            result.append({"name": c.name, "points_count": info.points_count})
        return {"ok": True, "host": QDRANT_HOST, "port": QDRANT_PORT, "collections": result}
    except Exception as e:
        return {"ok": False, "error": str(e), "host": QDRANT_HOST, "port": QDRANT_PORT}


@router.get("/validate")
def validate():
    """Return validation summary: pdf_metadata and raw_data counts."""
    out = {"pdf_metadata_count": 0, "completed_downloads": 0, "raw_data_count": 0, "total_words": 0}
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            out["pdf_metadata_count"] = len(meta)
            out["completed_downloads"] = sum(1 for m in meta if m.get("download_status") == "completed")
        except Exception:
            pass
    if os.path.exists(RAW_DATA_PATH):
        try:
            with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            out["raw_data_count"] = len(raw)
            out["total_words"] = sum(r.get("word_count", 0) for r in raw)
        except Exception:
            pass
    return {"ok": True, **out}
