import json

from lnp_crawler.normalization import canonicalize, normalize_lipid_list, normalize_record


def test_synonym_mapping():
    assert canonicalize('cationic lipid') == 'ionizable lipid'
    assert canonicalize('peg lipid') == 'PEG-lipid'
    assert canonicalize('chol') == 'cholesterol'
    assert canonicalize('IV.') == 'intravenous'


def test_list_normalization():
    result = normalize_lipid_list(['DSPC', 'chol', 'peg lipid', 'PEG-lipid'])
    assert 'cholesterol' in result
    assert 'PEG-lipid' in result
    assert result.count('PEG-lipid') == 1


def test_normalize_record_preserves_invalid_lipid_json():
    record = {'lipid_reagents_json': '{bad json', 'administration_route': 'SC.'}

    result = normalize_record(record)

    assert result['lipid_reagents_json'] == '{bad json'
    assert result['administration_route'] == 'subcutaneous'


def test_normalize_record_normalizes_lipid_json():
    record = {'lipid_reagents_json': json.dumps(['chol', 'peg lipid'])}

    result = normalize_record(record)

    assert json.loads(result['lipid_reagents_json']) == ['cholesterol', 'PEG-lipid']
