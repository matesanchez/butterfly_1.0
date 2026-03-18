#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_NORMALIZED, DATA_STAGING
from lnp_crawler.normalization import normalize_record

def main() -> int:
    DATA_NORMALIZED.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(DATA_STAGING / 'extracted_records.jsonl', 'r', encoding='utf-8') as src, open(DATA_NORMALIZED / 'normalized_records.jsonl', 'w', encoding='utf-8') as out:
        for line in src:
            out.write(json.dumps(normalize_record(json.loads(line)), ensure_ascii=False) + '\n')
            count += 1
    return count

if __name__ == '__main__':
    main()
