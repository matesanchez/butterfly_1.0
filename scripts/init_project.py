#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_EXPORTS, DATA_FAILED, DATA_NORMALIZED, DATA_RAW, DATA_STAGING, DB_PATH, EXTERNAL_REFS_PATH, LOGS_DIR
from lnp_crawler.db import init_schema

def main() -> None:
    for directory in [DATA_RAW, DATA_STAGING, DATA_NORMALIZED, DATA_FAILED, DATA_EXPORTS, LOGS_DIR, DB_PATH.parent]:
        directory.mkdir(parents=True, exist_ok=True)
    if not EXTERNAL_REFS_PATH.exists():
        raise FileNotFoundError(f'Missing registry file: {EXTERNAL_REFS_PATH}')
    init_schema(ROOT / 'db' / 'schema.sql')

if __name__ == '__main__':
    main()
