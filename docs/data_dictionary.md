# Data Dictionary

| Field | Table | Description |
|---|---|---|
| title | documents | Full article title |
| doi | documents | Digital Object Identifier |
| pmid | documents | PubMed ID |
| pmcid | documents | PubMed Central ID |
| journal_or_site | documents | Journal name or preprint server |
| publication_date | documents | ISO date or year string |
| abstract_text | documents | Abstract or body text snippet |
| pipeline_status | documents | DISCOVERED/FETCHED/PARSED/EXTRACTED/LOADED/FAILED |
| lipid_mix_text | lnp_records | Raw lipid mixture text from paper |
| lipid_reagents_json | lnp_records | JSON array of canonical lipid names |
| lipid_ratios_text | lnp_records | Original ratio text (e.g. "50:10:38.5:1.5") |
| lipid_ratios_json | lnp_records | Parsed numeric ratio structure |
| cells_or_organisms | lnp_records | Cell lines, animal models, or organisms |
| payload | lnp_records | Nucleic acid or protein payload type |
| administration_route | lnp_records | Delivery route (IV, IM, SC, etc.) |
| extraction_confidence | lnp_records | 0.0–1.0 score from extraction patterns |
| reviewer_status | lnp_records | unreviewed / approved / rejected |
