# 🦋 Butterfly Web Crawler 1.0 — LNP Literature Crawler

An automated, API-first pipeline to discover, fetch, parse, and extract structured LNP (Lipid Nanoparticle) formulation data from 10 scientific literature sources.

## Quick Start

```bash
# 1. Clone and set up virtual environment
git clone https://github.com/yourorg/lnp-literature-crawler
cd lnp-literature-crawler
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env: add NCBI_API_KEY, NCBI_EMAIL, UNPAYWALL_EMAIL

# 3. Bootstrap the project
python scripts/init_project.py

# 4. Run the full pipeline
python scripts/run_pipeline.py --limit 100

# 5. Dry run (no network calls)
python scripts/run_pipeline.py --dry-run --limit 5

# 6. Single source
python scripts/run_pipeline.py --source PubMed --limit 50
```

## Sources
PubMed · PubMed Central · Europe PMC · bioRxiv · medRxiv · Crossref · OpenAlex · Semantic Scholar · DOAJ · Unpaywall

## Output
- `db/lnp_literature.sqlite` — structured relational database
- `data/exports/lnp_formulations.csv` — one row per LNP record
- `data/exports/lnp_formulations.json` — JSON export
- `data/exports/qa_report.json` — QA validation report

## Run Tests
```bash
pytest tests/ -v
```
