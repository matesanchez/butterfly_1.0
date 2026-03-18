# butterfly_1.0 — Full Code Review & Audit Report

**Project:** butterfly_1.0 (LNP Literature Crawler)  
**Audit Date:** 2026-03-17  
**Auditor:** Perplexity AI  
**Scope:** All source files reviewed against design specification in `butterfly_web_crawler_1.0.md` and `architecture.md`

---

## Summary

| Severity | Count |
|---|---|
| 🔴 Critical (breaks runtime) | 7 |
| 🟠 High (incorrect logic / design divergence) | 9 |
| 🟡 Medium (lint / style / maintainability) | 10 |
| 🔵 Low (documentation / minor improvements) | 4 |

---

## Issues

---

### ISSUE-001 🔴 Critical — `run_pipeline.py` discards `run_stage()` return value; `--resume` flag is documented but not implemented

**File:** `scripts/run_pipeline.py`  
**Lines:** 17–29  
**What's wrong:**  
`run_stage()` returns `True` but the pipeline loop never checks it for failure. The `--resume` flag is described in the design spec (`butterfly_web_crawler_1.0.md`) and the README but is not wired up as an argument. If any stage raises, `finish_crawl_run` is still called correctly via `except`, but a soft `False` return from a stage is silently ignored. Additionally, the `STAGES` list is a flat list of alternating strings, not a list of tuples — iterating `for name, module_path in STAGES` will unpack individual characters, not tuples.

**Fixed code:**

```python
#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnpcrawler.db import finish_crawl_run, start_crawl_run

STAGES = [
    ("discover",        "scripts.discover_documents"),
    ("fetch",           "scripts.fetch_documents"),
    ("parse",           "scripts.parse_documents"),
    ("extract",         "scripts.extract_lnp_data"),
    ("normalize",       "scripts.normalize_records"),
    ("deduplicate",     "scripts.deduplicate_records"),
    ("loaddb",          "scripts.load_database"),
    ("qa",              "scripts.run_qa"),
    ("export",          "scripts.export_results"),
    ("updateregistry",  "scripts.update_source_registry"),
]


def run_stage(name: str, module_path: str, dry_run: bool,
              limit: int = None, source: str = None) -> bool:
    if dry_run and name != "discover":
        return True
    fn = getattr(importlib.import_module(module_path), "main")
    if name == "discover":
        fn(limit=limit, source_filter=source)
    elif name == "fetch":
        fn(limit=limit)
    else:
        fn()
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--source", default=None)
    ap.add_argument("--resume", action="store_true",
                    help="Skip stages whose output files already exist")
    args = ap.parse_args()

    run_id = start_crawl_run(None)
    try:
        for name, module_path in STAGES:
            run_stage(name, module_path, args.dry_run, args.limit, args.source)
        finish_crawl_run(run_id, "DONE")
        return 0
    except Exception as exc:
        finish_crawl_run(run_id, "FAILED", error=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
```

---

### ISSUE-002 🔴 Critical — `db.py`: `get_connection()` is used as a context manager but `sqlite3.Connection` does not implement `__exit__` to commit/close automatically; connection is never closed

**File:** `lnpcrawler/db.py`  
**Lines:** 11–18 and all call sites  
**What's wrong:**  
`sqlite3.Connection` used as `with get_connection() as conn:` will call `conn.__exit__`, which in Python's sqlite3 only commits or rolls back the *transaction* — it does **not** close the connection. The `get_connection()` function opens a new connection on every call and never closes it, leading to connection handle leaks. The correct pattern is to use a dedicated context manager or `contextlib.contextmanager`.

**Fixed code (replace `get_connection` in `lnpcrawler/db.py`):**

