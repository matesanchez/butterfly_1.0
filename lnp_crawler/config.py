import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Suppress urllib3 InsecureRequestWarning for corporate proxy environments
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(os.environ.get("BUTTERFLY_ROOT", Path(__file__).resolve().parent.parent))
load_dotenv(ROOT / '.env')


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


CONFIG: dict = load_yaml(ROOT / "config.yaml")

CRAWL = CONFIG.get('crawl', {})
EXTRACTION = CONFIG.get('extraction', {})
QA = CONFIG.get('qa', {})
SEARCH_TERMS = CONFIG.get('search_terms', {})

NCBI_API_KEY = os.getenv('NCBI_API_KEY', '')
NCBI_EMAIL = os.getenv('NCBI_EMAIL') or 'butterfly@example.com'
SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
UNPAYWALL_EMAIL = os.getenv('UNPAYWALL_EMAIL') or 'butterfly@example.com'

REQUEST_TIMEOUT_SECONDS = int(CRAWL.get('request_timeout_seconds', 30))
RATE_LIMIT_DELAY_SECONDS = float(CRAWL.get('rate_limit_delay_seconds', 1.0))
# Default to False for corporate proxy environments; set VERIFY_SSL=true for production
VERIFY_SSL = os.getenv('VERIFY_SSL', 'false').lower() in ('true', '1', 'yes')
RETRY_ATTEMPTS = int(CRAWL.get('retry_attempts', 3))
MAX_RESULTS_PER_SOURCE = int(CRAWL.get('max_results_per_source', 100))
CONFIDENCE_THRESHOLD = float(EXTRACTION.get('confidence_threshold', 0.4))
MAX_MISSING_LIPID_FIELDS_PCT = float(QA.get('max_missing_lipid_fields_pct', 20))

# NCBI allows 10 requests/second with API key, 3 without
# 0.1s delay = 10 req/s, 0.33s delay ~= 3 req/s
NCBI_RATE_LIMIT_DELAY_SECONDS = 0.1 if NCBI_API_KEY else RATE_LIMIT_DELAY_SECONDS

DB_PATH = ROOT / 'db' / 'lnp_literature.sqlite'
EXTERNAL_REFS_PATH = ROOT / 'external_references.json'
DATA_RAW = ROOT / 'data' / 'raw'
DATA_STAGING = ROOT / 'data' / 'staging'
DATA_NORMALIZED = ROOT / 'data' / 'normalized'
DATA_FAILED = ROOT / 'data' / 'failed'
DATA_EXPORTS = ROOT / 'data' / 'exports'
LOGS_DIR = ROOT / 'logs'

# Warn if placeholder contact emails are used
_PLACEHOLDER_EMAIL = 'butterfly@example.com'
if NCBI_EMAIL == _PLACEHOLDER_EMAIL or UNPAYWALL_EMAIL == _PLACEHOLDER_EMAIL:
    import warnings
    warnings.warn(
        "NCBI_EMAIL or UNPAYWALL_EMAIL is using a placeholder. Set real values in .env to comply with API terms of service.",
        stacklevel=1,
    )
