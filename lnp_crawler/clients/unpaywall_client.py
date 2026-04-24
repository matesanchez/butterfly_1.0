import logging
from typing import Optional
from lnp_crawler.config import UNPAYWALL_EMAIL
from lnp_crawler.http_utils import retry_request

BASE = "https://api.unpaywall.org/v2"
logger = logging.getLogger(__name__)

def get_oa_url(doi: str) -> Optional[str]:
    try:
        r = retry_request(f'{BASE}/{doi}', {'email': UNPAYWALL_EMAIL})
        if not r:
            return None
        best = r.json().get('best_oa_location')
        return (best or {}).get('url_for_pdf') or (best or {}).get('url')
    except Exception as e:
        logger.warning(f"Error fetching OA URL for DOI {doi}: {e}")
        return None
