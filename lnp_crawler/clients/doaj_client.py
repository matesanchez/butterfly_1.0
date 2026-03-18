import time, requests
from typing import List, Dict
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import generic_queries
BASE = "https://doaj.org/api/search/articles"

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        r = requests.get(f'{BASE}/{query}', params={'pageSize': min(max_results,25)}, timeout=REQUEST_TIMEOUT_SECONDS, verify=VERIFY_SSL)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('results', []):
            bib = art.get('bibjson') or {}
            doi = next((i.get('id') for i in bib.get('identifier', []) if i.get('type') == 'doi'), None)
            uid = doi or bib.get('title')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            link = bib.get('link', [{}])
            docs.append({'source_name':'DOAJ','external_id':uid,'title':bib.get('title') or 'Unknown','doi':doi,'pmid':None,'pmcid':None,'journal_or_site':(bib.get('journal') or {}).get('title'),'publication_date':bib.get('year'),'source_url':link[0].get('url') if link else None,'abstract_text':bib.get('abstract')})
    return docs
