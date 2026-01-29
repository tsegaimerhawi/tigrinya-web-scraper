"""Scrape API: trigger scraping and PDF downloading."""
import asyncio
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, BackgroundTasks

from app.services.scraper_service import scrape_articles

router = APIRouter(prefix="/scrape", tags=["scrape"])

# In-memory scrape status (reset on restart)
_scrape_status: dict = {"running": False, "stage": None, "progress": None, "result": None, "error": None}


class ScrapeRequest(BaseModel):
    newspaper_id: str = "haddas-ertra"
    max_articles: int = 100
    max_pages: int = 100
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def _set_status(**kwargs):
    global _scrape_status
    _scrape_status.update(kwargs)


async def _run_scrape(newspaper_id: str, max_articles: int, max_pages: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    _set_status(running=True, stage="initializing", progress=None, result=None, error=None)
    try:
        result = await scrape_articles(
            newspaper_id=newspaper_id,
            max_articles=max_articles,
            max_pages=max_pages,
            start_date=start_date,
            end_date=end_date,
            progress_callback=lambda p: _set_status(stage=p.get("stage"), progress=p)
        )
        _set_status(stage="download_complete", result=result, progress=None)
    except Exception as e:
        _set_status(running=False, stage="error", error=str(e))
        return
    _set_status(running=False)


@router.post("")
async def start_scrape(
    background_tasks: BackgroundTasks,
    request: ScrapeRequest
):
    """Start scraping in the background. Poll GET /scrape/status for progress."""
    if _scrape_status.get("running"):
        return {"ok": False, "message": "Scrape already running", "status": _scrape_status}

    background_tasks.add_task(
        _run_scrape, 
        request.newspaper_id, 
        request.max_articles, 
        request.max_pages,
        request.start_date,
        request.end_date
    )
    return {"ok": True, "message": "Scrape started", "newspaper_id": request.newspaper_id}


@router.get("/status")
def scrape_status():
    """Current scrape status (running, stage, result, error)."""
    return {"ok": True, **_scrape_status}
