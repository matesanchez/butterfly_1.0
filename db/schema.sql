PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    homepage TEXT,
    api_url TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    last_crawled_at TEXT
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY,
    source_id INTEGER,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    discovered_count INTEGER DEFAULT 0,
    fetched_count INTEGER DEFAULT 0,
    inserted_count INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL,
    external_id TEXT,
    doi TEXT,
    pmid TEXT,
    pmcid TEXT,
    title TEXT NOT NULL,
    journal_or_site TEXT,
    publication_date TEXT,
    source_url TEXT,
    abstract_text TEXT,
    full_text_path TEXT,
    raw_hash TEXT,
    pipeline_status TEXT NOT NULL DEFAULT 'DISCOVERED',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(doi),
    UNIQUE(source_id, external_id),
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS lnp_records (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    lipid_mix_text TEXT,
    lipid_reagents_json TEXT,
    lipid_ratios_text TEXT,
    lipid_ratios_json TEXT,
    cells_or_organisms TEXT,
    payload TEXT,
    administration_route TEXT,
    other_relevant_info TEXT,
    evidence_span TEXT,
    extraction_confidence REAL,
    reviewer_status TEXT DEFAULT 'unreviewed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
