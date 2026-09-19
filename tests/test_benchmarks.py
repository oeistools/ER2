"""The benchmark script runs (``--quick``), so it cannot rot unnoticed."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "benchmarks" / "run.py"


def test_benchmarks_run_quickly():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--quick"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr
    assert "## Number theory" in result.stdout
    assert "| phi(n)" in result.stdout
