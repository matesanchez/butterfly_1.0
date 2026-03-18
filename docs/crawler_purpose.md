# LNP Literature Crawler Purpose

## Goal
Build an automated crawler that discovers, retrieves, parses, and structures scientific literature describing lipid nanoparticle (LNP) therapeutics.

## What the crawler collects
For each relevant paper, article, preprint, or report, the crawler should extract:
- Source name
- Journal or site
- Article title
- DOI / PMID / PMCID when available
- Lipid mix reagents
- Lipid ratios or molar percentages
- Cell type, tissue, animal model, or organism studied
- Payload type (e.g. mRNA, siRNA, plasmid DNA, CRISPR cargo, protein)
- Administration route when stated
- Other relevant formulation notes

## Primary use case
Create a searchable local database of LNP formulation evidence so researchers can compare formulations across sources.

## Design principles
- Prefer APIs over brittle scraping
- Preserve source traceability for every extracted record
- Keep the stack easy to run locally
- Make every stage resumable and testable
- Separate raw text, parsed text, and normalized structured data

## Non-goals
- Rehosting copyrighted full text beyond what is allowed
- Replacing manual scientific review
- Building a large distributed crawler before the extraction logic is validated

## Definition of done
The crawler is successful when a single command can:
1. Read the source registry
2. Discover new candidate literature
3. Fetch text or abstracts
4. Extract LNP formulation fields
5. Store the data in SQLite
6. Run QA checks
7. Export results for review
