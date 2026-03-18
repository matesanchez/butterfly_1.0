import time
import requests
from typing import Optional
from lnp_crawler.config import RATE_LIMIT_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS, UNPAYWALL_EMAIL
BASE = "https://api.unpaywall.org/v2"

def get_oa_url(doi: str) -> Optional[str]:
    try:
        r = requests.get(f'{BASE}/{doi}', params={'email': UNPAYWALL_EMAIL}, timeout=REQUEST_TIMEOUT_SECONDS)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY_SECONDS)
        best = r.json().get('best_oa_location')
        return (best or {}).get('url_for_pdf') or (best or {}).get('url')
    except Exception:
        return None
