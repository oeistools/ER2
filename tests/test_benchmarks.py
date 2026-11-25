"""The benchmark script runs (``--quick``), so it cannot rot unnoticed."""

import json
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
    assert "## Calculus and series" in result.stdout


def test_baseline_and_compare(tmp_path):
    """``--json`` saves a baseline that ``--compare`` reads back."""
    baseline = tmp_path / "baseline.json"
    run = [sys.executable, str(SCRIPT), "--quick"]
    saved = subprocess.run(
        [*run, "--json", str(baseline)], capture_output=True, text=True
    )
    assert saved.returncode == 0, saved.stderr
    data = json.loads(baseline.read_text())
    assert data["environment"]["er2"] and data["benchmarks"]
    assert all(b["er2_s"] > 0 for b in data["benchmarks"])
    compared = subprocess.run(
        [*run, "--compare", str(baseline)], capture_output=True, text=True
    )
    assert compared.returncode == 0, compared.stderr
    assert "| Calculus and series | expand((x + k)^20) |" in compared.stdout
    assert "Geometric mean of the changes" in compared.stdout
