import json
from json import JSONDecodeError

ALIASES = {
    'cationic lipid': 'ionizable lipid',
    'peg lipid': 'PEG-lipid',
    'pegylated lipid': 'PEG-lipid',
    'chol': 'cholesterol',
    'iv': 'intravenous',
    'im': 'intramuscular',
    'sc': 'subcutaneous',
}


def canonicalize(value: str) -> str:
    cleaned = (value or '').strip()
    alias_key = cleaned.lower().strip(" .")
    return ALIASES.get(alias_key, cleaned)


def normalize_lipid_list(items):
    normalized = []
    seen = set()
    for item in items:
        c = canonicalize(item)
        if c and c.lower() not in seen:
            normalized.append(c)
            seen.add(c.lower())
    return normalized


def normalize_record(rec: dict) -> dict:
    out = dict(rec)
    raw = rec.get('lipid_reagents_json')
    if raw:
        try:
            lipids = json.loads(raw)
            out['lipid_reagents_json'] = json.dumps(normalize_lipid_list(lipids))
        except (JSONDecodeError, TypeError):
            pass
    route = rec.get('administration_route')
    if route:
        out['administration_route'] = canonicalize(route)
    return out
