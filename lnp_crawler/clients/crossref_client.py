import time, requests
from typing import List, Dict
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import generic_queries
BASE = "https://api.crossref.org/works"

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        r = requests.get(BASE, params={'query': query, 'rows': min(max_results,25)}, timeout=REQUEST_TIMEOUT_SECONDS, verify=VERIFY_SSL)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('message', {}).get('items', []):
            uid = art.get('DOI') or str(art.get('title', ['']))
            if not uid or uid in seen:
                continue
            seen.add(uid)
            date_parts = ((art.get('published-print') or art.get('published-online') or {}).get('date-parts') or [['']])[0]
            docs.append({'source_name':'Crossref','external_id':uid,'title':(art.get('title') or ['Unknown'])[0],'doi':art.get('DOI'),'pmid':None,'pmcid':None,'journal_or_site':((art.get('container-title') or ['']) or [''])[0],'publication_date':str(date_parts[0]),'source_url':art.get('URL'),'abstract_text':art.get('abstract')})
    return docs
