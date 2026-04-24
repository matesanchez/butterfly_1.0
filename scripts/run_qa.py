#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp_crawler.config import DATA_EXPORTS, DATA_NORMALIZED  # noqa: E402
from lnp_crawler.qa import write_qa_report  # noqa: E402

def main() -> dict:
    DATA_EXPORTS.mkdir(parents=True, exist_ok=True)
    in_path = DATA_NORMALIZED / 'deduped_records.jsonl'
    print("   Loading records for QA analysis...", flush=True, end='\r')
    records = [json.loads(line) for line in in_path.read_text(encoding='utf-8').splitlines() if line.strip()] if in_path.exists() else []
    print(f"   Analyzing: {len(records)} records" + " " * 40, flush=True)
    result = write_qa_report(DATA_EXPORTS / 'qa_report.json', records)
    print("   ✓ QA analysis complete" + " " * 40, flush=True)
    return result

if __name__ == '__main__':
    main()