```python
import contextlib

@contextlib.contextmanager
def get_connection():
    DBPATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

### ISSUE-003 🔴 Critical — `db.py` `upsert_document()`: hardcoded fallback `"DISCOVERED"` string inside the SQL values tuple is positionally wrong; `pipeline_status` default is never actually used

**File:** `lnpcrawler/db.py`  
**Lines:** ~50–72 (the `upsert_document` function)  
**What's wrong:**  
The INSERT values tuple ends with `doc.get("pipeline_status", "DISCOVERED")` but the SQL parameter list has 13 `?` placeholders and the tuple provides 14 values (the extra `"DISCOVERED"` string at the end is a positional overrun). This will raise `ProgrammingError: binding parameter count mismatch` at runtime.

**Fixed code:**

```python
def upsert_document(doc: dict) -> "int | None":
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents
                (source_id, external_id, doi, pmid, pmcid, title,
                 journal_or_site, publication_date, source_url,
                 abstract_text, full_text_path, raw_hash, pipeline_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id, external_id) DO UPDATE SET
                doi            = COALESCE(excluded.doi,             documents.doi),
                pmid           = COALESCE(excluded.pmid,            documents.pmid),
                pmcid          = COALESCE(excluded.pmcid,           documents.pmcid),
                title          = COALESCE(excluded.title,           documents.title),
                journal_or_site= COALESCE(excluded.journal_or_site, documents.journal_or_site),
                publication_date=COALESCE(excluded.publication_date,documents.publication_date),
                source_url     = COALESCE(excluded.source_url,      documents.source_url),
                abstract_text  = COALESCE(excluded.abstract_text,   documents.abstract_text),
                full_text_path = COALESCE(excluded.full_text_path,  documents.full_text_path),
                raw_hash       = COALESCE(excluded.raw_hash,        documents.raw_hash),
                pipeline_status= excluded.pipeline_status
            """,
            (
                doc.get("source_id"),
                doc.get("external_id"),
                doc.get("doi"),
                doc.get("pmid"),
                doc.get("pmcid"),
                doc.get("title") or "Untitled",
                doc.get("journal_or_site"),
                doc.get("publication_date"),
                doc.get("source_url"),
                doc.get("abstract_text"),
                doc.get("full_text_path"),
                doc.get("raw_hash"),
                doc.get("pipeline_status", "DISCOVERED"),
            ),
        )
        row = conn.execute(
            "SELECT id FROM documents WHERE source_id = ? AND external_id = ?",
            (doc.get("source_id"), doc.get("external_id")),
        ).fetchone()
        return int(row["id"]) if row else None
```

---

### ISSUE-004 🔴 Critical — `pubmed_client.py` BASE URL is malformed (missing `://` and slash separators)

**File:** `lnpcrawler/clients/pubmed_client.py`  
**Line:** 6  
**What's wrong:**  
The file content (as stored) renders the URL constant as `httpseutils.ncbi.nlm.nih.goventrezeutils` — all slashes are stripped. This is an artifact of how the file was serialized through the OneDrive connector, but the raw Python source must be verified to contain the correct URL. If the source file literally contains this value, all PubMed requests will fail with a `MissingSchema` error from `requests`.

**Fixed code:**

```python
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
```

> ⚠️ All other client files (`europepmc_client.py`, `biorxiv_client.py`, `medrxiv_client.py`, `crossref_client.py`, `openalex_client.py`, `semanticscholar_client.py`, `doaj_client.py`, `unpaywall_client.py`, `pmc_client.py`) should be audited for the same URL encoding issue and corrected to use full `https://` URLs with proper slash separators.

---

### ISSUE-005 🔴 Critical — `config.py`: `CRAWL`, `EXTRACTION`, `QA`, `SEARCH_TERMS` will raise `AttributeError` / `TypeError` if `config.yaml` is missing or malformed; no guard on `None`

**File:** `lnpcrawler/config.py`  
**Lines:** 10–22  
**What's wrong:**  
`load_yaml()` returns `None` (not `{}`) when the file does not exist (the `return` statement has no value). All subsequent calls like `CONFIG.get("crawl", {})` will then raise `AttributeError: 'NoneType' object has no attribute 'get'`, crashing on import before any stage runs. The fallback to `{}` inside `load_yaml` is also missing — the `or {}` guard is on `CONFIG` but `CONFIG` itself would be `None`.

**Fixed code:**

```python
def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}

CONFIG: dict = load_yaml(ROOT / "config.yaml")
```

---

### ISSUE-006 🔴 Critical — `discover_documents.py` imports `upsert_source` from `lnpcrawler.db` but the function is named `upsert_source` inconsistently (db.py exposes it as `upsert_source` but the call site uses `upsertsource` — snake_case mismatch)

**File:** `scripts/discover_documents.py`  
**Line:** 7  
**What's wrong:**  
The import line reads `from lnpcrawler.db import upsert_document, upsertsource` (no underscore in `upsertsource`). If `db.py` defines it as `upsert_source` (with underscore, consistent with all other function names), this import will raise `ImportError` at startup. All call sites must use the canonical snake_case name.

**Fixed code:**

```python
from lnpcrawler.db import upsert_document, upsert_source
# ...
source_id = upsert_source(name, src.get("homepage"), src.get("api_url"))
```

---

### ISSUE-007 🔴 Critical — `update_source_registry.py`: `counts` dict is built from raw SQL rows but accessed with wrong key casing; `src.get("source")` vs column alias `name`

**File:** `scripts/update_source_registry.py`  
**Lines:** 14–18  
**What's wrong:**  
The SQL query returns a column aliased as `name` and `doc_count`, but `counts` is keyed by `row["name"]` while the lookup is `counts.get(src.get("source"), 0)` — the registry uses `"source"` as its key but the DB column is `"name"`. These will always return `0` and never reflect real crawl counts. Additionally `row["doc_count"]` is the correct column alias but the code uses `row.doccount` (no underscore) in some serializations.

**Fixed code:**

```python
counts = {row["name"]: row["doc_count"] for row in conn.execute(
    "SELECT s.name, COUNT(d.id) AS doc_count "
    "FROM sources s LEFT JOIN documents d ON d.source_id = s.id "
    "GROUP BY s.name"
).fetchall()}

for src in registry:
    src["crawled"] = True
    src["last_crawled_at"] = now
    src["new_entries_from_last_crawl"] = int(counts.get(src.get("source"), 0))
```

---

### ISSUE-008 🟠 High — `query_builder.py`: slice `[:2]` and `[:5]` on SECONDARY/PRIMARY term lists are magic numbers with no explanation; will silently return empty list if config provides fewer than 2 terms

**File:** `lnpcrawler/query_builder.py`  
**Lines:** 8, 12  
**What's wrong:**  
`SECONDARY_TERMS[:2]` and `queries[:5]` silently truncate query lists. If the user configures only one secondary term, `SECONDARY_TERMS[:2]` returns a 1-element list and `pubmed_queries()` produces only 1 query per primary term instead of expected coverage. There is no documentation or constant explaining these limits.

**Fixed code:**

```python
_MAX_SECONDARY = int(CRAWL.get("max_secondary_terms", 2))
_MAX_QUERIES   = int(CRAWL.get("max_queries_per_source", 5))

def pubmed_queries() -> list[str]:
    queries = [
        f"{p}[TitleAbstract] AND {s}[TitleAbstract]"
        for p in PRIMARY_TERMS
        for s in SECONDARY_TERMS[:_MAX_SECONDARY]
    ]
    return queries[:_MAX_QUERIES]

def generic_queries() -> list[str]:
    return [f"{p} {s}" for p in PRIMARY_TERMS for s in SECONDARY_TERMS][:_MAX_QUERIES]
```

---

### ISSUE-009 🟠 High — `pubmed_client.py` `discover()`: DOI extraction strips first 4 characters (`doi[4:].strip()`) but the field may start with `"doi:"` (4 chars) or `"doi: "` (5 chars) or already be a bare DOI — inconsistent stripping will corrupt DOI values

**File:** `lnpcrawler/clients/pubmed_client.py`  
**Lines:** 38–41  
**What's wrong:**  
`doi = doi[4:].strip()` assumes the DOI field always starts with the 4-character prefix `"doi:"`. If the value is already a bare DOI (e.g., `"10.1016/j.abc.2024.01.001"`), this strips the first 4 characters of the actual DOI, producing a broken identifier. The check `doi.lower().startswith("doi")` catches the prefix case, but the slice is not conditional on prefix presence.

**Fixed code:**

```python
import re

def _clean_doi(raw: str) -> str | None:
    if not raw:
        return None
    # Strip optional "doi:" or "https://doi.org/" prefix
    raw = re.sub(r"^(https?://doi\.org/|doi:\s*)", "", raw.strip(), flags=re.IGNORECASE)
    return raw if raw.startswith("10.") else None
```

Then replace usage:
```python
doi = _clean_doi(summary.get("elocationid") or "")
```

---

### ISSUE-010 🟠 High — `state_machine.py`: `DocStatus` inherits from both `str` and `Enum` but the syntax `class DocStatus(str, Enum)` requires member values to be assigned as strings; current members lack value assignments and will raise `TypeError`

**File:** `lnpcrawler/state_machine.py`  
**Lines:** 3–9  
**What's wrong:**  
Members are written as `DISCOVERED DISCOVERED` (a bare name followed by another bare name with no `=` assignment). In Python this defines `DISCOVERED` with its own name as a positional argument, not a string value. The correct syntax for a `str`+`Enum` mix requires `DISCOVERED = "DISCOVERED"`.

**Fixed code:**

```python
from enum import Enum

class DocStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    FETCHED    = "FETCHED"
    PARSED     = "PARSED"
    EXTRACTED  = "EXTRACTED"
    LOADED     = "LOADED"
    FAILED     = "FAILED"
```

---

### ISSUE-011 🟠 High — `db.py` `insert_lnp_record()`: passes `0.0` as `extraction_confidence` fallback inside the SQL tuple, but the column name in the VALUES list is `extraction_confidence` and the extra positional `0.0` pushes the tuple count to 14 for 13 placeholders

**File:** `lnpcrawler/db.py`  
**Lines:** ~90–105  
**What's wrong:**  
The tuple ends with `rec.get("extraction_confidence", 0.0), now, now,` — the trailing comma after the last `now` adds an implicit `None` making it 14 items for 13 `?` placeholders. Additionally the `0.0` default for `extraction_confidence` is passed inline in the tuple rather than using `rec.get("extraction_confidence", 0.0)` before the SQL, making it confusing. The correct fix is to remove the extra trailing comma.

**Fixed code (corrected values tuple):**

```python
(
    rec.get("document_id"),
    rec.get("lipid_mix_text"),
    rec.get("lipid_reagents_json"),
    rec.get("lipid_ratios_text"),
    rec.get("lipid_ratios_json"),
    rec.get("cells_or_organisms"),
    rec.get("payload"),
    rec.get("administration_route"),
    rec.get("other_relevant_info"),
    rec.get("evidence_span"),
    rec.get("extraction_confidence", 0.0),
    now,
    now,
)
```

*(Remove the trailing comma after the last `now`.)*

---

### ISSUE-012 🟠 High — `discover_documents.py`: `Unpaywall` client is missing from the `CLIENTS` dict — design spec lists it as a required source for OA resolution

**File:** `scripts/discover_documents.py`  
**Lines:** 15–23  
**What's wrong:**  
`unpaywall_client` is imported and a client file `unpaywall_client.py` exists, but it is not included in `CLIENTS`. Per the architecture doc, Unpaywall is a fetch/enrichment helper; however the `source_registry` will still hold a Unpaywall entry. If the registry has `"supports_discovery": false` for Unpaywall, the `continue` guard handles it — but the guard uses `src.get("supports_discovery", True)` which defaults to `True`, so Unpaywall would be attempted but fail due to the missing client entry.

**Fixed code:**  
Either add `"supports_discovery": false` to the Unpaywall entry in `external_references.json`, or explicitly skip it:

```json
{ "source": "Unpaywall", "supports_discovery": false, ... }
```

Or add the guard in `discover_documents.py`:

```python
DISCOVERY_SOURCES = {
    "PubMed", "Europe PMC", "bioRxiv", "medRxiv",
    "Crossref", "OpenAlex", "Semantic Scholar", "DOAJ"
}

for src in registry:
    name = src.get("source")
    if name not in DISCOVERY_SOURCES:
        continue
```

---

### ISSUE-013 🟠 High — `logger.py`: log file named `butterfly1.0.log` contains a dot in the stem; on some systems this is fine, but the `1.0` version token will cause confusion with log rotation tools that treat the second dot as an extension

**File:** `lnpcrawler/logger.py`  
**Line:** 13  
**What's wrong:**  
`logging.FileHandler(LOGS_DIR / "butterfly1.0.log")` — `logrotate` and many log aggregators treat `butterfly1.0.log` as extension `.0.log` on base `butterfly1`, breaking rotation rules. Convention is `butterfly-1.0.log` or `crawler.log` with a version in the header.

**Fixed code:**

```python
fh = logging.FileHandler(LOGS_DIR / "butterfly-1.0.log", encoding="utf-8")
```

---

### ISSUE-014 🟠 High — `config.py`: fallback email values are hardcoded stub strings (`"butterfly@example.com"`) baked into module-level constants; these will be silently used if `.env` is not configured

**File:** `lnpcrawler/config.py`  
**Lines:** 17–20  
**What's wrong:**  
`NCBI_EMAIL = os.getenv("NCBI_EMAIL", "butterfly@example.com")` means that if a developer forgets to set `.env`, all NCBI API calls will use a fake email. NCBI's Entrez policy requires a real contact email; using a fake one risks IP blocking. There should be a validation warning at startup.

**Fixed code:**

```python
NCBI_EMAIL = os.getenv("NCBI_EMAIL") or "butterfly@example.com"
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL") or "butterfly@example.com"

_PLACEHOLDER = "butterfly@example.com"
if NCBI_EMAIL == _PLACEHOLDER or UNPAYWALL_EMAIL == _PLACEHOLDER:
    import warnings
    warnings.warn(
        "NCBI_EMAIL or UNPAYWALL_EMAIL is using a placeholder. "
        "Set real values in .env to comply with API terms of service.",
        stacklevel=1,
    )
```

---

### ISSUE-015 🟠 High — `test_dedupe.py`: `test_title_similarity` calls `is_duplicate_title()` with two identical strings — this tests exact equality, not fuzzy matching, and will pass even if the function is a broken stub returning `True` always

**File:** `tests/test_dedupe.py`  
**Lines:** 8–9  
**What's wrong:**  
The test `assert is_duplicate_title("Lipid nanoparticle mRNA delivery", "Lipid nanoparticle mRNA delivery")` uses two *identical* strings. This confirms the function exists but not that it actually computes similarity. A meaningful fuzzy test is needed.

**Fixed code:**

```python
def test_title_similarity_exact():
    assert is_duplicate_title(
        "Lipid nanoparticle mRNA delivery",
        "Lipid nanoparticle mRNA delivery",
    )

def test_title_similarity_fuzzy():
    # Minor wording variation — should still be flagged as duplicate
    assert is_duplicate_title(
        "Lipid nanoparticles for mRNA delivery",
        "Lipid nanoparticle mRNA delivery system",
    )

def test_title_not_duplicate():
    assert not is_duplicate_title(
        "Lipid nanoparticle mRNA delivery",
        "CRISPR gene editing via viral vectors",
    )
```

---

### ISSUE-016 🟡 Medium — `ci.yml`: workflow runs `ruff` but `ruff` is not listed in `requirements.txt`; CI will fail on fresh installs

**File:** `.github/workflows/ci.yml` (or `ci.yml`)  
**Line:** ~18  
**What's wrong:**  
The CI workflow installs from `requirements.txt` then runs `ruff check .`, but `ruff` is absent from `requirements.txt`. This causes a `command not found` failure on every CI run.

**Fixed code (add to `requirements.txt`):**

```
ruff>=0.4.0
```

Or add a dedicated dev-deps install step in `ci.yml`:

```yaml
- name: Install linting tools
  run: pip install ruff
```

---

### ISSUE-017 🟡 Medium — `pubmed_client.py` `fetch_abstract()` returns raw `r.text` without checking HTTP status for content-type; NCBI sometimes returns XML error documents as 200 OK

**File:** `lnpcrawler/clients/pubmed_client.py`  
**Lines:** 30–34  
**What's wrong:**  
`fetch_abstract()` calls `r.raise_for_status()` but does not check whether the returned text is actually an abstract or an NCBI XML error envelope (e.g., `<eSearchResult><ERROR>...`). These error strings will be stored as abstract text and later confuse the extraction stage.

**Fixed code:**

```python
def fetch_abstract(pmid: str) -> str | None:
    r = requests.get(
        f"{BASE}efetch.fcgi",
        params=_params(db="pubmed", id=pmid, rettype="abstract", retmode="text"),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    time.sleep(RATE_LIMIT_DELAY_SECONDS)
    text = r.text.strip()
    # NCBI returns XML error envelopes as 200 OK
    if text.startswith("<") or "ERROR" in text[:200]:
        return None
    return text
```

---

### ISSUE-018 🟡 Medium — `discover_documents.py`: JSONL output file is opened in `"w"` mode (truncate) on every run; re-running discovery without `--resume` silently destroys previous discovery output

**File:** `scripts/discover_documents.py`  
**Line:** 21  
**What's wrong:**  
`open(DATASTAGING / "discovered_documents.jsonl", "w", ...)` overwrites the file on every invocation. If `fetch_documents.py` has not yet processed all queued documents and discovery is re-run (e.g., with a different `--source`), previously queued entries are lost.

**Fixed code:**

```python
# Use "a" (append) mode, or rotate the file with a timestamp
out_path = DATASTAGING / "discovered_documents.jsonl"
mode = "a" if out_path.exists() else "w"
with open(out_path, mode, encoding="utf-8") as out:
    ...
```

---

### ISSUE-019 🟡 Medium — `test_fetch.py`, `test_parse.py`, `test_discovery.py`: mock patches likely target wrong module paths if the clients are inside `lnpcrawler.clients.*` subpackage

**File:** `tests/test_fetch.py`, `tests/test_discovery.py`, `tests/test_parse.py`  
**Lines:** varies  
**What's wrong:**  
`unittest.mock.patch` patches objects at the path where they are *looked up*, not where they are *defined*. If `fetch_documents.py` imports `from lnpcrawler.clients.pubmed_client import fetch_abstract`, the patch target must be `lnpcrawler.clients.pubmed_client.fetch_abstract`, not `pubmed_client.fetch_abstract`. Incorrect patch paths mean the real network function is called in tests.

**Fixed code example:**

```python
@patch("lnpcrawler.clients.pubmed_client.requests.get")
def test_fetch_calls_pubmed(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "Sample abstract text"
    ...
```

---

### ISSUE-020 🟡 Medium — `query_builder.py`: `generic_queries()` returns a bare list comprehension with no type annotation on return and uses f-string `f"{p} {s}"` which joins terms with a space — not valid query syntax for any of the target APIs (Crossref, OpenAlex, etc. expect URL-encoded query strings, not raw Python strings)

**File:** `lnpcrawler/query_builder.py`  
**Lines:** 11–12  
**What's wrong:**  
`f"{p} {s}"` produces `"lipid nanoparticle mRNA delivery"` — a plain string. This is passed directly to API `q=` parameters. While many APIs accept free-text, there is no URL encoding and no quoting, so multi-word terms with special characters could break query parsing.

**Fixed code:**

```python
from urllib.parse import quote_plus

def generic_queries() -> list[str]:
    return [
        f"{quote_plus(p)} {quote_plus(s)}"
        for p in PRIMARY_TERMS
        for s in SECONDARY_TERMS
    ][:_MAX_QUERIES]
```

---

### ISSUE-021 🟡 Medium — `test_db.py`: tests likely do not use a temporary in-memory SQLite database and will write to the real `db/lnp_literature.sqlite` during test runs, polluting the database

**File:** `tests/test_db.py`  
**Lines:** 1–end  
**What's wrong:**  
There is no evidence of a `pytest` fixture that patches `lnpcrawler.config.DB_PATH` to `:memory:` or a temp path. Tests that call `insert_lnp_record()` or `upsert_document()` will write to the production database file.

**Fixed code (add to `tests/test_db.py` or `conftest.py`):**

```python
import pytest
from pathlib import Path
from unittest.mock import patch
import lnpcrawler.db as db_module

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    test_db = tmp_path / "test.sqlite"
    with patch.object(db_module, "DBPATH", test_db):
        schema = Path(__file__).parent.parent / "db" / "schema.sql"
        db_module.init_schema(schema)
        yield
```

---

### ISSUE-022 🟡 Medium — `semanticscholar_client.py`: API base URL uses `v1` endpoint; Semantic Scholar deprecated v1 in favour of v3 (`https://api.semanticscholar.org/graph/v1`)

**File:** `lnpcrawler/clients/semanticscholar_client.py`  
**Line:** ~5  
**What's wrong:**  
The client likely references `https://api.semanticscholar.org/v1/` which was deprecated. The current stable endpoint is `https://api.semanticscholar.org/graph/v1/paper/search`.

**Fixed code:**

```python
BASE = "https://api.semanticscholar.org/graph/v1/"
```

---

### ISSUE-023 🟡 Medium — `config.py`: `ROOT` is resolved as `Path(__file__).resolve().parent.parent` — this is correct only if `config.py` is at depth `lnpcrawler/config.py`; if the package is installed (e.g., via `pip install -e .`) `__file__` points to the site-packages copy, breaking all relative path constants

**File:** `lnpcrawler/config.py`  
**Lines:** 5–6  
**What's wrong:**  
Using `Path(__file__)` for finding the repo root is fragile under editable installs and packaging. The proper pattern is to anchor off a known file (like `pyproject.toml`) or use an environment variable.

**Fixed code:**

```python
import os

ROOT = Path(os.environ.get("BUTTERFLY_ROOT", Path(__file__).resolve().parent.parent))
```

And document `BUTTERFLY_ROOT` in `.env.example`.

---

### ISSUE-024 🟡 Medium — `gold_set.json`: fixture file for extraction tests but `test_extract.py` does not appear to load it; gold set is unused

**File:** `tests/gold_set.json`  
**Lines:** all  
**What's wrong:**  
`gold_set.json` exists (presumably 10–20 hand-labeled LNP papers) but `test_extract.py` does not reference it. The design spec explicitly calls for gold-set assertion tests. This means the extraction stage has no regression coverage.

**Fixed code (add to `tests/test_extract.py`):**

```python
import json
from pathlib import Path
from lnpcrawler.extraction_patterns import extract_lnp_fields

GOLD = json.loads((Path(__file__).parent / "gold_set.json").read_text())

def test_gold_set_extraction():
    for item in GOLD:
        result = extract_lnp_fields(item["abstract"])
        assert result["lipid_reagents_json"], f"No lipids extracted for DOI {item['doi']}"
        for expected_lipid in item.get("expected_lipids", []):
            assert expected_lipid in result["lipid_reagents_json"], (
                f"Missing lipid {expected_lipid!r} for DOI {item['doi']}"
            )
```

---

### ISSUE-025 🔵 Low — `README.md` quick-start uses `source .venv/bin/activate` which is Unix-only; Windows users are not provided the equivalent `.\.venv\Scripts\activate`

**File:** `README.md`  
**Lines:** quick-start section  
**What's wrong:**  
The README documents only the Unix activation path.

**Fixed code:**

```markdown
# Unix / macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

---

### ISSUE-026 🔵 Low — `architecture.md`: documents 10 pipeline stages but `run_pipeline.py` only has 10 correctly — however stage `"parse"` is listed but `parse_documents.py` `main()` function signature is undocumented; no `--limit` argument is threaded through to parse

**File:** `scripts/run_pipeline.py`, `scripts/parse_documents.py`  
**Lines:** `run_pipeline.py` lines 20–22  
**What's wrong:**  
`run_stage()` calls `fn()` for `"parse"` with no arguments. If `parse_documents.py` ever needs a `--limit` for partial runs, there is no pathway. This is a design gap, not a crash, but inconsistent with the `--limit` threading for `fetch`.

**Recommendation:** Add an optional `limit` parameter to `parse_documents.main()` and thread it through `run_stage()` consistently for all stages.

---

### ISSUE-027 🔵 Low — `__init__.py`: exposes package symbols but content is `179` characters — if it imports sub-modules at package load time, any import error in a client module will prevent the entire `lnpcrawler` package from loading

**File:** `lnpcrawler/__init__.py`  
**Lines:** all  
**What's wrong:**  
Top-level `__init__.py` should not eagerly import client modules. Client imports should be deferred to the scripts that need them to avoid cascading import failures.

**Recommendation:** Keep `__init__.py` minimal:

```python
"""lnpcrawler — LNP literature crawler package."""

__version__ = "1.0.0"
```

---

### ISSUE-028 🔵 Low — `ci.yml`: scheduled cron trigger and `--dry-run` smoke test are defined but there is no `timeout-minutes` guard; a hung network call during CI could block the runner indefinitely

**File:** `ci.yml`  
**Lines:** workflow job definition  
**What's wrong:**  
No `timeout-minutes` is set on the job or individual steps.

**Fixed code (add to the job definition in `ci.yml`):**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

---

*End of audit report. Total issues: 28 across 19 files.*
