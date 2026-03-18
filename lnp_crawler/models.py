"""Dataclasses for pipeline records."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class DiscoveredDocument:
    source_name: str
    external_id: str
    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    journal_or_site: Optional[str] = None
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    abstract_text: Optional[str] = None

@dataclass
class ParsedDocument:
    source_name: str
    external_id: str
    title: str
    abstract_or_body: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    journal_or_site: Optional[str] = None
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    full_text_path: Optional[str] = None
    raw_hash: Optional[str] = None

@dataclass
class LNPRecord:
    document_id: int
    lipid_mix_text: Optional[str] = None
    lipid_reagents_json: Optional[str] = None
    lipid_ratios_text: Optional[str] = None
    lipid_ratios_json: Optional[str] = None
    cells_or_organisms: Optional[str] = None
    payload: Optional[str] = None
    administration_route: Optional[str] = None
    other_relevant_info: Optional[str] = None
    evidence_span: Optional[str] = None
    extraction_confidence: float = 0.0
