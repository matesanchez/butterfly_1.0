import json
from lnp_crawler.config import EXTERNAL_REFS_PATH


def load_registry() -> list[dict]:
    with open(EXTERNAL_REFS_PATH, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_registry(registry: list[dict]) -> None:
    with open(EXTERNAL_REFS_PATH, 'w', encoding='utf-8') as fh:
        json.dump(registry, fh, indent=2)
