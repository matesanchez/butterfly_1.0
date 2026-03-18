import time, requests
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS
from lnp_crawler.query_builder import generic_queries
BASE = "https://api.semanticscholar.org/graph/v1/paper/search"

def discover(max_results: int = 100) -> list[dict]:
    docs, seen = [], set()
    for query in generic_queries():
        r = requests.get(BASE, params={'query': query, 'limit': min(max_results,25), 'fields': 'title,abstract,year,venue,externalIds,url'}, timeout=REQUEST_TIMEOUT_SECONDS)
        if not r.ok:
            continue
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        for art in r.json().get('data', []):
            ext = art.get('externalIds') or {}
            uid = ext.get('DOI') or art.get('url') or art.get('title')
            if not uid or uid in seen:
                continue
            seen.add(uid)
            docs.append({'source_name':'Semantic Scholar','external_id':uid,'title':art.get('title') or 'Unknown','doi':ext.get('DOI'),'pmid':ext.get('PubMed'),'pmcid':ext.get('PubMedCentral'),'journal_or_site':art.get('venue'),'publication_date':art.get('year'),'source_url':art.get('url'),'abstract_text':art.get('abstract')})
    return docs
