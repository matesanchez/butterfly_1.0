from lnp_crawler.config import SEARCH_TERMS, CRAWL
from urllib.parse import quote_plus
from typing import List

PRIMARY_TERMS = SEARCH_TERMS.get('primary', ['lipid nanoparticle', 'LNP', 'ionizable lipid'])
SECONDARY_TERMS = SEARCH_TERMS.get('secondary', ['mRNA delivery', 'siRNA LNP', 'PEG-lipid'])

_MAX_SECONDARY = int(CRAWL.get('max_secondary_terms', 2))
_MAX_QUERIES = int(CRAWL.get('max_queries_per_source', 5))


def pubmed_queries() -> List[str]:
    queries = [
        f"{p}[TitleAbstract] AND {s}[TitleAbstract]"
        for p in PRIMARY_TERMS
        for s in SECONDARY_TERMS[:_MAX_SECONDARY]
    ]
    return queries[:_MAX_QUERIES]


def generic_queries() -> List[str]:
    return [
        f"{quote_plus(p)} {quote_plus(s)}"
        for p in PRIMARY_TERMS
        for s in SECONDARY_TERMS
    ][:_MAX_QUERIES]
