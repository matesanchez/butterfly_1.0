import subprocess
import sys


def test_pipeline_dry_run_script_entrypoint():
    result = subprocess.run(
        [sys.executable, "scripts/run_pipeline.py", "--dry-run", "--limit", "1"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PIPELINE COMPLETE" in result.stdout
