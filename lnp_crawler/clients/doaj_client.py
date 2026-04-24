import logging
from typing import List, Dict
from lnp_crawler.query_builder import generic_queries
from lnp_crawler.http_utils import retry_request

BASE = "https://doaj.org/api/search/articles"
logger = logging.getLogger(__name__)

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        try:
            r = retry_request(f'{BASE}/{query}', {'pageSize': min(max_results, 25)})
            if not r:
                logger.warning(f"Failed to search DOAJ for '{query}'")
                continue
            
            for art in r.json().get('results', []):
                bib = art.get('bibjson') or {}
                doi = next((i.get('id') for i in bib.get('identifier', []) if i.get('type') == 'doi'), None)
                uid = doi or bib.get('title')
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                link = bib.get('link', [{}])
                docs.append({'source_name': 'DOAJ', 'external_id': uid, 'title': bib.get('title') or 'Unknown', 'doi': doi, 'pmid': None, 'pmcid': None, 'journal_or_site': (bib.get('journal') or {}).get('title'), 'publication_date': bib.get('year'), 'source_url': link[0].get('url') if link else None, 'abstract_text': bib.get('abstract')})
        except Exception as e:
            logger.error(f"Error searching DOAJ for '{query}': {e}")
            continue
    return docs
