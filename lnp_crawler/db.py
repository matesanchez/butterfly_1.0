import contextlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from lnp_crawler.config import DB_PATH
from lnp_crawler.logger import get_logger

log = get_logger(__name__)


@contextlib.contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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

def init_schema(schema_path: Path) -> None:
    with get_connection() as conn:
        conn.executescript(schema_path.read_text(encoding='utf-8'))


def upsert_source(name: str, homepage: Optional[str], api_url: Optional[str]) -> int:
    with get_connection() as conn:
        conn.execute('INSERT OR IGNORE INTO sources (name, homepage, api_url) VALUES (?, ?, ?)', (name, homepage, api_url))
        row = conn.execute('SELECT id FROM sources WHERE name = ?', (name,)).fetchone()
        return int(row['id'])


def start_crawl_run(source_id: Optional[int]) -> int:
    with get_connection() as conn:
        cur = conn.execute('INSERT INTO crawl_runs (source_id, started_at, status) VALUES (?, ?, ?)', (source_id, datetime.now(timezone.utc).isoformat(), 'RUNNING'))
        return int(cur.lastrowid)


def finish_crawl_run(run_id: int, status: str, discovered: int = 0, fetched: int = 0, inserted: int = 0, error: Optional[str] = None) -> None:
    with get_connection() as conn:
        conn.execute('UPDATE crawl_runs SET finished_at = ?, status = ?, discovered_count = ?, fetched_count = ?, inserted_count = ?, error_message = ? WHERE id = ?', (datetime.now(timezone.utc).isoformat(), status, discovered, fetched, inserted, error, run_id))


def upsert_document(doc: dict) -> Optional[int]:
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


def update_document_status(document_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute('UPDATE documents SET pipeline_status = ? WHERE id = ?', (status, document_id))


def get_documents_by_status(status: str):
    with get_connection() as conn:
        return conn.execute('SELECT * FROM documents WHERE pipeline_status = ? ORDER BY id', (status,)).fetchall()


def insert_lnp_record(rec: dict) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO lnp_records (document_id, lipid_mix_text, lipid_reagents_json, lipid_ratios_text, lipid_ratios_json, cells_or_organisms, payload, administration_route, other_relevant_info, evidence_span, extraction_confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rec.get('document_id'), rec.get('lipid_mix_text'), rec.get('lipid_reagents_json'), rec.get('lipid_ratios_text'), rec.get('lipid_ratios_json'), rec.get('cells_or_organisms'), rec.get('payload'), rec.get('administration_route'), rec.get('other_relevant_info'), rec.get('evidence_span'), rec.get('extraction_confidence', 0.0), now, now),
        )
        return int(cur.lastrowid)
