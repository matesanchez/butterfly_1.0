import time, requests
from typing import List, Dict
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import generic_queries
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        r = requests.get(f'{BASE}/search', params={'query': query, 'resultType': 'core', 'format': 'json', 'pageSize': min(max_results,25)}, timeout=REQUEST_TIMEOUT_SECONDS, verify=VERIFY_SSL)
        r.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('resultList', {}).get('result', []):
            uid = art.get('id') or art.get('pmid') or art.get('doi')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            src = art.get('source', 'MED')
            docs.append({'source_name':'Europe PMC','external_id':uid,'title':art.get('title') or 'Unknown','doi':art.get('doi'),'pmid':art.get('pmid'),'pmcid':art.get('pmcid'),'journal_or_site':art.get('journalTitle'),'publication_date':str(art.get('pubYear') or ''),'source_url':f'https://europepmc.org/article/{src}/{uid}','abstract_text':art.get('abstractText')})
    return docs
