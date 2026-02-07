#!/usr/bin/env python3
"""Validate raw_data.json and pdf_metadata.json."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("TIGRINYA_DATA_DIR", ROOT)
RAW_PATH = os.path.join(DATA_DIR, "raw_data.json")
META_PATH = os.path.join(DATA_DIR, "pdf_metadata.json")

def main():
    print("Validating results...")
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        completed = sum(1 for m in meta if m.get("download_status") == "completed")
        print(f"  pdf_metadata.json: {len(meta)} entries, {completed} completed")
    else:
        print("  pdf_metadata.json: not found")
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        total_words = sum(r.get("word_count", 0) for r in raw)
        print(f"  raw_data.json: {len(raw)} articles, {total_words} total words")
    else:
        print("  raw_data.json: not found")

if __name__ == "__main__":
    main()
