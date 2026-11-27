"""Golden tests: ER2 programs and their expected output.

Every ``examples/*.er2`` and ``tests/examples/*.er2`` program has a
``tests/examples/<name>.out`` file with its exact expected output; the
programs of ``examples/ten/`` ("Ten programs in ER2") have theirs in
``tests/examples/ten/``.
"""

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PROGRAMS = sorted(
    [
        *ROOT.glob("examples/*.er2"),
        *ROOT.glob("examples/ten/*.er2"),
        *HERE.glob("*.er2"),
    ]
)


def expected_output(program):
    """Return the path of the expected output of ``program``."""
    folder = HERE / "ten" if program.parent.name == "ten" else HERE
    return folder / f"{program.stem}.out"


def test_every_program_has_expected_output():
    missing = [p.name for p in PROGRAMS if not expected_output(p).exists()]
    assert not missing


@pytest.mark.parametrize("program", PROGRAMS, ids=lambda p: p.name)
def test_golden_output(program):
    result = subprocess.run(
        [sys.executable, "-m", "er2", str(program)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    expected = expected_output(program).read_text(encoding="utf-8")
    assert result.stdout == expected
