import json
from pathlib import Path
from unittest.mock import patch

from scripts import discover_documents
from lnp_crawler.config import DATA_STAGING


def test_discovery_writes_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(discover_documents, 'DATA_STAGING', tmp_path)
    monkeypatch.setattr(discover_documents, 'load_registry', lambda: [{'source': 'PubMed', 'homepage': 'x', 'api_url': 'y'}])
    monkeypatch.setattr(discover_documents, 'upsert_source', lambda *args, **kwargs: 1)
    monkeypatch.setattr(discover_documents, 'upsert_document', lambda doc: 99)

    class FakeClient:
        @staticmethod
        def discover(max_results=100):
            return [{'external_id': 'abc', 'title': 'Test title', 'doi': '10.1/x', 'pmid': '123', 'pmcid': None, 'journal_or_site': 'J', 'publication_date': '2024', 'source_url': 'http://x', 'abstract_text': 'text'}]

    monkeypatch.setattr('lnp_crawler.clients.pubmed_client.discover', FakeClient.discover)
    count = discover_documents.main(limit=1, source_filter='PubMed')
    assert count == 1
    out = tmp_path / 'discovered_documents.jsonl'
    lines = out.read_text(encoding='utf-8').splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row['document_id'] == 99
