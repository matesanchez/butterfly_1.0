import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_schema_creates_tables():
    schema = (ROOT / 'db' / 'schema.sql').read_text(encoding='utf-8')
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert 'sources' in tables
        assert 'documents' in tables
        assert 'lnp_records' in tables
        assert 'crawl_runs' in tables
        conn.close()
    finally:
        try:
            Path(db_path).unlink()
        except OSError:
            pass
