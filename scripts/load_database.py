#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_NORMALIZED
from lnp_crawler.db import insert_lnp_record, update_document_status
from lnp_crawler.state_machine import DocStatus

def main() -> int:
    # Count records first
    total = sum(1 for _ in open(DATA_NORMALIZED / 'deduped_records.jsonl', 'r', encoding='utf-8'))
    print(f"   Loading: {total} records into database", flush=True)
    
    count = 0
    with open(DATA_NORMALIZED / 'deduped_records.jsonl', 'r', encoding='utf-8') as fh:
        for idx, line in enumerate(fh, 1):
            if idx % max(1, total // 10) == 0 or idx == total or idx == 1:
                print(f"   [{idx}/{total}] Loading records...", flush=True, end='\r')
            rec = json.loads(line)
            insert_lnp_record(rec)
            update_document_status(rec['document_id'], DocStatus.LOADED.value)
            count += 1
    
    print(f"   ✓ Loaded {count} records" + " " * 40, flush=True)
    return count

if __name__ == '__main__':
    main()
