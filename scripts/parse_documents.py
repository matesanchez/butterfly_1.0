#!/usr/bin/env python3
import json, sys
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_RAW, DATA_STAGING
from lnp_crawler.db import get_documents_by_status, update_document_status
from lnp_crawler.state_machine import DocStatus
from lnp_crawler.text_cleaning import clean, extract_sections

def parse_raw(payload: dict) -> dict:
    abstract = clean(payload.get('abstract') or '')
    full = payload.get('fulltext') or ''
    if full.strip().startswith('<'):
        full = BeautifulSoup(full, 'lxml').get_text(separator=' ')
    full = clean(full)
    combined = ' '.join(part for part in [abstract, full] if part).strip()
    return {'abstract_or_body': combined, 'sections': extract_sections(combined)}

def main(limit: Optional[int] = None) -> int:
    DATA_STAGING.mkdir(parents=True, exist_ok=True)
    docs = get_documents_by_status(DocStatus.FETCHED.value)
    if limit:
        docs = docs[:limit]
    
    count = 0
    total = len(docs)
    print(f"   Processing: {total} documents", flush=True)
    
    with open(DATA_STAGING / 'parsed_documents.jsonl', 'w', encoding='utf-8') as out:
        for idx, doc in enumerate(docs, 1):
            if idx % max(1, total // 10) == 0 or idx == total or idx == 1:
                print(f"   [{idx}/{total}] Parsing documents...", flush=True, end='\r')
            
            payload = json.loads((DATA_RAW / f"{doc['id']}.json").read_text(encoding='utf-8'))
            record = {'document_id': doc['id'], 'title': doc['title'], 'doi': doc['doi'], **parse_raw(payload)}
            out.write(json.dumps(record, ensure_ascii=False) + '\n')
            update_document_status(doc['id'], DocStatus.PARSED.value)
            count += 1
    
    print(f"   ✓ Parsed {count} documents" + " " * 40, flush=True)
    return count

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int)
    args = ap.parse_args()
    main(limit=args.limit)
