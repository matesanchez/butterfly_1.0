import time, requests
from typing import List, Dict
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import generic_queries
BASE = "https://api.biorxiv.org"

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        q = query.replace(' ', '%20')
        r = requests.get(f'{BASE}/details/medrxiv/{q}/0/{min(max_results,25)}', timeout=REQUEST_TIMEOUT_SECONDS, verify=VERIFY_SSL)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('collection', []):
            uid = art.get('doi') or art.get('title')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            docs.append({'source_name':'medRxiv','external_id':uid,'title':art.get('title') or 'Unknown','doi':art.get('doi'),'pmid':None,'pmcid':None,'journal_or_site':'medRxiv','publication_date':art.get('date'),'source_url':'https://www.medrxiv.org','abstract_text':art.get('abstract')})
    return docs
