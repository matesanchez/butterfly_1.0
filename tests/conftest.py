import pytest
from pathlib import Path
from unittest.mock import patch
import lnp_crawler.db as db_module
from lnp_crawler.config import DB_PATH

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    test_db = tmp_path / "test.sqlite"
    with patch.object(db_module, "DB_PATH", test_db):
        # initialize schema if available
        schema = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
        if schema.exists():
            db_module.init_schema(schema)
        yield
