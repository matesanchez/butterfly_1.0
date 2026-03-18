from lnp_crawler.extraction_patterns import extract_all, extract_lipids, extract_payload, extract_route


def test_extract_core_fields():
    text = 'LNPs were formulated with ionizable lipid, cholesterol, DSPC, and PEG-lipid. The molar ratio was 50:38.5:10:1.5. mRNA was delivered intravenously in mice.'
    result = extract_all(text)
    assert result['lipid_mix_text']
    assert result['payload'] == 'mRNA'
    assert result['administration_route']
    assert result['extraction_confidence'] > 0


def test_extract_lipid_list():
    lipids = extract_lipids('Formulation contained DSPC, cholesterol, and PEG-lipid.')
    assert 'DSPC' in lipids
    assert any(x.lower().startswith('chol') for x in lipids)


def test_extract_payload_and_route():
    text = 'siRNA was administered intravenously.'
    assert extract_payload(text) == 'siRNA'
    assert extract_route(text)


def test_gold_set_extraction():
    import json
    from pathlib import Path
    gold_path = Path(__file__).parent / 'fixtures' / 'gold_set.json'
    data = json.loads(gold_path.read_text(encoding='utf-8'))
    for item in data:
        res = extract_all(item['text'])
        assert res['lipid_reagents_json'] or res.get('lipid_mix_text'), f"No lipids extracted for {item['title']}"
        expected = item.get('expected')
        if expected:
            for lipid in expected.get('lipid_reagents', []):
                assert any(lipid.lower() in s.lower() for s in (res.get('lipid_reagents_json') or [])) or (res.get('lipid_mix_text') and lipid.lower() in res.get('lipid_mix_text').lower())
            if expected.get('payload'):
                assert expected['payload'].lower() in (res.get('payload') or '').lower()
