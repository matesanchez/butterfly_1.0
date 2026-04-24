import json
import re
from typing import List, Optional

LIPID_NAMES = [
    r'DLin-MC3-DMA', r'MC3', r'ALC-0315', r'SM-102', r'lipid\s*H', r'ionizable\s+lipid',
    r'cationic\s+lipid', r'DSPC', r'DOPE', r'DOPC', r'DPPC', r'cholesterol', r'Chol',
    r'PEG-lipid', r'PEGylated\s+lipid', r'DMG-PEG', r'ALC-0159', r'C12-200', r'DLinDMA',
    r'DOTAP', r'DOTMA'
]
LIPID_PATTERN = re.compile('|'.join(LIPID_NAMES), re.IGNORECASE)
RATIO_PATTERN = re.compile(r'(?:molar ratio|mol/mol|wt/wt|weight ratio)[^\n\.;:]{0,120}', re.IGNORECASE)
PAYLOAD_PATTERN = re.compile(r'(mRNA|siRNA|saRNA|plasmid DNA|pDNA|CRISPR|sgRNA|RNP|antisense|miRNA|ASO)', re.IGNORECASE)
ROUTE_PATTERN = re.compile(r'(intravenous(?:ly)?|IV|intraperitoneal(?:ly)?|IP|intramuscular(?:ly)?|IM|subcutaneous(?:ly)?|SC|intranasal(?:ly)?|IN|intratracheal(?:ly)?|IT|oral(?:ly)?|topical(?:ly)?|intratumoral(?:ly)?)', re.IGNORECASE)
CELL_PATTERN = re.compile(r'(HeLa|HEK293|HepG2|A549|Jurkat|PBMC|dendritic cell|hepatocyte|macrophage|T cell|B cell|mouse|mice|rat|rabbit|NHP|non-human primate|human|in vivo|in vitro)', re.IGNORECASE)


def _unique(values):
    seen = []
    seen_lower = set()
    for value in values:
        cleaned = value.strip()
        lowered = cleaned.lower()
        if cleaned and lowered not in seen_lower:
            seen.append(cleaned)
            seen_lower.add(lowered)
    return seen


def extract_lipids(text: str) -> List[str]:
    return _unique([m.group(0) for m in LIPID_PATTERN.finditer(text or '')])


def extract_ratios(text: str) -> Optional[str]:
    m = RATIO_PATTERN.search(text or '')
    return m.group(0).strip() if m else None


def extract_payload(text: str) -> Optional[str]:
    m = PAYLOAD_PATTERN.search(text or '')
    return m.group(1).strip() if m else None


def extract_route(text: str) -> Optional[str]:
    m = ROUTE_PATTERN.search(text or '')
    return m.group(1).strip() if m else None


def extract_cells(text: str) -> Optional[str]:
    hits = _unique([m.group(1) for m in CELL_PATTERN.finditer(text or '')])
    return ', '.join(hits) if hits else None


def score_confidence(lipids, payload, cells, route, ratios) -> float:
    score = 0.0
    if lipids:
        score += 0.4
    if payload:
        score += 0.2
    if cells:
        score += 0.15
    if route:
        score += 0.15
    if ratios:
        score += 0.1
    return round(min(score, 1.0), 2)


def extract_all(text: str) -> dict:
    lipids = extract_lipids(text)
    ratios = extract_ratios(text)
    payload = extract_payload(text)
    route = extract_route(text)
    cells = extract_cells(text)
    return {
        'lipid_mix_text': ', '.join(lipids) if lipids else None,
        'lipid_reagents_json': json.dumps(lipids) if lipids else None,
        'lipid_ratios_text': ratios,
        'lipid_ratios_json': None,
        'cells_or_organisms': cells,
        'payload': payload,
        'administration_route': route,
        'other_relevant_info': None,
        'evidence_span': (text or '')[:500] if text else None,
        'extraction_confidence': score_confidence(lipids, payload, cells, route, ratios),
    }
