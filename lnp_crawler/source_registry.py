import json
from typing import List, Dict
from lnp_crawler.config import EXTERNAL_REFS_PATH


def load_registry() -> List[Dict]:
    with open(EXTERNAL_REFS_PATH, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_registry(registry: List[Dict]) -> None:
    with open(EXTERNAL_REFS_PATH, 'w', encoding='utf-8') as fh:
        json.dump(registry, fh, indent=2)
