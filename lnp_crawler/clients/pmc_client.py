import time
import requests
from typing import Optional
from lnp_crawler.config import NCBI_API_KEY, NCBI_EMAIL, RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def fetch_fulltext_xml(pmcid: str) -> Optional[str]:
    params = {'db': 'pmc', 'id': pmcid.replace('PMC', ''), 'rettype': 'full', 'retmode': 'xml', 'email': NCBI_EMAIL, 'tool': 'butterfly_1.0'}
    if NCBI_API_KEY:
        params['api_key'] = NCBI_API_KEY
    try:
        r = requests.get(f'{BASE}/efetch.fcgi', params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        return r.text
    except Exception:
        return None
