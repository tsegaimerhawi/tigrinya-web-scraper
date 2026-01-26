"""Articles API: list scraped articles and get full text."""
import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.config import METADATA_PATH, RAW_DATA_PATH

router = APIRouter(prefix="/articles", tags=["articles"])


def _load_raw():
    if not os.path.exists(RAW_DATA_PATH):
        return []
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_metadata():
    if not os.path.exists(METADATA_PATH):
        return []
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("")
def list_articles(limit: Optional[int] = 100, offset: Optional[int] = 0):
    """List processed articles (from raw_data)."""
    data = _load_raw()
    total = len(data)
    chunk = data[offset : offset + (limit or 100)]
    for item in chunk:
        item.pop("extracted_text", None)
    return {"articles": chunk, "total": total, "limit": limit or 100, "offset": offset}


@router.get("/metadata")
def list_metadata():
    """Raw metadata from last scrape (including failed downloads)."""
    return {"metadata": _load_metadata()}


@router.get("/{index}/text")
def get_article_text(index: int):
    """Get full extracted text for an article (for copying)."""
    data = _load_raw()
    for item in data:
        if item.get("index") == index:
            return {
                "index": index,
                "news_title": item.get("news_title"),
                "article_url": item.get("article_url"),
                "extracted_text": item.get("extracted_text", ""),
                "word_count": item.get("word_count", 0),
            }
    raise HTTPException(status_code=404, detail="Article not found")
