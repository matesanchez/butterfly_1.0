#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_NORMALIZED
from lnp_crawler.dedupe import deduplicate_records

def main() -> int:
    print("   Loading records for deduplication...", flush=True, end='\r')
    records = [json.loads(line) for line in (DATA_NORMALIZED / 'normalized_records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    print(f"   Deduplicating: {len(records)} records", flush=True)
    
    deduped = deduplicate_records(records)
    print(f"   ✓ Deduplicated {len(deduped)} records (removed {len(records) - len(deduped)} duplicates)" + " " * 30, flush=True)
    
    with open(DATA_NORMALIZED / 'deduped_records.jsonl', 'w', encoding='utf-8') as out:
        for rec in deduped:
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return len(deduped)

if __name__ == '__main__':
    main()
