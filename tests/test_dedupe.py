from lnp_crawler.dedupe import deduplicate_records, is_duplicate_title


def test_exact_doi_dedupe():
    records = [
        {'doi': '10.1234/test', 'title': 'Paper A'},
        {'doi': '10.1234/test', 'title': 'Paper A duplicate'},
    ]
    assert len(deduplicate_records(records)) == 1


def test_title_similarity():
    assert is_duplicate_title('Lipid nanoparticle mRNA delivery', 'Lipid nanoparticle mRNA delivery')


def test_title_similarity_fuzzy():
    assert is_duplicate_title(
        'Lipid nanoparticles for mRNA delivery',
        'Lipid nanoparticle mRNA delivery system',
    )


def test_different_papers_kept():
    records = [
        {'doi': '10.1/a', 'title': 'LNP Paper A'},
        {'doi': '10.1/b', 'title': 'siRNA Delivery Paper B'},
    ]
    assert len(deduplicate_records(records)) == 2
