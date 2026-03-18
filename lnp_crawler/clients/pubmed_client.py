import time
import requests
from lnp_crawler.config import NCBI_API_KEY, NCBI_EMAIL, RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS
from lnp_crawler.query_builder import pubmed_queries
from urllib.parse import urljoin
import re

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def _params(extra: dict) -> dict:
    params = {'email': NCBI_EMAIL, 'tool': 'butterfly_1.0', 'retmode': 'json'}
    if NCBI_API_KEY:
        params['api_key'] = NCBI_API_KEY
    params.update(extra)
    return params

def search(query: str, max_results: int = 100) -> list[str]:
    r = requests.get(f'{BASE}/esearch.fcgi', params=_params({'db': 'pubmed', 'term': query, 'retmax': max_results}), timeout=REQUEST_TIMEOUT_SECONDS)
    r.raise_for_status()
    time.sleep(RATE_LIMIT_DELAY_SECONDS)
    return r.json().get('esearchresult', {}).get('idlist', [])

def fetch_summary(pmid: str) -> dict:
    r = requests.get(f'{BASE}/esummary.fcgi', params=_params({'db': 'pubmed', 'id': pmid}), timeout=REQUEST_TIMEOUT_SECONDS)
    r.raise_for_status()
    time.sleep(RATE_LIMIT_DELAY_SECONDS)
    return r.json().get('result', {}).get(pmid, {})

def fetch_abstract(pmid: str) -> str:
    r = requests.get(urljoin(BASE, 'efetch.fcgi'), params=_params({'db': 'pubmed', 'id': pmid, 'rettype': 'abstract', 'retmode': 'text'}), timeout=REQUEST_TIMEOUT_SECONDS)
    r.raise_for_status()
    time.sleep(RATE_LIMIT_DELAY_SECONDS)
    text = r.text.strip()
    if not text:
        return None
    # NCBI sometimes returns XML error envelopes with status 200
    if text.startswith('<') or 'ERROR' in text[:200].upper():
        return None
    return text

def discover(max_results: int = 100) -> list[dict]:
    docs, seen = [], set()
    for query in pubmed_queries():
        for pmid in search(query, max_results=max_results):
            if pmid in seen:
                continue
            seen.add(pmid)
            summary = fetch_summary(pmid)
            abstract = fetch_abstract(pmid)
            doi = summary.get('elocationid') or None
            def _clean_doi(raw: str | None) -> str | None:
                if not raw:
                    return None
                raw = raw.strip()
                raw = re.sub(r'^(https?://doi\.org/|doi:\s*)', '', raw, flags=re.IGNORECASE)
                return raw if raw.startswith('10.') else raw

            doi = _clean_doi(doi)
            docs.append({'source_name': 'PubMed', 'external_id': pmid, 'title': summary.get('title') or 'Unknown', 'doi': doi, 'pmid': pmid, 'pmcid': None, 'journal_or_site': summary.get('fulljournalname'), 'publication_date': summary.get('pubdate'), 'source_url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/', 'abstract_text': abstract})
    return docs
