"""``er2.oeis`` against recorded OEIS responses (no network).

The fixtures in ``data/`` were recorded from oeis.org on 2026-09-19 (long
text fields trimmed).  ``test_live.py`` runs against the real site when
``ER2_NETWORK_TESTS=1``.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from er2 import oeis, prelude
from er2.printing import latex
from er2.runtime.numbers import Integer

DATA = Path(__file__).resolve().parent / "data"
SEARCHES = {
    ("id:A000045", 0): "id_A000045.json",
    ("id:A000010", 0): "id_A000010.json",
    ("1,2,5,14,42", 0): "search_catalan_terms.json",
    ("1,2,5,14,42", 10): "search_catalan_terms_start10.json",
}
BFILES = {"b000010.txt", "b000045.txt"}


class FakeResponse:
    def __init__(self, url, text, status=200):
        self.url, self.text, self.status_code = url, text, status

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} for {self.url}")

    def json(self):
        return json.loads(self.text)


@pytest.fixture
def offline(monkeypatch):
    """Serve OEIS requests from ``data/``; record every URL requested."""
    requested = []

    def fake_get(url, params=None, **kwargs):
        query = dict(params or {})
        parsed = urlparse(url)
        for key, values in parse_qs(parsed.query).items():
            query.setdefault(key, values[0])
        requested.append((parsed.path, query.get("q"), query.get("start")))
        if parsed.path == "/search":
            key = (query["q"], int(query.get("start", 0)))
            name = SEARCHES.get(key)
            text = (DATA / name).read_text() if name else "null"
            return FakeResponse(url, text)
        name = parsed.path.rsplit("/", 1)[-1]
        if name in BFILES:
            return FakeResponse(url, (DATA / name).read_text())
        return FakeResponse(url, "", status=404)

    monkeypatch.setattr(requests, "get", fake_get)
    oeis._sequence.cache_clear()
    oeis._bfile.cache_clear()
    yield requested
    oeis._sequence.cache_clear()
    oeis._bfile.cache_clear()


def test_sequence_lookup(offline):
    s = oeis.sequence("A000045")
    assert s.id == "A000045" and s.url == "https://oeis.org/A000045"
    assert s.name.startswith("Fibonacci numbers")
    assert s.offset == 0 and type(s.offset) is Integer
    assert s.terms[:10] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert all(type(t) is Integer for t in s.terms)
    assert "nonn" in s.keywords and "core" in s.keywords
    assert oeis.sequence(45) is s  # the same (cached) entry
    assert oeis.sequence("a000045") is not None


def test_terms_use_the_offset_and_the_bfile(offline):
    s = oeis.sequence("A000045")
    assert s[0] == 0 and s[10] == 55
    assert s[2:7] == [1, 2, 3, 5, 8]
    assert not any(path.endswith(".txt") for path, _, _ in offline)
    assert s[100] == 354224848179261915075  # beyond the shown terms
    assert type(s[100]) is Integer
    assert len(s.bfile()) == 120
    with pytest.raises(IndexError, match="no known term a\\(5000\\)"):
        s[5000]


def test_printing(offline):
    s = oeis.sequence("A000010")
    assert repr(s).startswith("A000010 (Euler totient function")
    assert repr(s).endswith(": 1, 1, 2, 2, 4, 2, 6, 4, 6, 4, ...")
    tex = latex(s)
    assert tex.startswith(r"\text{A000010 (Euler totient function")
    assert tex.endswith(r": 1, 1, 2, 2, 4, 2, 6, 4, 6, 4, \ldots")
    assert s._repr_latex_() == f"${tex}$"


def test_search_and_identify(offline):
    found = oeis.search([1, 2, 5, 14, 42], limit=3)
    assert [s.id for s in found] == ["A000108", "A120588", "A080937"]
    many = oeis.search("1,2,5,14,42", limit=15)  # two pages
    assert len(many) == 15 and many[0].id == "A000108"
    assert oeis.identify([1, 2, 5, 14, 42])[0].name.startswith("Catalan")
    by_function = oeis.identify(
        lambda n: prelude.namespace()["binomial"](2 * n, n) // (n + 1),
        count=5,
    )
    assert by_function[0].id == "A000108"
    assert oeis.search("9,8,7,1,2,3,4,99,1234,5") == []


def test_check_against_the_bfile(offline):
    phi = prelude.namespace()["phi"]
    result = oeis.check(phi, "A000010")
    assert result and result.checked == 300
    assert repr(result) == "A000010: 300 terms agree"
    wrong = oeis.check(lambda n: phi(n) + (n == 12), "A000010")
    assert not wrong and wrong.mismatch == (12, 4, 5)
    assert repr(wrong) == (
        "A000010: a(12) = 4 in the OEIS, but the function gives 5 "
        "(11 terms agreed before)"
    )
    assert oeis.check(phi, 10, count=50).checked == 50


def test_write_bfile(offline, tmp_path):
    phi = prelude.namespace()["phi"]
    path = oeis.write_bfile(phi, "A000010", 6, path=tmp_path)
    assert Path(path) == tmp_path / "b000010.txt"
    assert Path(path).read_text() == "1 1\n2 1\n3 2\n4 2\n5 4\n6 2\n"
    assert offline == []  # writing needs no network


def test_details_and_bibtex_come_from_oeis_tools(offline):
    s = oeis.sequence("A000045")
    assert s.details.name == s.name
    assert s.bibtex().startswith("@misc{A000045,")


def test_errors(offline):
    with pytest.raises(oeis.OEISError, match="A999999 is not in the OEIS"):
        oeis.sequence("A999999")
    with pytest.raises(ValueError, match="not an OEIS identifier"):
        oeis.sequence("fibonacci")


def test_unreachable_oeis_is_an_oeis_error(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(requests, "get", fail)
    oeis._sequence.cache_clear()
    with pytest.raises(oeis.OEISError, match="cannot reach the OEIS"):
        oeis.sequence("A000001")


def test_missing_extra_explains_how_to_install(monkeypatch):
    monkeypatch.setitem(sys.modules, "oeis_tools", None)
    with pytest.raises(ImportError, match=r"pip install 'er2\[oeis\]'"):
        oeis.search("catalan")


def test_the_prelude_entry_costs_no_startup_time():
    code = "import sys, er2.prelude; er2.prelude.namespace()['oeis']; "
    code += "print('requests' in sys.modules, 'oeis_tools' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.stdout == "False False\n", result.stderr
