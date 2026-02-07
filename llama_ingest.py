#!/usr/bin/env python3
"""
LlamaIndex ingestion: load raw_data.json, embed with Gemini, store in Qdrant.
Run from project root. Uses backend ingest service.
"""
import argparse
import json
import os
import sys

# Run from repo root; backend is sibling to this script
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "backend"))

os.chdir(ROOT)
# Data dir: same as backend default (project root)
DATA_DIR = os.environ.get("TIGRINYA_DATA_DIR", ROOT)
os.environ.setdefault("TIGRINYA_DATA_DIR", DATA_DIR)


def main():
    parser = argparse.ArgumentParser(description="LlamaIndex Tigrinya ingestion into Qdrant")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of articles")
    parser.add_argument("--pdf-dir", default="pdfs", help="PDF directory (unused; for compat)")
    parser.add_argument("--collection", default=None, help="Qdrant collection name")
    parser.add_argument("--qdrant-host", default=None, help="Qdrant host")
    parser.add_argument("--qdrant-port", type=int, default=None, help="Qdrant port")
    parser.add_argument("--batch-size", type=int, default=50, help="Documents per batch")
    parser.add_argument("--batch-delay", type=int, default=60, help="Delay between batches (seconds)")
    args = parser.parse_args()

    # Optional: load runner_config.json for script-runner compatibility
    config_path = os.path.join(ROOT, "runner_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if args.qdrant_host is None:
                args.qdrant_host = cfg.get("qdrant_host", "localhost")
            if args.qdrant_port is None:
                args.qdrant_port = int(cfg.get("qdrant_port", 6333))
            if args.collection is None:
                args.collection = cfg.get("collection_llamaindex", "tigrinya_llamaindex")
        except Exception:
            pass

    from app.services.ingest_service import run_ingestion

    result = run_ingestion(
        raw_data_path=os.path.join(DATA_DIR, "raw_data.json"),
        collection_name=args.collection or os.environ.get("QDRANT_COLLECTION", "tigrinya_llamaindex"),
        qdrant_host=args.qdrant_host or os.environ.get("QDRANT_HOST", "localhost"),
        qdrant_port=args.qdrant_port or int(os.environ.get("QDRANT_PORT", "6333")),
        limit=args.limit,
        batch_size=args.batch_size,
        batch_delay_seconds=args.batch_delay,
    )

    if result.get("ok"):
        print(f"✅ Ingested {result.get('count', 0)} documents into {result.get('collection', '')}")
        print(f"   Points in Qdrant: {result.get('points_count', 0)}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
