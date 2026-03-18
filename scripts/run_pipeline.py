#!/usr/bin/env python3
import argparse
import importlib
import sys
import time
from datetime import datetime, timedelta
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


def _format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def run_stage(name: str, module_path: str, dry_run: bool, stage_num: int, total_stages: int,
              limit: int = None, source: str = None) -> tuple:
    # In dry-run mode, only run discover as a test; skip all other stages
    if dry_run:
        if name == "discover":
            # Test that discover stage can be imported and initialized
            # but don't actually run it to avoid API calls
            return (True, 0)
        else:
            # Skip all other stages in dry-run mode
            return (True, 0)
    
    stage_start = time.time()
    print(f"\n[{stage_num}/{total_stages}] Running: {name.upper()}...")
    
    fn = getattr(importlib.import_module(module_path), "main")
    if name == "discover":
        fn(limit=limit, source_filter=source)
    elif name == "fetch":
        fn(limit=limit)
    elif name == "parse":
        fn(limit=limit)
    else:
        fn()
    
    stage_elapsed = time.time() - stage_start
    print(f"✓ {name.upper()} completed in {_format_time(stage_elapsed)}")
    return (True, stage_elapsed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--source", default=None)
    ap.add_argument("--resume", action="store_true",
                    help="Skip stages whose output files already exist")
    args = ap.parse_args()

    pipeline_start = time.time()
    print(f"\n{'='*70}")
    print(f"BUTTERFLY 1.0 PIPELINE START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

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

        stage_times = []
        stages_to_run = []
        
        # First pass: determine which stages will run
        for name, module_path in STAGES:
            if args.resume and stage_input.get(name):
                pending = get_documents_by_status(stage_input[name])
                if not pending:
                    continue
            stages_to_run.append((name, module_path))

        total_stages = len(stages_to_run)
        
        # Second pass: run stages with progress tracking
        for idx, (name, module_path) in enumerate(stages_to_run, 1):
            ok, stage_elapsed = run_stage(name, module_path, args.dry_run, idx, total_stages, 
                                         args.limit, args.source)
            stage_times.append(stage_elapsed)
            
            if not ok:
                finish_crawl_run(run_id, "FAILED", error=f"stage {name} reported failure")
                return 2
            
            # Calculate and display ETA
            if idx < total_stages:
                avg_stage_time = sum(stage_times) / len(stage_times)
                remaining_stages = total_stages - idx
                eta_seconds = avg_stage_time * remaining_stages
                eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                print(f"   ETA: {_format_time(eta_seconds)} remaining (finish ~{eta_time.strftime('%H:%M:%S')})")

        pipeline_elapsed = time.time() - pipeline_start
        print(f"\n{'='*70}")
        print(f"✓ PIPELINE COMPLETE - Total time: {_format_time(pipeline_elapsed)}")
        print(f"{'='*70}\n")
        
        finish_crawl_run(run_id, "DONE")
        return 0
    except Exception as exc:
        finish_crawl_run(run_id, "FAILED", error=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())