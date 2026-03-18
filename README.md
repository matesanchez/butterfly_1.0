# butterfly_1.0 — LNP Literature Crawler
Vibecoded by Mateo Sanchez
03/16/2026

**butterfly_1.0** is a comprehensive, API-first literature crawler designed to discover, fetch, parse, and extract structured lipid nanoparticle (LNP) formulation data from scientific publications across multiple public databases.

## Overview

Lipid nanoparticles (LNPs) are critical delivery vehicles for mRNA, siRNA, and other therapeutic payloads. Understanding LNP formulation compositions, administration routes, and delivery outcomes across the scientific literature is essential for drug development and research.

butterfly_1.0 automates this process by:
- **Discovering** relevant papers across 8 major scientific databases (PubMed, Europe PMC, bioRxiv, medRxiv, Crossref, OpenAlex, Semantic Scholar, DOAJ)
- **Fetching** full-text articles and abstracts from publicly available sources (PMC, Unpaywall)
- **Parsing** documents into clean, structured sections
- **Extracting** LNP-specific data: lipid composition, molar ratios, payload type, administration route, and formulation details
- **Normalizing** and **deduplicating** records using fuzzy matching
- **Loading** results into a SQLite database for downstream analysis
- **Quality assurance** to ensure extraction confidence meets thresholds

## Pipeline Architecture

The crawler operates as a 10-stage pipeline:

1. **Discover** — Search multiple sources using configurable primary/secondary search term combinations
2. **Fetch** — Download full-text and abstract content for discovered documents
3. **Parse** — Clean and segment text using heuristic section extraction
4. **Extract** — Identify LNP components, lipid reagents, ratios, and administration details
5. **Normalize** — Standardize lipid names and formulation descriptions
6. **Deduplicate** — Remove duplicate records using title fuzzy matching and DOI comparison
7. **Load DB** — Insert cleaned records into the document and LNP record tables
8. **QA** — Validate extraction quality against confidence thresholds
9. **Export** — Generate final CSV/JSON exports for downstream use
10. **Update Registry** — Update source crawl metadata with document counts

Each stage is idempotent and can be resumed independently using the `--resume` flag.

## Setup

### Requirements
- Python 3.7+
- SQLite 3.24+ (for UPSERT support)
- pip or conda

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd butterfly_1.0
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   ```
   
   **Unix/macOS:**
   ```bash
   source .venv/bin/activate
   ```
   
   **Windows (PowerShell):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   **Windows (cmd.exe):**
   ```cmd
   .venv\Scripts\activate.bat
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add:
   - `NCBI_EMAIL` — Your email (required for NCBI Entrez API; they block invalid emails)
   - `NCBI_API_KEY` — Optional; speeds up NCBI requests
   - `SEMANTIC_SCHOLAR_API_KEY` — Optional
   - `UNPAYWALL_EMAIL` — Your email (required for Unpaywall OA lookup)
   - `BUTTERFLY_ROOT` — Leave blank to use default; set if you move the project

5. **Initialize the database:**
   ```bash
   python scripts/init_project.py
   ```
   
   This creates `db/lnp_literature.sqlite` with the required schema.

6. **Verify installation:**
   ```bash
   pytest tests/ -v
   ```

## Running the Crawler

### Quick Dry Run (No API Calls)
```bash
python scripts/run_pipeline.py --dry-run --limit 5
```
This exercises the pipeline framework without making any external API requests; useful for verifying your setup works correctly without network dependencies.

### Full Crawl (All Stages)
```bash
python scripts/run_pipeline.py
```
Runs all 10 pipeline stages in sequence with real-time progress tracking. On first run, this may take several hours depending on:
- Number of sources and search term combinations
- Rate limiting (1 second default between requests per source)
- Network latency and API availability

**Output:** Shows stage progress, elapsed time per stage, and ETA for completion:
```
======================================================================
BUTTERFLY 1.0 PIPELINE START - 2026-03-17 20:29:01
======================================================================

[1/10] Running: DISCOVER...
   ... (API calls and data discovery) ...
✓ DISCOVER completed in 5.2m
   ETA: 42.5m remaining (finish ~21:17:30)

[2/10] Running: FETCH...
   ... (fetching documents) ...
✓ FETCH completed in 8.1m
   ETA: 38.2m remaining (finish ~21:25:15)
   
... (remaining stages)

✓ PIPELINE COMPLETE - Total time: 47.3m
======================================================================
```

### Running Individual Stages

You can invoke individual stages by importing and calling their `main()` function:

```bash
# Discover documents only
python -c "from scripts.discover_documents import main; main(limit=100, source_filter='PubMed')"

# Fetch with a limit (useful for testing)
python -c "from scripts.fetch_documents import main; main(limit=10)"

# Parse documents
python -c "from scripts.parse_documents import main; main(limit=50)"

# Extract LNP data
python -c "from scripts.extract_lnp_data import main; main()"
```

### Command-Line Options

**`run_pipeline.py` accepts:**
- `--dry-run` — Skip all API calls and test the pipeline framework
- `--limit N` — Limit discovery to N results per source (default: no limit; use with `--source` for testing)
- `--source NAME` — Run discovery for a single source only (e.g., `PubMed`, `Europe PMC`)
- `--resume` — Skip stages that already have completed work; allows resuming interrupted runs

**Progress Tracking:**
- Real-time output shows which stage is running (e.g., `[3/10] Running: EXTRACT...`)
- Per-stage elapsed time displayed (e.g., `✓ EXTRACT completed in 12.5m`)
- Running ETA shows estimated time remaining and finish time (e.g., `ETA: 35.2m remaining (finish ~21:15:30)`)
- Total pipeline completion time shown at the end

