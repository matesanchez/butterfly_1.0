from scripts import parse_documents


def test_parse_raw_html():
    payload = {'abstract': 'Abstract text', 'fulltext': '<html><body><h1>Methods</h1><p>DSPC and cholesterol.</p></body></html>'}
    parsed = parse_documents.parse_raw(payload)
    assert 'Abstract text' in parsed['abstract_or_body']
    assert 'DSPC' in parsed['abstract_or_body']
    assert parsed['sections']
