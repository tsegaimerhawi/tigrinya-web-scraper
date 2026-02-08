"""Process API: manually trigger PDF text extraction and AI analysis."""
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, BackgroundTasks

from app.services.pdf_service import process_pdfs

router = APIRouter(prefix="/process", tags=["process"])

# In-memory processing status
_process_status: dict = {"running": False, "stage": None, "result": None, "error": None}


class ProcessRequest(BaseModel):
    filenames: List[str]  # List of PDF filenames to process


def _set_status(**kwargs):
    global _process_status
    _process_status.update(kwargs)


async def _run_processing(filenames: Optional[List[str]]):
    _set_status(running=True, stage="processing", result=None, error=None)
    try:
        result = process_pdfs(pdf_filenames=filenames)
        _set_status(stage="done", result=result)
    except Exception as e:
        _set_status(running=False, stage="error", error=str(e))
        return
    _set_status(running=False)


@router.post("")
async def start_processing(
    background_tasks: BackgroundTasks,
    request: ProcessRequest
):
    """Start PDF processing in the background for selected files."""
    if _process_status.get("running"):
        return {"ok": False, "message": "Processing already running", "status": _process_status}

    if not request.filenames:
        return {"ok": False, "message": "No files specified"}

    background_tasks.add_task(_run_processing, request.filenames)
    return {"ok": True, "message": f"Processing {len(request.filenames)} PDFs", "count": len(request.filenames)}


@router.post("/all")
async def start_processing_all(background_tasks: BackgroundTasks):
    """Process all PDFs from metadata in the background (extract text, NER, image descriptions)."""
    if _process_status.get("running"):
        return {"ok": False, "message": "Processing already running", "status": _process_status}
    background_tasks.add_task(_run_processing, None)
    return {"ok": True, "message": "Processing all PDFs from metadata"}


@router.get("/status")
def processing_status():
    """Current processing status."""
    return {"ok": True, **_process_status}
