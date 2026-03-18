import time, requests
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS
from lnp_crawler.query_builder import generic_queries
BASE = "https://api.openalex.org/works"

def discover(max_results: int = 100) -> list[dict]:
    docs, seen = [], set()
    for query in generic_queries():
        r = requests.get(BASE, params={'search': query, 'per-page': min(max_results,25)}, timeout=REQUEST_TIMEOUT_SECONDS)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('results', []):
            uid = art.get('id') or art.get('doi')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            source = ((art.get('primary_location') or {}).get('source') or {})
            docs.append({'source_name':'OpenAlex','external_id':uid,'title':art.get('display_name') or 'Unknown','doi':(art.get('doi') or '').replace('https://doi.org/','') or None,'pmid':None,'pmcid':None,'journal_or_site':source.get('display_name'),'publication_date':art.get('publication_year'),'source_url':art.get('id'),'abstract_text':None})
    return docs
