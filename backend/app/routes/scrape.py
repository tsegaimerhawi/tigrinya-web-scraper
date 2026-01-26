"""Scrape API: trigger scraping and PDF processing."""
import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from app.services.pdf_service import process_pdfs
from app.services.scraper_service import scrape_articles

router = APIRouter(prefix="/scrape", tags=["scrape"])

# In-memory scrape status (reset on restart)
_scrape_status: dict = {"running": False, "stage": None, "result": None, "error": None}


def _set_status(**kwargs):
    global _scrape_status
    _scrape_status.update(kwargs)


async def _run_scrape(newspaper_id: str, max_articles: int, max_pages: int):
    _set_status(running=True, stage="scraping", result=None, error=None)
    try:
        result = await scrape_articles(
            newspaper_id=newspaper_id,
            max_articles=max_articles,
            max_pages=max_pages,
        )
        _set_status(stage="scraping_done", result=result)
        if result.get("ok") and result.get("successful", 0) > 0:
            _set_status(stage="processing_pdfs")
            pdf_result = process_pdfs()
            _set_status(stage="done", result={**result, "pdf_processing": pdf_result})
        else:
            _set_status(stage="done", result=result)
    except Exception as e:
        _set_status(running=False, stage="error", error=str(e))
        return
    _set_status(running=False)


@router.post("")
async def start_scrape(
    background_tasks: BackgroundTasks,
    newspaper_id: str = "haddas-ertra",
    max_articles: int = 20,
    max_pages: int = 50,
):
    """Start scraping in the background. Poll GET /scrape/status for progress."""
    if _scrape_status.get("running"):
        return {"ok": False, "message": "Scrape already running", "status": _scrape_status}

    background_tasks.add_task(_run_scrape, newspaper_id, max_articles, max_pages)
    return {"ok": True, "message": "Scrape started", "newspaper_id": newspaper_id}


@router.get("/status")
def scrape_status():
    """Current scrape status (running, stage, result, error)."""
    return {"ok": True, **_scrape_status}
