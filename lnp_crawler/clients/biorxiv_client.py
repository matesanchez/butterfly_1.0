import logging
from typing import List, Dict
from lnp_crawler.query_builder import generic_queries
from lnp_crawler.http_utils import retry_request

BASE = "https://api.biorxiv.org"
logger = logging.getLogger(__name__)

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        try:
            q = query.replace(' ', '%20')
            r = retry_request(f'{BASE}/details/biorxiv/{q}/0/{min(max_results, 25)}')
            if not r:
                logger.warning(f"Failed to search bioRxiv for '{query}'")
                continue
            
            for art in r.json().get('collection', []):
                uid = art.get('doi') or art.get('title')
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                docs.append({'source_name': 'bioRxiv', 'external_id': uid, 'title': art.get('title') or 'Unknown', 'doi': art.get('doi'), 'pmid': None, 'pmcid': None, 'journal_or_site': 'bioRxiv', 'publication_date': art.get('date'), 'source_url': 'https://www.biorxiv.org', 'abstract_text': art.get('abstract')})
        except Exception as e:
            logger.error(f"Error searching bioRxiv for '{query}': {e}")
            continue
    return docs
