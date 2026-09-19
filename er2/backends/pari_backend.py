"""The PARI backend: number theory through cypari2 (ARCHITECTURE.md §3.7).

There is a single ``cypari2.Pari()`` instance.  Arguments are converted
with ``to_pari`` and results with ``from_pari``, so users never receive a
raw ``cypari2.gen`` unless they ask for one through ``pari.raw``.

The functions come from ``er2/data/pari_functions.csv`` (§3.5, D10):
``PRELUDE`` holds the ``prelude`` rows, which become top-level names, and
``pari`` gives every ``prelude`` and ``namespace`` row as ``pari.<name>``.
"""

import csv
import functools
import inspect
from fractions import Fraction
from pathlib import Path

import cypari2
import sympy

from er2.runtime.factorization import Factorization
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational

__all__ = [
    "PARI",
    "PRELUDE",
    "dedekind_psi",
    "factor",
    "from_pari",
    "pari",
    "set_precision",
    "set_stack",
    "to_pari",
]

TABLE_PATH = Path(__file__).resolve().parent.parent / "data/pari_functions.csv"

PARI = cypari2.Pari()

# PARI's default maximum stack is only ~8 MB.  The maximum is reserved
# address space; the stack grows into it only when a computation needs it.
DEFAULT_STACK_MAX = 2**30


def set_stack(size=None, max_size=None):
    """Set the PARI stack size and its maximum, in bytes.

    This clears the PARI stack, so call it before a computation, not
    during one.  ``None`` keeps the current value.
    """
    size = PARI.stacksize() if size is None else size
    max_size = PARI.stacksizemax() if max_size is None else max_size
    PARI.allocatemem(size, max(size, max_size), silent=True)


set_stack(max_size=DEFAULT_STACK_MAX)


def set_precision(digits):
    """Set the precision of real results, in decimal digits."""
    PARI.set_real_precision(digits)


# cypari2 lowers PARI's real precision to 15 digits (a Python float); ER2
# uses GP's default, 38 digits.  cypari2 methods do not read this default,
# so ``_function`` passes it to every method that takes ``precision``.
DEFAULT_PRECISION = 38
set_precision(DEFAULT_PRECISION)


def to_pari(obj):
    """Convert an ER2 (or Python, or SymPy) number to a PARI object."""
    if isinstance(obj, cypari2.gen.Gen):
        return obj
    if isinstance(obj, (bool, int)):
        return PARI(int(obj))
    if isinstance(obj, Fraction):
        return PARI(obj.numerator) / obj.denominator
    if isinstance(obj, sympy.Rational):
        return PARI(int(obj.p)) / int(obj.q)
    if isinstance(obj, Mod):
        return PARI.Mod(int(obj.lift()), int(obj.modulus))
    if isinstance(obj, float):
        return PARI(obj)
    if isinstance(obj, (list, tuple)):
        return PARI([to_pari(item) for item in obj])
    if isinstance(obj, str):
        return obj
    raise TypeError(f"cannot convert {type(obj).__name__} to PARI")


def from_pari(obj):
    """Convert a PARI object to ER2 numbers, lists and SymPy objects.

    Raises ``TypeError`` for PARI types that ER2 does not support yet
    (M4); ``pari.raw`` gives the unconverted result.
    """
    if not isinstance(obj, cypari2.gen.Gen):
        return obj
    kind = obj.type()
    converter = _FROM_PARI.get(kind)
    if converter is None:
        raise TypeError(
            f"ER2 cannot convert the PARI type {kind} yet; "
            "use pari.raw to get the raw PARI object"
        )
    return converter(obj)


def _real(obj):
    """Convert a ``t_REAL`` exactly to a SymPy ``Float``."""
    bits = int(PARI.bitprecision(obj))
    if obj == 0:
        return sympy.Float(0, precision=bits)
    shift = bits - 1 - int(PARI.exponent(obj))
    mantissa = int(PARI.truncate(obj * PARI(2) ** shift))
    return sympy.Float(
        sympy.Integer(mantissa) / sympy.Integer(2) ** shift, precision=bits
    )


def _polynomial(obj):
    """Convert a ``t_POL`` to a SymPy expression."""
    var = sympy.Symbol(str(PARI.variable(obj)))
    coefficients = [sympy.sympify(from_pari(c)) for c in PARI.Vecrev(obj)]
    return sympy.Add(*(c * var**k for k, c in enumerate(coefficients)))


def _matrix(obj):
    rows, cols = int(PARI.matsize(obj)[0]), int(PARI.matsize(obj)[1])
    return sympy.Matrix(
        rows, cols, lambda i, j: sympy.sympify(from_pari(obj[i, j]))
    )


