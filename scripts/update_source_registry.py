#!/usr/bin/env python3
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import List, Dict
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.db import get_connection
from lnp_crawler.source_registry import load_registry, save_registry

def main() -> List[Dict]:
    print("   Updating source registry...", flush=True, end='\r')
    registry = load_registry()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT s.name, COUNT(d.id) AS doc_count "
            "FROM sources s LEFT JOIN documents d ON d.source_id = s.id "
            "GROUP BY s.name"
        ).fetchall()
        counts = {row["name"]: row["doc_count"] for row in rows}

    now = datetime.now(timezone.utc).isoformat()
    total_docs = 0
    for src in registry:
        src_name = src.get("source")
        src["crawled"] = True
        src["last_crawled_at"] = now
        doc_count = int(counts.get(src_name, 0))
        src["new_entries_from_last_crawl"] = doc_count
        total_docs += doc_count

    save_registry(registry)
    print(f"   ✓ Registry updated with {total_docs} total documents from {len(registry)} sources" + " " * 30, flush=True)
    return registry

if __name__ == '__main__':
    main()