**Example:**
```bash
# Discover from PubMed only, limit to 50 results, then proceed through pipeline
python scripts/run_pipeline.py --source PubMed --limit 50

# Resume after an interruption, skipping sources with no work
python scripts/run_pipeline.py --resume
```

## Configuration

Edit `config.yaml` to customize:

```yaml
crawl:
  request_timeout_seconds: 30
  rate_limit_delay_seconds: 1.0
  retry_attempts: 3
  max_results_per_source: 100
  max_secondary_terms: 2        # Secondary search terms per primary term
  max_queries_per_source: 5     # Max queries to run per source

extraction:
  confidence_threshold: 0.4     # Minimum score to include LNP record

qa:
  max_missing_lipid_fields_pct: 20  # % of missing fields allowed to pass QA

search_terms:
  primary:
    - lipid nanoparticle
    - LNP
    - ionizable lipid
  secondary:
    - mRNA delivery
    - siRNA LNP
    - PEG-lipid
```

## Output

### Database Schema
Results are stored in `db/lnp_literature.sqlite`:

**documents table:**
- `id`, `source_id`, `external_id`, `doi`, `pmid`, `pmcid`
- `title`, `journal_or_site`, `publication_date`
- `source_url`, `abstract_text`, `full_text_path`, `raw_hash`
- `pipeline_status` (DISCOVERED → FETCHED → PARSED → EXTRACTED → LOADED)

**lnp_records table:**
- `document_id`, `lipid_mix_text`, `lipid_reagents_json`
- `lipid_ratios_text`, `lipid_ratios_json`
- `cells_or_organisms`, `payload` (mRNA, siRNA, etc.)
- `administration_route`, `evidence_span`
- `extraction_confidence`, `created_at`, `updated_at`

### Data Exports
The pipeline generates JSONL and CSV exports in `data/exports/`:
- `lnp_records.jsonl` — Structured LNP extraction results
- `documents.csv` — Crawled document metadata
- `sources_summary.json` — Per-source crawl statistics

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=lnp_crawler --cov=scripts -v
```

Tests use an in-memory SQLite database (configured via `tests/conftest.py`) and do not modify the production database.

## Troubleshooting

### SSL Certificate verification (already disabled for corporate)
**Good news:** SSL verification is **disabled by default** for corporate proxy compatibility.

If you want to enable verification for security:
```bash
# Windows PowerShell
$env:VERIFY_SSL = 'true'
python scripts/run_pipeline.py

# Windows cmd
set VERIFY_SSL=true
python scripts/run_pipeline.py

# Unix/macOS
export VERIFY_SSL=true
python scripts/run_pipeline.py
```

**If you still get SSL errors in corporate environments:**
- Option 1: Keep `VERIFY_SSL=false` (default, development-friendly)
- Option 2: Contact IT to get the corporate root certificate and install it in Python's certificate store

### NCBI API timeouts or blocking
- Ensure `NCBI_EMAIL` is set to a valid email in `.env`
- Use `NCBI_API_KEY` to increase rate limits (register at https://www.ncbi.nlm.nih.gov/account/)
- Increase `request_timeout_seconds` in `config.yaml` if networks are slow

### Missing abstracts or full text
- Some journals require authentication for full-text access
- Open Access (OA) resolution via Unpaywall is attempted but coverage is ~25% of all papers
- Check `documents.abstract_text` and set `pipeline_status` to FAILED if content is unavailable

### Database is locked
- Ensure only one instance of `run_pipeline.py` is running
- SQLite uses WAL mode; `.sqlite-wal` and `.sqlite-shm` files are temporary and can be safely deleted

### Extraction confidence too low
- Lower `confidence_threshold` in `config.yaml` if extracting novel lipid compositions
- Review gold-set test in `tests/test_extract.py` to improve extraction patterns

## Project Structure

```
butterfly_1.0/
├── lnp_crawler/              # Core package
│   ├── clients/              # API clients (PubMed, bioRxiv, etc.)
│   ├── config.py             # Configuration and environment
│   ├── db.py                 # SQLite connection and queries
│   ├── dedupe.py             # Deduplication logic
│   ├── extraction_patterns.py # LNP extraction rules
│   ├── logger.py             # Logging configuration
│   ├── normalization.py      # Text normalization
│   ├── query_builder.py      # Search query construction
│   └── state_machine.py      # Document pipeline status
├── scripts/                  # Entrypoints for each pipeline stage
│   ├── run_pipeline.py       # Main orchestrator
│   ├── discover_documents.py # Stage 1
│   ├── fetch_documents.py    # Stage 2
│   └── ... (7 more stages)
├── db/
│   └── schema.sql            # SQLite database schema
├── data/
│   ├── raw/                  # Downloaded full-text files (JSON)
│   ├── staging/              # Intermediate JSONL files
│   ├── normalized/           # Normalized records
│   ├── failed/               # Documents that failed extraction
│   └── exports/              # Final CSV/JSON exports
├── tests/
│   ├── conftest.py           # Pytest fixtures (temp DB)
│   ├── test_db.py
│   ├── test_extract.py
│   └── ... (more tests)
├── config.yaml               # Tunable pipeline parameters
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Development

**Code quality:**
```bash
ruff check .          # Linting
pytest tests/ -q      # Tests
```

**Contributing:**
- Ensure all tests pass: `pytest tests/ -v`
- Follow PEP 8 style (checked by ruff)
- Add tests for new extraction patterns or client integrations
- Update documentation if adding pipeline stages

## License

[Add license information here]

## Support & Questions

For issues, open a GitHub issue with:
- Python version and OS
- Relevant log output (`logs/butterfly-1.0.log`)
- Steps to reproduce
- Expected vs. actual behavior
