import logging
from typing import List, Dict
from lnp_crawler.query_builder import generic_queries
from lnp_crawler.http_utils import retry_request

BASE = "https://api.crossref.org/works"
logger = logging.getLogger(__name__)

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        try:
            r = retry_request(BASE, {'query': query, 'rows': min(max_results, 25)})
            if not r:
                logger.warning(f"Failed to search Crossref for '{query}'")
                continue
            
            for art in r.json().get('message', {}).get('items', []):
                uid = art.get('DOI') or str(art.get('title', ['']))
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                date_parts = ((art.get('published-print') or art.get('published-online') or {}).get('date-parts') or [['']])[0]
                docs.append({'source_name': 'Crossref', 'external_id': uid, 'title': (art.get('title') or ['Unknown'])[0], 'doi': art.get('DOI'), 'pmid': None, 'pmcid': None, 'journal_or_site': ((art.get('container-title') or ['']) or [''])[0], 'publication_date': str(date_parts[0]), 'source_url': art.get('URL'), 'abstract_text': art.get('abstract')})
        except Exception as e:
            logger.error(f"Error searching Crossref for '{query}': {e}")
            continue
    return docs
