#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lnp_crawler.config import DATA_EXPORTS, DATA_NORMALIZED
from lnp_crawler.qa import write_qa_report

def main() -> dict:
    DATA_EXPORTS.mkdir(parents=True, exist_ok=True)
    in_path = DATA_NORMALIZED / 'deduped_records.jsonl'
    records = [json.loads(line) for line in in_path.read_text(encoding='utf-8').splitlines() if line.strip()] if in_path.exists() else []
    return write_qa_report(DATA_EXPORTS / 'qa_report.json', records)

if __name__ == '__main__':
    main()
