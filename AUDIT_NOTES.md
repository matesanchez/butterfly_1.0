# Audit notes

## Reviewed attached files
- Prior round pipeline scripts, schema, clients, project metadata, and registry.
- New round test files, gold set, CI workflow, README/config, and design docs.

## Confirmed issues fixed
- Replaced inconsistent identity references with `butterfly_1.0`.
- Replaced broken `init.py` package behavior with proper `lnp_crawler/__init__.py`.
- Added missing helper modules required by the scripts.
- Added missing tests for discovery, fetch, and parse.
- Aligned normalization and dedupe helper APIs with the supplied tests.
- Kept PubMed Central and Unpaywall as fetch/enrichment helpers, not discovery sources.
- Consolidated all files into one extractable audited bundle.

## Remaining caveat
- External source client behavior is still limited by live API variability; the generated tests focus on internal contract behavior and file I/O rather than real network integration.
