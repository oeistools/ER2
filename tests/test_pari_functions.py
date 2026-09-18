"""Integrity checks for the PARI -> ER2 name table (ARCHITECTURE.md §3.5)."""

import builtins
import csv
import keyword
import re
from collections import Counter
from pathlib import Path

import cypari2
import pytest

CSV_PATH = (
    Path(__file__).resolve().parent.parent / "er2/data/pari_functions.csv"
)
STATUSES = {"prelude", "namespace", "wrapper", "python", "conflict"}
EXPOSED = {"prelude", "namespace"}
# snake_case, a CapWords type constructor (Mod, Pol), or the constant I.
PEP8_NAME = re.compile(r"[a-z_][a-z0-9_]*|[A-Z][a-z]+|I")


@pytest.fixture(scope="module")
def rows():
    """Return all rows of the name table."""
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def exposed(rows):
    """Return the rows that ER2 exposes directly from cypari2."""
    return [r for r in rows if r["status"] in EXPOSED]


def test_statuses_are_known(rows):
    """Every row has one of the documented statuses."""
    assert {r["status"] for r in rows} <= STATUSES


def test_pari_names_are_unique(rows):
    """Each PARI function appears exactly once."""
    duplicates = Counter(r["pari_name"] for r in rows) - Counter(
        {r["pari_name"]: 1 for r in rows}
    )
    assert not duplicates


def test_exposed_er2_names_are_unique(exposed):
    """No two exposed PARI functions share an ER2 name."""
    counts = Counter(r["er2_name"] for r in exposed)
    assert [name for name, n in counts.items() if n > 1] == []


def test_exposed_er2_names_follow_pep8(exposed):
    """Exposed names follow PEP 8 naming (ARCHITECTURE.md §6.1)."""
    bad = [
        r["er2_name"]
        for r in exposed
        if not PEP8_NAME.fullmatch(r["er2_name"])
    ]
    assert bad == []


def test_exposed_er2_names_are_not_keywords(exposed):
    """Exposed names are valid identifiers, not Python keywords."""
    assert [
        r["er2_name"] for r in exposed if keyword.iskeyword(r["er2_name"])
    ] == []


def test_prelude_does_not_shadow_builtins(rows):
    """The prelude never hides a Python builtin (ARCHITECTURE.md §1.1)."""
    prelude = [r["er2_name"] for r in rows if r["status"] == "prelude"]
    assert [name for name in prelude if hasattr(builtins, name)] == []


def test_exposed_functions_exist_in_cypari2(exposed):
    """Every prelude/namespace row resolves to a cypari2 method."""
    pari = cypari2.Pari()
    missing = [
        r["pari_name"] for r in exposed if not hasattr(pari, r["pari_name"])
    ]
    assert missing == []


@pytest.mark.parametrize(
    ("pari_name", "er2_name"),
    [("eulerphi", "phi"), ("moebius", "mu"), ("bigomega", "bigomega")],
)
def test_draft_names_are_mapped(rows, pari_name, er2_name):
    """The names used in the draft map to the right PARI functions."""
    row = next(r for r in rows if r["pari_name"] == pari_name)
    assert (row["er2_name"], row["status"]) == (er2_name, "prelude")
