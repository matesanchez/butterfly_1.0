#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_NORMALIZED
from lnp_crawler.dedupe import deduplicate_records

def main() -> int:
    records = [json.loads(line) for line in (DATA_NORMALIZED / 'normalized_records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    deduped = deduplicate_records(records)
    with open(DATA_NORMALIZED / 'deduped_records.jsonl', 'w', encoding='utf-8') as out:
        for rec in deduped:
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return len(deduped)

if __name__ == '__main__':
    main()
