import time, requests
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS
from lnp_crawler.query_builder import generic_queries
BASE = "https://api.biorxiv.org"

def discover(max_results: int = 100) -> list[dict]:
    docs, seen = [], set()
    for query in generic_queries():
        q = query.replace(' ', '%20')
        r = requests.get(f'{BASE}/details/biorxiv/{q}/0/{min(max_results,25)}', timeout=REQUEST_TIMEOUT_SECONDS)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('collection', []):
            uid = art.get('doi') or art.get('title')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            docs.append({'source_name':'bioRxiv','external_id':uid,'title':art.get('title') or 'Unknown','doi':art.get('doi'),'pmid':None,'pmcid':None,'journal_or_site':'bioRxiv','publication_date':art.get('date'),'source_url':'https://www.biorxiv.org','abstract_text':art.get('abstract')})
    return docs
