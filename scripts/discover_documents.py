#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from typing import Optional
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_STAGING, MAX_RESULTS_PER_SOURCE
from lnp_crawler.db import upsert_document, upsert_source
from lnp_crawler.source_registry import load_registry
from lnp_crawler.clients import biorxiv_client, crossref_client, doaj_client, europepmc_client, medrxiv_client, openalex_client, pubmed_client, semanticscholar_client

DISCOVERY_SOURCES = {
    'PubMed', 'Europe PMC', 'bioRxiv', 'medRxiv',
    'Crossref', 'OpenAlex', 'Semantic Scholar', 'DOAJ'
}

CLIENTS = {'PubMed': pubmed_client, 'Europe PMC': europepmc_client, 'bioRxiv': biorxiv_client, 'medRxiv': medrxiv_client, 'Crossref': crossref_client, 'OpenAlex': openalex_client, 'Semantic Scholar': semanticscholar_client, 'DOAJ': doaj_client}

def main(limit: Optional[int] = None, source_filter: Optional[str] = None) -> int:
    registry = load_registry()
    total = 0
    DATA_STAGING.mkdir(parents=True, exist_ok=True)
    out_path = DATA_STAGING / 'discovered_documents.jsonl'
    mode = 'a' if out_path.exists() else 'w'
    
    # Count sources to discover from
    sources_to_query = []
    for src in registry:
        name = src.get('source')
        if source_filter and name != source_filter:
            continue
        if name not in DISCOVERY_SOURCES:
            continue
        if name not in CLIENTS:
            continue
        sources_to_query.append((name, src))
    
    with open(out_path, mode, encoding='utf-8') as out:
        for idx, (name, src) in enumerate(sources_to_query, 1):
            print(f"   [{idx}/{len(sources_to_query)}] Querying: {name}...", flush=True)
            client = CLIENTS.get(name)
            source_id = upsert_source(name, src.get('homepage'), src.get('api_url'))
            
            try:
                docs_found = 0
                for doc in client.discover(max_results=limit or MAX_RESULTS_PER_SOURCE):
                    doc['source_id'] = source_id
                    doc['pipeline_status'] = 'DISCOVERED'
                    doc['document_id'] = upsert_document(doc)
                    out.write(json.dumps(doc, ensure_ascii=False) + '\n')
                    total += 1
                    docs_found += 1
                print(f"       ✓ Found {docs_found} documents", flush=True)
            except Exception as e:
                print(f"       ✗ Error: {e}", flush=True)
                continue
    
    return total

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int)
    ap.add_argument('--source')
    args = ap.parse_args()
    main(limit=args.limit, source_filter=args.source)
