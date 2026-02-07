#!/usr/bin/env python3
"""Check Qdrant connection and list collections."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def _get_host_port():
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = int(os.environ.get("QDRANT_PORT", "6333"))
    config_path = os.path.join(ROOT, "runner_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            host = cfg.get("qdrant_host", host)
            port = int(cfg.get("qdrant_port", port))
        except Exception:
            pass
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    return host, port


def main():
    host, port = _get_host_port()
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        print(f"✅ Qdrant at {host}:{port}")
        for c in collections.collections:
            info = client.get_collection(c.name)
            print(f"   - {c.name}: {info.points_count} points")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant at {host}:{port}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
