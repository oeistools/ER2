r"""The On-Line Encyclopedia of Integer Sequences (ARCHITECTURE.md §10).

``oeis`` is in the prelude::

    s = oeis.sequence("A000045")        # Fibonacci numbers
    s[10]                               # 55, using the sequence's offset
    oeis.identify([1, 2, 5, 14, 42])    # which sequences contain these terms
    oeis.identify(sigma, 20)            # ... or the first 20 values of sigma
    oeis.check(phi, "A000010")          # compare phi with the OEIS b-file
    oeis.write_bfile(phi, "A000010", 10000)

It builds on the author's ``oeis-tools`` package (``pip install
'er2[oeis]'``), which fetches sequences and b-files; ER2 adds search, ER2
numbers (terms are ``Integer``), checks and LaTeX.  Nothing is imported
from the network stack until an OEIS function is called, so the prelude
entry costs no startup time.
"""

import functools
import itertools

from er2.printing import _escape, latex
from er2.runtime.numbers import Integer

__all__ = [
    "Check",
    "OEISError",
    "OEISSequence",
    "check",
    "identify",
    "search",
    "sequence",
    "write_bfile",
]

OEIS_URL = "https://oeis.org"
# OEIS returns search results in pages of 10.
PAGE_SIZE = 10
TIMEOUT = 30
HEADERS = {"User-Agent": "er2 (https://github.com/oeistools/ER2)"}


class OEISError(Exception):
    """A sequence that does not exist, or OEIS could not be reached."""


def _tools():
    """Return the ``oeis_tools`` package, or explain how to install it."""
    try:
        import oeis_tools
    except ImportError:
        raise ImportError(
            "er2.oeis needs the oeis-tools package: "
            "pip install 'er2[oeis]' (or pip install oeis-tools)"
        ) from None
    return oeis_tools


def _search_page(query, start=0):
    """Return one page of raw OEIS search results (a list of records)."""
    _tools()  # a clear message if the er2[oeis] extra is missing
    import requests

    try:
        response = requests.get(
            f"{OEIS_URL}/search",
            params={"q": query, "fmt": "json", "start": start},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OEISError(f"cannot reach the OEIS: {exc}") from exc
    return response.json() or []


class OEISSequence:
    """An OEIS entry: its name, offset and terms, as ER2 values.

    ``seq.terms`` are the terms shown on the OEIS page; ``seq[n]`` is
    ``a(n)`` for the sequence's own indexing (``seq.offset``), read from
    the b-file when ``n`` is beyond the shown terms.  ``seq.details`` is
    the full ``oeis_tools.Sequence`` (comments, formulas, programs,
    authors, ...), fetched on first use.
    """

    def __init__(self, record):
        """Create the sequence from an OEIS JSON record."""
        self.record = record
        self.id = f"A{int(record['number']):06d}"
        self.name = record.get("name", "")
        self.terms = [
            Integer(t) for t in record.get("data", "").split(",") if t
        ]
        offset = record.get("offset", "0").split(",")[0]
        self.offset = Integer(offset)
        self.keywords = [k for k in record.get("keyword", "").split(",") if k]

    @property
    def url(self):
        """The sequence's page on oeis.org."""
        return f"{OEIS_URL}/{self.id}"

    @functools.cached_property
    def details(self):
        """The full ``oeis_tools.Sequence`` (fetched from OEIS once)."""
        return _tools().Sequence(self.id)

    def bfile(self):
        """Return the b-file as a dict ``{n: a(n)}`` (downloaded once)."""
        return _bfile(self.id)

    def bibtex(self):
        """Return a BibTeX entry citing this sequence (from oeis-tools)."""
        return self.details.get_bibtex()

    def __getitem__(self, n):
        """Return ``a(n)``, with the OEIS offset (``seq[seq.offset]`` first).

        A slice ``seq[a:b]`` returns ``[a(a), ..., a(b - 1)]``.
        """
        if isinstance(n, slice):
            start = self.offset if n.start is None else n.start
            stop = self.offset + len(self.terms) if n.stop is None else n.stop
            return [self[k] for k in range(start, stop, n.step or 1)]
        index = int(n) - self.offset
        if 0 <= index < len(self.terms):
            return self.terms[index]
        try:
            return self.bfile()[int(n)]
        except KeyError:
            raise IndexError(f"{self.id} has no known term a({n})") from None

    def __len__(self):
        """Return the number of terms shown on the OEIS page."""
        return len(self.terms)

    def __iter__(self):
        """Iterate over the terms shown on the OEIS page."""
        return iter(self.terms)

    def __eq__(self, other):
        """Sequences are equal when they are the same OEIS entry."""
        if isinstance(other, OEISSequence):
            return self.id == other.id
        return NotImplemented

    def __hash__(self):
        """Hash by OEIS identifier."""
        return hash((OEISSequence, self.id))

    def _preview(self, count=10):
        shown = ", ".join(map(str, self.terms[:count]))
        return shown + (", ..." if len(self.terms) > count else "")

    def __repr__(self):
        """Return ``A000045 (Fibonacci numbers): 0, 1, 1, 2, ...``."""
        return f"{self.id} ({self.name}): {self._preview()}"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer=None):
        terms = ", ".join(map(str, self.terms[:10]))
        dots = r", \ldots" if len(self.terms) > 10 else ""
        return rf"\text{{{self.id} ({_escape(self.name)})}}: {terms}{dots}"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()


