#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp_crawler.config import DATA_EXPORTS  # noqa: E402
from lnp_crawler.db import get_connection  # noqa: E402

def main() -> int:
    DATA_EXPORTS.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_EXPORTS / 'lnp_formulations.csv'
    json_path = DATA_EXPORTS / 'lnp_formulations.json'
    
    print("   Exporting results to CSV and JSON...", flush=True, end='\r')
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT d.id AS document_id, d.title, d.doi, d.pmid, d.pmcid, d.journal_or_site,
                   d.publication_date, d.source_url, r.lipid_mix_text, r.lipid_reagents_json,
                   r.lipid_ratios_text, r.cells_or_organisms, r.payload, r.administration_route,
                   r.other_relevant_info, r.evidence_span, r.extraction_confidence
            FROM lnp_records r JOIN documents d ON d.id = r.document_id ORDER BY d.id
        """).fetchall()
    records = [dict(row) for row in rows]
    json_path.write_text(json.dumps(records, indent=2), encoding='utf-8')
    if records:
        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
    else:
        csv_path.write_text('', encoding='utf-8')
    print(f"   ✓ Exported {len(records)} records to CSV and JSON" + " " * 30, flush=True)
    return len(records)

if __name__ == '__main__':
    main()
