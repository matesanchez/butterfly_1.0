"""HTTP retry utilities for API calls with exponential backoff."""
import time
import requests
import logging
from typing import Optional
from lnp_crawler.config import RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, VERIFY_SSL, RATE_LIMIT_DELAY_SECONDS

logger = logging.getLogger(__name__)


def retry_request(url: str, params: dict = None, retries: int = RETRY_ATTEMPTS, 
                  timeout: int = REQUEST_TIMEOUT_SECONDS, verify_ssl: bool = VERIFY_SSL,
                  rate_limit_delay: float = RATE_LIMIT_DELAY_SECONDS) -> Optional[requests.Response]:
    """
    Retry HTTP GET requests with exponential backoff for transient failures.
    
    Args:
        url: Request URL
        params: Query parameters
        retries: Number of retry attempts
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        rate_limit_delay: Delay after successful request (in seconds)
    
    Returns:
        requests.Response object or None if all retries fail
    """
    if params is None:
        params = {}
    
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, verify=verify_ssl)
            
            # Retry on server errors (5xx)
            if r.status_code >= 500:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"HTTP {r.status_code} error, retrying in {wait_time}s... (attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP {r.status_code} error after {retries} attempts")
                    return None
            
            # For other errors, return None on client errors (4xx)
            if r.status_code >= 400:
                if r.status_code == 404:
                    logger.debug(f"HTTP 404: Resource not found at {url}")
                else:
                    logger.warning(f"HTTP {r.status_code} error: {r.text[:200]}")
                return None
            
            # Success: apply rate limiting delay
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)
            
            return r
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Connection failed after {retries} attempts: {e}")
                return None
    
    return None
