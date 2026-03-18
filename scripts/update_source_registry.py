#!/usr/bin/env python3
from datetime import datetime, timezone
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.db import get_connection
from lnp_crawler.source_registry import load_registry, save_registry

def main() -> list[dict]:
    registry = load_registry()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT s.name, COUNT(d.id) AS doc_count "
            "FROM sources s LEFT JOIN documents d ON d.source_id = s.id "
            "GROUP BY s.name"
        ).fetchall()
        counts = {row["name"]: row["doc_count"] for row in rows}

    now = datetime.now(timezone.utc).isoformat()
    for src in registry:
        src_name = src.get("source")
        src["crawled"] = True
        src["last_crawled_at"] = now
        src["new_entries_from_last_crawl"] = int(counts.get(src_name, 0))

    save_registry(registry)
    return registry

if __name__ == '__main__':
    main()
