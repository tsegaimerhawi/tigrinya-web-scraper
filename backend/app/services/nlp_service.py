"""NLP utilities for Tigrinya text: word frequency, stats, etc."""
import re
from collections import Counter
from typing import Any


def word_frequency(text: str, top_n: int = 50) -> list[dict]:
    """Return top N words by frequency. Uses simple split on whitespace."""
    if not text or not text.strip():
        return []
    words = re.findall(r"[\u1200-\u137F]+|[a-zA-Z]+|\d+", text)
    words = [w for w in words if len(w) > 1]
    counts = Counter(words)
    return [{"word": w, "count": c} for w, c in counts.most_common(top_n)]


def text_stats(text: str) -> dict[str, Any]:
    """Basic stats: chars, words, lines, Ge'ez vs other."""
    if not text:
        return {"char_count": 0, "word_count": 0, "line_count": 0, "geez_char_count": 0}

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    geez = sum(1 for c in text if "\u1200" <= c <= "\u137F")
    words = re.findall(r"[\u1200-\u137F]+|[a-zA-Z]+|\d+", text)

    return {
        "char_count": len(text),
        "word_count": len(words),
        "line_count": len(lines),
        "geez_char_count": geez,
    }


def extract_sentences(text: str, min_length: int = 10) -> list[str]:
    """Simple sentence split on period/newline. Filters short fragments."""
    if not text:
        return []
    raw = re.split(r"[.\n]+", text)
    return [s.strip() for s in raw if len(s.strip()) >= min_length]


def remove_duplicate_lines(text: str) -> str:
    """Deduplicate consecutive identical lines."""
    if not text:
        return ""
    lines = text.splitlines()
    out = []
    prev = None
    for line in lines:
        if line != prev:
            out.append(line)
            prev = line
    return "\n".join(out)
