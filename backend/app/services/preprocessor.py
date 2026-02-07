"""Tigrinya text preprocessor: sentence splitting for ingestion."""
import re
from typing import List


def split_into_sentences(text: str, min_words: int = 5) -> List[str]:
    """
    Split Tigrinya text into sentences.
    Uses Ethiopic full stop (።) and standard punctuation.
    Filters out fragments with fewer than min_words words.
    """
    if not text or not text.strip():
        return []

    # Tigrinya sentence delimiters
    sentence_pattern = r"[።?!.]+\s*"
    parts = re.split(f"({sentence_pattern})", text)
    sentences = []
    current = ""

    for part in parts:
        if not part:
            continue
        current += part
        if re.match(sentence_pattern, part):
            sent = current.strip()
            if _is_valid_sentence(sent, min_words):
                sentences.append(sent)
            current = ""

    remaining = current.strip()
    if _is_valid_sentence(remaining, min_words):
        sentences.append(remaining)

    return sentences


def _is_valid_sentence(sentence: str, min_words: int) -> bool:
    if not sentence:
        return False
    if re.match(r"^[.\-\s።?!,:'\"]+$", sentence):
        return False
    words = sentence.split()
    if len(words) < min_words:
        return False
    geez = sum(1 for c in sentence if "\u1200" <= c <= "\u137F")
    return geez >= 10
