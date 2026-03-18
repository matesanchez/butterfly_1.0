import time
import requests
from typing import List, Dict, Optional
from lnp_crawler.config import NCBI_API_KEY, NCBI_EMAIL, NCBI_RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL
from lnp_crawler.query_builder import pubmed_queries
from lnp_crawler.http_utils import retry_request
from urllib.parse import urljoin
import re
import logging

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
logger = logging.getLogger(__name__)

def _params(extra: dict) -> dict:
    params = {'email': NCBI_EMAIL, 'tool': 'butterfly_1.0', 'retmode': 'json'}
    if NCBI_API_KEY:
        params['api_key'] = NCBI_API_KEY
    params.update(extra)
    return params

def search(query: str, max_results: int = 100) -> List[str]:
    r = retry_request(f'{BASE}esearch.fcgi', _params({'db': 'pubmed', 'term': query, 'retmax': max_results}), rate_limit_delay=NCBI_RATE_LIMIT_DELAY_SECONDS)
    if not r:
        return []
    return r.json().get('esearchresult', {}).get('idlist', [])

def fetch_summary(pmid: str) -> dict:
    r = retry_request(f'{BASE}esummary.fcgi', _params({'db': 'pubmed', 'id': pmid}), rate_limit_delay=NCBI_RATE_LIMIT_DELAY_SECONDS)
    if not r:
        return {}
    return r.json().get('result', {}).get(pmid, {})

def fetch_abstract(pmid: str) -> Optional[str]:
    r = retry_request(urljoin(BASE, 'efetch.fcgi'), _params({'db': 'pubmed', 'id': pmid, 'rettype': 'abstract', 'retmode': 'text'}), rate_limit_delay=NCBI_RATE_LIMIT_DELAY_SECONDS)
    if not r:
        return None
    text = r.text.strip()
    if not text:
        return None
    # NCBI sometimes returns XML error envelopes with status 200
    if text.startswith('<') or 'ERROR' in text[:200].upper():
        return None
    return text

def discover(max_results: int = 100) -> List[Dict]:
    docs, seen = [], set()
    for query in pubmed_queries():
        try:
            pmids = search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Error searching PubMed for '{query}': {e}")
            continue
        
        for pmid in pmids:
            if pmid in seen:
                continue
            seen.add(pmid)
            try:
                summary = fetch_summary(pmid)
                if not summary:
                    logger.debug(f"No summary for PMID {pmid}, skipping")
                    continue
                abstract = fetch_abstract(pmid)
                doi = summary.get('elocationid') or None
                def _clean_doi(raw: Optional[str]) -> Optional[str]:
                    if not raw:
                        return None
                    raw = raw.strip()
                    raw = re.sub(r'^(https?://doi\.org/|doi:\s*)', '', raw, flags=re.IGNORECASE)
                    return raw if raw.startswith('10.') else raw

                doi = _clean_doi(doi)
                docs.append({'source_name': 'PubMed', 'external_id': pmid, 'title': summary.get('title') or 'Unknown', 'doi': doi, 'pmid': pmid, 'pmcid': None, 'journal_or_site': summary.get('fulljournalname'), 'publication_date': summary.get('pubdate'), 'source_url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/', 'abstract_text': abstract})
            except Exception as e:
                logger.error(f"Error processing PMID {pmid}: {e}")
                continue
    return docs
