# Architecture

## Pipeline Stages
1. Source discovery (API queries → candidate list)
2. Metadata fetch (abstracts, OA full-text, PMC XML)
3. Text parsing (HTML/XML → clean text with sections)
4. LNP field extraction (regex → JSON fields + confidence score)
5. Normalization (canonical lipid/payload names)
6. Deduplication (DOI + fuzzy title)
7. SQLite upsert
8. QA checks
9. CSV/JSON export
10. Registry update

## State Machine
DISCOVERED → FETCHED → PARSED → EXTRACTED → LOADED
(any stage can transition to FAILED)

## Source Priority
1. PubMed (NCBI eUtils) — highest recall for peer-reviewed articles
2. Europe PMC — OA full-text access, strong API
3. bioRxiv / medRxiv — preprints
4. Crossref, OpenAlex, Semantic Scholar — metadata enrichment
5. DOAJ — open-access journal index
6. Unpaywall — OA PDF resolver (used in fetch stage)
