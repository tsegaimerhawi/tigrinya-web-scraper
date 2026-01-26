"""PDF processing: extract and clean Ge'ez text."""
import json
import os
import re
from typing import Tuple

import pdfplumber

from app.config import METADATA_PATH, RAW_DATA_PATH


def clean_text(text: str) -> str:
    """Clean extracted text: keep Ge'ez, numbers, punctuation; remove English and noise."""
    if not text:
        return ""

    noise = [
        r"PAGE\s+\d+", r"page\s+\d+", r"waga\s+[\d.]+", r"ዋጋ\s+[\d.]+",
        r"ISSUE\s+\d+", r"VOL\s+\d+", r"VOLUME\s+\d+",
        r"\d{1,2}/\d{1,2}/\d{4}", r"\d{4}-\d{2}-\d{2}",
        r"©\s*\d{4}", r"All rights reserved", r"http[s]?://\S+", r"www\.\S+",
    ]
    for p in noise:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[a-zA-Z]+\b", "", text)

    nav = [r"•", r"▪", r"&", r"±±", r"——", r"\(\([^)]*\)\)", r"\b\d+\s*[a-zA-Z]+\b"]
    lines = text.split("\n")
    kept = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        special = sum(1 for c in line if c in "•●○■□▪▫▲▼◄►◆◇◈◉◊※‹›«»\"\"''±——&()[]{}")
        total = len(line.replace(" ", ""))
        if total > 0 and special / total > 0.15:
            continue
        if len(line) < 10:
            geez = sum(1 for c in line if "\u1200" <= c <= "\u137F")
            if geez < 3:
                continue
        for p in nav:
            line = re.sub(p, "", line)
        if line.strip():
            kept.append(line)

    text = "\n".join(kept)
    allowed = r"[\u1200-\u137F\u0000-\u007F\u2000-\u206F]"
    text = re.sub(f"[^{allowed}]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int]:
    """Extract and clean text from PDF. Returns (cleaned_text, word_count)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full = ""
            for page in pdf.pages:
                try:
                    t = page.extract_text()
                    if t:
                        full += t + "\n"
                except Exception:
                    continue
            cleaned = clean_text(full)
            words = [w for w in cleaned.split() if w.strip()]
            return cleaned, len(words)
    except Exception:
        return "", 0


def process_pdfs() -> dict:
    """Process all completed PDFs from metadata, write raw_data.json. Returns summary."""
    if not os.path.exists(METADATA_PATH):
        return {"ok": False, "error": "No metadata found", "processed": 0}

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    completed = [m for m in metadata if m.get("download_status") == "completed"]
    processed = []

    for item in completed:
        path = item.get("pdf_filepath")
        if not path or not os.path.exists(path):
            continue
        fn = item.get("pdf_filename", "")
        title = fn.split("_", 1)[1].replace(".pdf", "") if "_" in fn else fn.replace(".pdf", "")

        text, wc = extract_text_from_pdf(path)
        processed.append({
            "index": item.get("index"),
            "news_title": title,
            "article_url": item.get("article_url"),
            "publication_date": item.get("date"),
            "pdf_filename": fn,
            "pdf_url": item.get("pdf_url"),
            "extracted_text": text,
            "word_count": wc,
            "processing_status": "completed",
        })

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    total_words = sum(p["word_count"] for p in processed)
    return {
        "ok": True,
        "processed": len(processed),
        "total_words": total_words,
        "raw_data_path": RAW_DATA_PATH,
    }
