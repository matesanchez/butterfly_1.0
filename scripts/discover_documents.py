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
    with open(out_path, mode, encoding='utf-8') as out:
        for src in registry:
            name = src.get('source')
            if source_filter and name != source_filter:
                continue
            if name not in DISCOVERY_SOURCES:
                continue
            client = CLIENTS.get(name)
            if not client:
                continue
            source_id = upsert_source(name, src.get('homepage'), src.get('api_url'))
            for doc in client.discover(max_results=limit or MAX_RESULTS_PER_SOURCE):
                doc['source_id'] = source_id
                doc['pipeline_status'] = 'DISCOVERED'
                doc['document_id'] = upsert_document(doc)
                out.write(json.dumps(doc, ensure_ascii=False) + '\n')
                total += 1
    return total

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int)
    ap.add_argument('--source')
    args = ap.parse_args()
    main(limit=args.limit, source_filter=args.source)