_FROM_PARI = {
    "t_INT": lambda obj: Integer(int(obj)),
    "t_FRAC": lambda obj: Rational(
        int(PARI.numerator(obj)), int(PARI.denominator(obj))
    ),
    "t_REAL": _real,
    "t_COMPLEX": lambda obj: (
        sympy.sympify(from_pari(PARI.real(obj)))
        + sympy.I * sympy.sympify(from_pari(PARI.imag(obj)))
    ),
    "t_INTMOD": lambda obj: Mod(int(PARI.lift(obj)), int(obj.mod())),
    "t_POL": _polynomial,
    "t_RFRAC": lambda obj: (
        _polynomial(PARI.numerator(obj)) / _polynomial(PARI.denominator(obj))
    ),
    "t_VEC": lambda obj: [from_pari(item) for item in obj],
    "t_COL": lambda obj: [from_pari(item) for item in obj],
    "t_VECSMALL": lambda obj: [Integer(int(item)) for item in obj],
    "t_MAT": _matrix,
    "t_STR": str,
}


def _call(pari_name, *args, **kwargs):
    function = getattr(PARI, pari_name)
    args = [to_pari(arg) for arg in args]
    kwargs = {key: to_pari(value) for key, value in kwargs.items()}
    return from_pari(function(*args, **kwargs))


def factor(n, limit=None):
    """Factor an integer or a rational number with PARI.

    ``limit=B`` gives a partial factorization: only primes up to ``B``
    are found by trial division, and factors that may be composite are
    listed in ``unfactored`` (D7).  A full factorization can take very
    long for large numbers; Ctrl-C interrupts it.
    """
    n = to_pari(n)
    if limit is None:
        matrix = PARI.factor(n)
    else:
        matrix = PARI.factor(n, to_pari(limit))
    pairs = [
        (int(matrix[i, 0]), int(matrix[i, 1]))
        for i in range(int(PARI.matsize(matrix)[0]))
    ]
    unit = 1
    if pairs and pairs[0][0] == -1:
        unit = -1
        pairs.pop(0)
    unfactored = ()
    if limit is not None:
        unfactored = [p for p, _ in pairs if not PARI.ispseudoprime(p)]
    return Factorization(pairs, unit=unit, unfactored=unfactored)


def dedekind_psi(n):
    """Dedekind psi: ``n * prod(1 + 1/p)`` over the primes ``p`` of ``n``.

    ``psi`` is not used as a name, because PARI's ``psi`` is the digamma
    function (``pari.digamma``), as is SciPy's (D5).
    """
    n = to_pari(n)
    if n.type() != "t_INT" or n <= 0:
        raise ValueError("dedekind_psi() needs a positive integer")
    result = n
    for p in PARI.factor(n)[0]:
        result = result / p * (p + 1)
    return from_pari(result)


# Prelude predicates that return a Python bool.  ``ispower`` and
# ``isprimepower`` return an exponent, as in PARI (0 when false).
_BOOLEAN = {"isprime", "ispseudoprime", "issquare", "issquarefree"}


def _function(row):
    """Return the ER2 function for a row of the PARI table."""
    pari_name, er2_name = row["pari_name"], row["er2_name"]
    call = functools.partial(_call, pari_name)
    takes_precision = "precision" in _parameters(getattr(PARI, pari_name))
    convert = bool if er2_name in _BOOLEAN else _same

    def function(*args, **kwargs):
        if takes_precision and "precision" not in kwargs:
            kwargs["precision"] = PARI.get_real_precision_bits()
        return convert(call(*args, **kwargs))

    function.__name__ = function.__qualname__ = er2_name
    function.__doc__ = (
        f"{row['summary']}\n\nPARI function ``{pari_name}``."
        if row["summary"]
        else f"PARI function ``{pari_name}``."
    )
    return function


def _same(value):
    return value


def _parameters(method):
    try:
        return inspect.signature(method).parameters
    except (TypeError, ValueError):
        return {}


def _read_table():
    with TABLE_PATH.open(newline="", encoding="utf-8") as fh:
        return [
            row
            for row in csv.DictReader(fh)
            if row["status"] in ("prelude", "namespace")
        ]


_ROWS = _read_table()

# Top-level ER2 functions (the ``prelude`` rows); ``factor`` has its own.
PRELUDE = {
    row["er2_name"]: _function(row)
    for row in _ROWS
    if row["status"] == "prelude"
}
PRELUDE["factor"] = factor


class PariNamespace:
    """PARI functions by their ER2 names: ``pari.eulerphi`` is ``phi``.

    Every function converts its arguments and results (ER2 numbers in and
    out).  ``pari.raw`` is the cypari2 instance itself, for the rare cases
    that need raw PARI objects.
    """

    def __init__(self, rows):
        """Index the ``prelude`` and ``namespace`` rows by ER2 name."""
        self._rows = {row["er2_name"]: row for row in rows}
        self.raw = PARI
        self.set_stack = set_stack
        self.set_precision = set_precision

    def __getattr__(self, name):
        """Return the ER2 function for ``name`` (created on first use)."""
        row = self.__dict__.get("_rows", {}).get(name)
        if row is None:
            raise AttributeError(f"PARI has no ER2 function {name!r}")
        function = PRELUDE.get(name) or _function(row)
        setattr(self, name, function)
        return function

    def __dir__(self):
        """List the available functions."""
        return sorted({*self._rows, "raw", "set_precision", "set_stack"})

    def __repr__(self):
        """Return a short description."""
        return f"<PARI functions ({len(self._rows)}), use dir(pari)>"


pari = PariNamespace(_ROWS)
