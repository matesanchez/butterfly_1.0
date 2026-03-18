import json
from pathlib import Path
from lnp_crawler.config import MAX_MISSING_LIPID_FIELDS_PCT


def build_qa_report(records: list[dict]) -> dict:
    total = len(records)
    missing = sum(1 for rec in records if not rec.get('lipid_reagents_json'))
    pct = round((missing / total) * 100, 2) if total else 0.0
    return {
        'total_records': total,
        'missing_lipid_fields': missing,
        'missing_lipid_fields_pct': pct,
        'threshold_pct': MAX_MISSING_LIPID_FIELDS_PCT,
        'passed': pct <= MAX_MISSING_LIPID_FIELDS_PCT,
    }


def write_qa_report(path: Path, records: list[dict]) -> dict:
    report = build_qa_report(records)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
