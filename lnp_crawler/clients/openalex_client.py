import logging
from typing import List, Dict
from lnp_crawler.query_builder import generic_queries
from lnp_crawler.http_utils import retry_request

BASE = "https://api.openalex.org/works"
logger = logging.getLogger(__name__)

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        try:
            r = retry_request(BASE, {'search': query, 'per-page': min(max_results, 25)})
            if not r:
                logger.warning(f"Failed to search OpenAlex for '{query}'")
                continue
            
            for art in r.json().get('results', []):
                uid = art.get('id') or art.get('doi')
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                source = ((art.get('primary_location') or {}).get('source') or {})
                docs.append({'source_name': 'OpenAlex', 'external_id': uid, 'title': art.get('display_name') or 'Unknown', 'doi': (art.get('doi') or '').replace('https://doi.org/', '') or None, 'pmid': None, 'pmcid': None, 'journal_or_site': source.get('display_name'), 'publication_date': art.get('publication_year'), 'source_url': art.get('id'), 'abstract_text': None})
        except Exception as e:
            logger.error(f"Error searching OpenAlex for '{query}': {e}")
            continue
    return docs
