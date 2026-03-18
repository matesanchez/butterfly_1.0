from rapidfuzz import fuzz
from typing import List, Dict


def is_duplicate_title(a: str, b: str, threshold: int = 75) -> bool:
    return fuzz.ratio((a or '').strip().lower(), (b or '').strip().lower()) >= threshold


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    deduped = []
    seen_dois = set()
    seen_titles = []
    for rec in records:
        doi = (rec.get('doi') or '').strip().lower()
        title = (rec.get('title') or '').strip()
        if doi and doi in seen_dois:
            continue
        if any(is_duplicate_title(title, prev) for prev in seen_titles):
            continue
        deduped.append(rec)
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.append(title)
    return deduped
