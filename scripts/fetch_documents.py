#!/usr/bin/env python3
import argparse, hashlib, json, sys, requests
from pathlib import Path
from typing import Optional
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_RAW
from lnp_crawler.db import get_connection, get_documents_by_status, update_document_status
from lnp_crawler.state_machine import DocStatus
from lnp_crawler.clients.pmc_client import fetch_fulltext_xml
from lnp_crawler.clients.unpaywall_client import get_oa_url

def main(limit: Optional[int] = None) -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    docs = get_documents_by_status(DocStatus.DISCOVERED.value)
    if limit:
        docs = docs[:limit]
    
    fetched = 0
    failed = 0
    total = len(docs)
    
    for idx, doc in enumerate(docs, 1):
        doc_id = doc['id']
        # Handle both dict and sqlite3.Row objects
        try:
            title = doc['title'][:50] if doc['title'] else 'Untitled'
        except (KeyError, TypeError):
            title = 'Untitled'
        print(f"   [{idx}/{total}] Fetching: {title}...", flush=True, end='\r')
        
        raw_path = DATA_RAW / f'{doc_id}.json'
        try:
            content = None
            content_type = 'abstract_only'
            if doc['pmcid']:
                content = fetch_fulltext_xml(doc['pmcid'])
                if content:
                    content_type = 'pmc_xml'
            if not content and doc['doi']:
                oa_url = get_oa_url(doc['doi'])
                if oa_url:
                    r = requests.get(oa_url, timeout=30)
                    r.raise_for_status()
                    content = r.text
                    content_type = 'oa_landing_or_fulltext'
            payload = {'document_id': doc_id, 'doi': doc['doi'], 'pmcid': doc['pmcid'], 'abstract': doc['abstract_text'], 'fulltext': content, 'content_type': content_type}
            serialized = json.dumps(payload, ensure_ascii=False)
            raw_path.write_text(serialized, encoding='utf-8')
            raw_hash = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
            with get_connection() as conn:
                conn.execute('UPDATE documents SET raw_hash = ?, full_text_path = ? WHERE id = ?', (raw_hash, str(raw_path), doc_id))
            update_document_status(doc_id, DocStatus.FETCHED.value)
            fetched += 1
        except Exception as e:
            update_document_status(doc_id, DocStatus.FAILED.value)
            failed += 1
    
    print(f"   ✓ Fetched {fetched}/{total} documents ({failed} failed)" + " " * 60, flush=True)
    return fetched

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int)
    args = ap.parse_args()
    main(limit=args.limit)
