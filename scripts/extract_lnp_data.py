#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_STAGING
from lnp_crawler.db import update_document_status
from lnp_crawler.extraction_patterns import extract_all
from lnp_crawler.state_machine import DocStatus

def main() -> int:
    count = 0
    with open(DATA_STAGING / 'parsed_documents.jsonl', 'r', encoding='utf-8') as src, open(DATA_STAGING / 'extracted_records.jsonl', 'w', encoding='utf-8') as out:
        for line in src:
            rec = json.loads(line)
            merged = {**rec, **extract_all(rec.get('abstract_or_body', ''))}
            out.write(json.dumps(merged, ensure_ascii=False) + '\n')
            update_document_status(rec['document_id'], DocStatus.EXTRACTED.value)
            count += 1
    return count

if __name__ == '__main__':
    main()
