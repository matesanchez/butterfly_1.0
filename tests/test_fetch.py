import json
from unittest.mock import Mock

from scripts import fetch_documents


class FakeDoc(dict):
    def __getattr__(self, item):
        return self[item]


def test_fetch_writes_raw_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_documents, 'DATA_RAW', tmp_path)
    monkeypatch.setattr(fetch_documents, 'get_documents_by_status', lambda status: [
        {'id': 1, 'doi': '10.1/x', 'pmcid': None, 'abstract_text': 'abstract', 'title': 'T'}
    ])
    monkeypatch.setattr(fetch_documents, 'get_oa_url', lambda doi: 'http://example.test/paper')

    class Resp:
        text = 'full text here'
        def raise_for_status(self):
            return None

    mock_requests = Mock()
    mock_resp = Resp()
    mock_requests.get = Mock(return_value=mock_resp)
    monkeypatch.setattr(fetch_documents, 'requests', mock_requests)
    monkeypatch.setattr(fetch_documents, 'fetch_fulltext_xml', lambda pmcid: None)
    monkeypatch.setattr(fetch_documents, 'update_document_status', lambda *args, **kwargs: None)

    class DummyConn:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, *args, **kwargs): return None
    monkeypatch.setattr(fetch_documents, 'get_connection', lambda: DummyConn())

    count = fetch_documents.main(limit=1)
    assert count == 1
    payload = json.loads((tmp_path / '1.json').read_text(encoding='utf-8'))
    assert payload['document_id'] == 1
    assert payload['fulltext'] == 'full text here'
