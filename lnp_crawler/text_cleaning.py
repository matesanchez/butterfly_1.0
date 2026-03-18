import re


def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text or '')


def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip())


def clean(text: str) -> str:
    return normalize_whitespace(strip_html(text))


def extract_sections(text: str) -> dict[str, str]:
    pattern = re.compile(r'(abstract|introduction|methods?|materials and methods|results|discussion|conclusion)', re.IGNORECASE)
    parts = pattern.split(text or '')
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        key = parts[i].strip().lower().replace(' ', '_')
        sections[key] = parts[i + 1].strip()
    if not sections:
        sections['body'] = clean(text or '')
    return sections
