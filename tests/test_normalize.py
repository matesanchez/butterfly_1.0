from lnp_crawler.normalization import canonicalize, normalize_lipid_list


def test_synonym_mapping():
    assert canonicalize('cationic lipid') == 'ionizable lipid'
    assert canonicalize('peg lipid') == 'PEG-lipid'
    assert canonicalize('chol') == 'cholesterol'


def test_list_normalization():
    result = normalize_lipid_list(['DSPC', 'chol', 'peg lipid'])
    assert 'cholesterol' in result
    assert 'PEG-lipid' in result
