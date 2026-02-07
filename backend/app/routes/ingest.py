"""Ingest API: trigger LlamaIndex ingestion into Qdrant."""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ingest_service import run_ingestion

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    limit: Optional[int] = None
    batch_size: int = 50
    batch_delay_seconds: int = 60
    collection_name: Optional[str] = None
    qdrant_host: Optional[str] = None
    qdrant_port: Optional[int] = None


@router.post("")
def start_ingest(request: IngestRequest):
    """Run LlamaIndex ingestion: raw_data.json -> embed -> Qdrant."""
    result = run_ingestion(
        limit=request.limit,
        batch_size=request.batch_size,
        batch_delay_seconds=request.batch_delay_seconds,
        collection_name=request.collection_name,
        qdrant_host=request.qdrant_host,
        qdrant_port=request.qdrant_port,
    )
    return result
