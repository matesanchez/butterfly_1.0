#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp_crawler.db import finish_crawl_run, start_crawl_run, get_documents_by_status
from lnp_crawler.state_machine import DocStatus

STAGES = [
    ("discover",        "scripts.discover_documents"),
    ("fetch",           "scripts.fetch_documents"),
    ("parse",           "scripts.parse_documents"),
    ("extract",         "scripts.extract_lnp_data"),
    ("normalize",       "scripts.normalize_records"),
    ("deduplicate",     "scripts.deduplicate_records"),
    ("loaddb",          "scripts.load_database"),
    ("qa",              "scripts.run_qa"),
    ("export",          "scripts.export_results"),
    ("updateregistry",  "scripts.update_source_registry"),
]


def run_stage(name: str, module_path: str, dry_run: bool,
              limit: int = None, source: str = None) -> bool:
    if dry_run and name != "discover":
        return True
    fn = getattr(importlib.import_module(module_path), "main")
    if name == "discover":
        fn(limit=limit, source_filter=source)
    elif name == "fetch":
        fn(limit=limit)
    elif name == "parse":
        fn(limit=limit)
    else:
        fn()
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--source", default=None)
    ap.add_argument("--resume", action="store_true",
                    help="Skip stages whose output files already exist")
    args = ap.parse_args()

    run_id = start_crawl_run(None)
    try:
        # mapping of stage -> required input status to run (for --resume)
        stage_input = {
            'discover': None,
            'fetch': DocStatus.DISCOVERED.value,
            'parse': DocStatus.FETCHED.value,
            'extract': DocStatus.PARSED.value,
            'normalize': DocStatus.EXTRACTED.value,
            'deduplicate': None,
            'loaddb': None,
            'qa': None,
            'export': None,
            'updateregistry': None,
        }

        for name, module_path in STAGES:
            # If resuming, skip stages that have no work remaining
            if args.resume and stage_input.get(name):
                pending = get_documents_by_status(stage_input[name])
                if not pending:
                    continue
            ok = run_stage(name, module_path, args.dry_run, args.limit, args.source)
            if not ok:
                finish_crawl_run(run_id, "FAILED", error=f"stage {name} reported failure")
                return 2
        finish_crawl_run(run_id, "DONE")
        return 0
    except Exception as exc:
        finish_crawl_run(run_id, "FAILED", error=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())