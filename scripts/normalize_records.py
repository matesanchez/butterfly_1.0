#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp_crawler.config import DATA_NORMALIZED, DATA_STAGING  # noqa: E402
from lnp_crawler.normalization import normalize_record  # noqa: E402

def main() -> int:
    DATA_NORMALIZED.mkdir(parents=True, exist_ok=True)
    
    # Count records first
    total = sum(1 for _ in open(DATA_STAGING / 'extracted_records.jsonl', 'r', encoding='utf-8'))
    print(f"   Normalizing: {total} records", flush=True)
    
    count = 0
    with open(DATA_STAGING / 'extracted_records.jsonl', 'r', encoding='utf-8') as src, open(DATA_NORMALIZED / 'normalized_records.jsonl', 'w', encoding='utf-8') as out:
        for idx, line in enumerate(src, 1):
            if idx % max(1, total // 10) == 0 or idx == total or idx == 1:
                print(f"   [{idx}/{total}] Normalizing records...", flush=True, end='\r')
            out.write(json.dumps(normalize_record(json.loads(line)), ensure_ascii=False) + '\n')
            count += 1
    
    print(f"   ✓ Normalized {count} records" + " " * 40, flush=True)
    return count

if __name__ == '__main__':
    main()
