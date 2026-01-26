"""NLP API: word frequency, stats, etc. on provided text or article."""
import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import RAW_DATA_PATH
from app.services.nlp_service import (
    extract_sentences,
    remove_duplicate_lines,
    text_stats,
    word_frequency,
)

router = APIRouter(prefix="/nlp", tags=["nlp"])


def _load_raw() -> list:
    if not os.path.exists(RAW_DATA_PATH):
        return []
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TextInput(BaseModel):
    text: str


class NLPWordFreqRequest(BaseModel):
    text: Optional[str] = None
    article_index: Optional[int] = None
    top_n: int = 50


@router.post("/word-frequency")
def nlp_word_frequency(body: NLPWordFreqRequest):
    """Top N words by frequency. Provide text directly or article_index to use stored article."""
    text = body.text
    if not text and body.article_index is not None:
        data = _load_raw()
        for item in data:
            if item.get("index") == body.article_index:
                text = item.get("extracted_text", "")
                break
        if not text:
            raise HTTPException(status_code=404, detail="Article not found")
    if not text:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'article_index'")
    return {"ok": True, "data": word_frequency(text, body.top_n)}


@router.post("/stats")
def nlp_stats(body: TextInput):
    """Character, word, line, and Ge'ez counts."""
    return {"ok": True, "data": text_stats(body.text)}


@router.post("/sentences")
def nlp_sentences(body: TextInput, min_length: int = 10):
    """Extract sentences (simple split)."""
    return {"ok": True, "data": extract_sentences(body.text, min_length)}


@router.post("/dedupe-lines")
def nlp_dedupe_lines(body: TextInput):
    """Remove consecutive duplicate lines."""
    return {"ok": True, "data": remove_duplicate_lines(body.text)}