def sequence(oeis_id):
    """Return the OEIS sequence ``oeis_id`` (``"A000045"`` or ``45``)."""
    return _sequence(_normalize_id(oeis_id))


@functools.lru_cache(maxsize=256)
def _sequence(oeis_id):
    records = _search_page(f"id:{oeis_id}")
    if not records:
        raise OEISError(f"{oeis_id} is not in the OEIS")
    return OEISSequence(records[0])


def _normalize_id(oeis_id):
    if isinstance(oeis_id, int) and not isinstance(oeis_id, bool):
        return f"A{oeis_id:06d}"
    text = str(oeis_id).strip().upper()
    if not _tools().check_id(text):
        raise ValueError(f"not an OEIS identifier: {oeis_id!r}")
    return text


@functools.lru_cache(maxsize=64)
def _bfile(oeis_id):
    tools = _tools()
    bfile = tools.BFile(oeis_id)
    values, indices = bfile.get_bfile_data(), bfile.get_bfile_indices()
    if values is None or indices is None:
        raise OEISError(f"cannot read the b-file of {oeis_id}")
    return {Integer(n): Integer(v) for n, v in zip(indices, values)}


def search(query, limit=10):
    """Search the OEIS; return up to ``limit`` matching sequences.

    ``query`` is OEIS search syntax (``"catalan"``, ``"keyword:nice"``,
    ``"1,2,5,14,42"``) or a list of terms.
    """
    if not isinstance(query, str):
        query = ",".join(str(int(term)) for term in query)
    results = []
    for start in itertools.count(0, PAGE_SIZE):
        page = _search_page(query, start)
        results.extend(OEISSequence(record) for record in page)
        if len(page) < PAGE_SIZE or len(results) >= limit:
            break
    return results[:limit]


def identify(values, count=20, offset=1, limit=10):
    """Return the OEIS sequences that contain ``values``.

    ``values`` is a list of terms, or a function: ``identify(sigma, 20)``
    searches for ``sigma(1), ..., sigma(20)`` (``offset`` is the first
    index).  The OEIS ranks the matches; the best one comes first.
    """
    if callable(values):
        values = [values(k) for k in range(offset, offset + count)]
    return search(list(values), limit=limit)


class Check:
    """The result of ``check``: true when every compared term agrees."""

    def __init__(self, oeis_id, checked, mismatch=None):
        """Store how many terms agreed and the first mismatch, if any."""
        self.oeis_id = oeis_id
        self.checked = checked
        self.mismatch = mismatch  # (n, OEIS value, computed value)

    def __bool__(self):
        """Whether all compared terms agree."""
        return self.mismatch is None

    def __repr__(self):
        """Describe the result in one line."""
        if self.mismatch is None:
            return f"{self.oeis_id}: {self.checked} terms agree"
        n, expected, got = self.mismatch
        return (
            f"{self.oeis_id}: a({n}) = {expected} in the OEIS, "
            f"but the function gives {got} "
            f"({self.checked} terms agreed before)"
        )


def check(f, oeis_id, count=None):
    """Compare ``f(n)`` with the OEIS b-file of ``oeis_id``.

    All b-file terms are compared, or the first ``count``.  The result is
    true when they all agree; otherwise it shows the first mismatch.
    """
    oeis_id = _normalize_id(oeis_id)
    terms = sorted(_bfile(oeis_id).items())
    if count is not None:
        terms = terms[:count]
    for checked, (n, expected) in enumerate(terms):
        got = f(n)
        if got != expected:
            return Check(oeis_id, checked, (n, expected, got))
    return Check(oeis_id, len(terms))


def write_bfile(f, oeis_id, count, offset=1, path=None):
    """Write ``f(offset), ..., f(offset + count - 1)`` as an OEIS b-file.

    The file is named as OEIS expects (``b000010.txt`` for ``A000010``),
    in the current directory unless ``path`` says otherwise.  Returns the
    path of the file.
    """
    oeis_id = _normalize_id(oeis_id)
    values = [int(f(n)) for n in range(offset, offset + count)]
    return _tools().bfile.create_bfile(oeis_id, values, offset, path)
