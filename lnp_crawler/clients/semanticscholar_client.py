import logging
from typing import List, Dict
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import generic_queries
from lnp_crawler.http_utils import retry_request

BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
logger = logging.getLogger(__name__)

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in generic_queries():
        try:
            r = retry_request(BASE, {'query': query, 'limit': min(max_results, 25), 'fields': 'title,abstract,year,venue,externalIds,url'})
            if not r:
                logger.warning(f"Failed to search Semantic Scholar for '{query}'")
                continue
            
            for art in r.json().get('data', []):
                ext = art.get('externalIds') or {}
                uid = ext.get('DOI') or art.get('url') or art.get('title')
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                docs.append({'source_name': 'Semantic Scholar', 'external_id': uid, 'title': art.get('title') or 'Unknown', 'doi': ext.get('DOI'), 'pmid': ext.get('PubMed'), 'pmcid': ext.get('PubMedCentral'), 'journal_or_site': art.get('venue'), 'publication_date': art.get('year'), 'source_url': art.get('url'), 'abstract_text': art.get('abstract')})
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar for '{query}': {e}")
            continue
    return docs
