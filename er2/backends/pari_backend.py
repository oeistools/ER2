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
import re
from fractions import Fraction
from pathlib import Path

import cypari2

from er2 import _lazy
from er2.runtime.factorization import Factorization
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational
from er2.runtime.qfb import Qfb

__all__ = [
    "PARI",
    "PRELUDE",
    "dedekind_psi",
    "factor",
    "factor_polynomial",
    "from_pari",
    "is_rational_univariate",
    "jordan_totient",
    "pari",
    "radical",
    "set_precision",
    "set_stack",
    "to_pari",
    "variable",
]

TABLE_PATH = Path(__file__).resolve().parent.parent / "data/pari_functions.csv"


class _SympyOnDemand:
    """``sympy.X`` imports SymPy on first use (``er2._lazy``).

    Number theory never needs SymPy; only conversions of SymPy objects and
    of PARI polynomials, series and reals do.
    """

    def __getattr__(self, name):
        return getattr(_lazy.sympy(), name)


sympy = _SympyOnDemand()

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
    """Convert an ER2, Python or SymPy object to a PARI object.

    Numbers, ``Mod``, ``Qfb``, lists, SymPy polynomials and rational
    functions (``t_POL``, ``t_RFRAC``), series with an ``O`` term
    (``t_SER``), matrices, and ``oo`` are supported.
    """
    if isinstance(obj, cypari2.gen.Gen):
        return obj
    if isinstance(obj, (bool, int)):
        return PARI(int(obj))
    if isinstance(obj, Fraction):
        return PARI(obj.numerator) / obj.denominator
    if isinstance(obj, Mod):
        if obj.is_polynomial:
            return PARI.Mod(to_pari(obj.lift()), to_pari(obj.modulus))
        return PARI.Mod(int(obj.lift()), int(obj.modulus))
    if isinstance(obj, Qfb):
        return PARI.Qfb(int(obj.a), int(obj.b), int(obj.c))
    if isinstance(obj, float):
        return PARI(obj)
    if isinstance(obj, (list, tuple)):
        return PARI([to_pari(item) for item in obj])
    if isinstance(obj, str):
        return obj
    if not _lazy.sympy_loaded():
        raise TypeError(f"cannot convert {type(obj).__name__} to PARI")
    if isinstance(obj, sympy.MatrixBase):
        entries = [
            to_pari(obj[i, j])
            for i in range(obj.rows)
            for j in range(obj.cols)
        ]
        return PARI.matrix(obj.rows, obj.cols, entries)
    if isinstance(obj, sympy.Basic):
        return _sympy_to_pari(obj)
    raise TypeError(f"cannot convert {type(obj).__name__} to PARI")


# Fixed GP functions used by the conversions.  Only these constant texts
# are ever parsed by GP; user values are passed as arguments.
_GP_REAL = PARI("(q, bits) -> localbitprec(bits); q * 1.")
_GP_SERIES = PARI("(p, v, n) -> p + O(v^n)")
_GP_FACTORIAL = PARI("(n) -> n!")
_GP_INFINITY = {1: PARI("+oo"), -1: PARI("-oo")}
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
# Names created with ``varhigher`` because GP reserves them.
_CREATED = set()


def variable(name):
    """Return the PARI variable called ``name``.

    GP's own variable (``'x``) is used for ordinary names.  GP reserves
    the names of its functions and constants (``sigma``, ``I``, ``Pi``),
    so those get a new variable with that name, created once and found
    again in ``variables()``.

    This never triggers a PARI error and never keeps a PARI object between
    calls: inside a Python callback (``pari.sum(f, ...)``) a PARI error
    would abort the outer PARI call, and a kept object would outlive
    PARI's temporary stack.
    """
    if _IDENTIFIER.fullmatch(name) and name not in _GP_NAMES:
        return PARI("'" + name)
    if name in _CREATED:
        for var in PARI.variables():
            if str(var) == name:
                return var
    _CREATED.add(name)
    return PARI.varhigher(name)


def _sympy_to_pari(expr):
    """Convert a SymPy number, polynomial, rational function or series."""
    if isinstance(expr, sympy.Rational):
        return PARI(int(expr.p)) / int(expr.q)
    if isinstance(expr, sympy.Float):
        exact = sympy.Rational(expr)
        return _GP_REAL(to_pari(exact), expr._prec)
    if expr is sympy.oo or expr is sympy.S.NegativeInfinity:
        return _GP_INFINITY[1 if expr is sympy.oo else -1]
    if expr is sympy.I:
        return PARI("I")
    order = expr.getO() if isinstance(expr, sympy.Expr) else None
    if order is not None:
        return _series_to_pari(expr, order)
    if not isinstance(expr, sympy.Expr):
        raise TypeError(f"cannot convert {type(expr).__name__} to PARI")
    if expr.is_number:
        re, im = expr.as_real_imag()
        if all(part.is_Rational or part.is_Float for part in (re, im)):
            if im == 0:
                return _sympy_to_pari(re)
            return _sympy_to_pari(re) + _sympy_to_pari(im) * PARI("I")
        # An inexact number (pi, sqrt(2), log(3)) becomes a real, as in GP.
        digits = int(PARI.get_real_precision()) + 5
        value = expr.evalf(digits)
        if value.is_number and value != expr:
            return _sympy_to_pari(value)
        raise TypeError(f"cannot convert the number {expr} to PARI")
    numerator, denominator = sympy.fraction(sympy.together(expr))
    result = _polynomial_to_pari(numerator)
    if denominator != 1:
        result = result / _polynomial_to_pari(denominator)
    return result


def _polynomial_to_pari(expr):
    """Build a PARI polynomial from a SymPy polynomial expression."""
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    if not symbols:
        return _sympy_to_pari(sympy.sympify(expr))
    try:
        poly = sympy.Poly(expr, *symbols)
    except sympy.PolynomialError:
        raise TypeError(f"{expr} is not a polynomial") from None
    variables = [variable(s.name) for s in symbols]
    result = PARI(0)
    for exponents, coefficient in poly.terms():
        term = _sympy_to_pari(sympy.sympify(coefficient))
        for var, exponent in zip(variables, exponents):
            term = term * var**exponent
        result = result + term
    return result


def _series_to_pari(expr, order):
    """Convert ``p + O(x^n)`` (around 0, one variable) to a PARI series."""
    variables = order.variables
    if len(variables) != 1 or any(point != 0 for point in order.point):
        raise TypeError("only series around 0 in one variable convert to PARI")
    (var,) = variables
    term = order.expr
    exponent = sympy.degree(term, var) if term != 1 else 0
    return _GP_SERIES(
        to_pari(expr.removeO()), variable(var.name), int(exponent)
    )


def from_pari(obj):
    """Convert a PARI object to ER2 numbers, lists and SymPy objects.

    Raises ``TypeError`` for PARI types that ER2 does not support
    (``t_PADIC``, ``t_FFELT``, ``t_CLOSURE``, ...); ``pari.raw`` gives the
    unconverted result.
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


def _sympify(value):
    """Return ``value`` as a SymPy object, for use as a coefficient."""
    try:
        return sympy.sympify(value, strict=True)
    except sympy.SympifyError:
        raise TypeError(
            f"ER2 cannot use {value!r} as a coefficient of a polynomial"
        ) from None


def _polynomial(obj):
    """Convert a ``t_POL`` to a SymPy expression."""
    var = sympy.Symbol(str(PARI.variable(obj)))
    coefficients = [_sympify(from_pari(c)) for c in PARI.Vecrev(obj)]
    return sympy.Add(*(c * var**k for k, c in enumerate(coefficients)))


def _series(obj):
    """Convert a ``t_SER`` to a SymPy series ``p + O(x^n)``."""
    var = PARI.variable(obj)
    precision = int(PARI.serprec(obj, var))
    body = sympy.expand(_sympify(from_pari(PARI.truncate(obj))))
    return body + sympy.O(sympy.Symbol(str(var)) ** precision)


def _matrix(obj):
    rows, cols = map(int, PARI.matsize(obj))
    return sympy.Matrix(
        rows, cols, lambda i, j: _sympify(from_pari(obj[i, j]))
    )


_FROM_PARI = {
    "t_INT": lambda obj: Integer(int(obj)),
    "t_FRAC": lambda obj: Rational(
        int(PARI.numerator(obj)), int(PARI.denominator(obj))
    ),
    "t_REAL": _real,
    "t_COMPLEX": lambda obj: (
        _sympify(from_pari(PARI.real(obj)))
        + sympy.I * _sympify(from_pari(PARI.imag(obj)))
    ),
    "t_INTMOD": lambda obj: Mod(int(PARI.lift(obj)), int(obj.mod())),
    "t_POLMOD": lambda obj: Mod(
        from_pari(PARI.lift(obj)), from_pari(obj.mod())
    ),
    "t_POL": _polynomial,
    "t_RFRAC": lambda obj: (
        _polynomial(PARI.numerator(obj)) / _polynomial(PARI.denominator(obj))
    ),
    "t_SER": _series,
    "t_QFB": lambda obj: Qfb(int(obj[0]), int(obj[1]), int(obj[2])),
    "t_INFINITY": lambda obj: sympy.oo if obj > 0 else -sympy.oo,
    "t_VEC": lambda obj: [from_pari(item) for item in obj],
    "t_COL": lambda obj: [from_pari(item) for item in obj],
    "t_VECSMALL": lambda obj: [Integer(int(item)) for item in obj],
    "t_MAT": _matrix,
    "t_STR": str,
}


def _factor_rows(matrix):
    """Yield the ``(factor, exponent)`` rows of a PARI factorization."""
    for i in range(int(PARI.matsize(matrix)[0])):
        yield matrix[i, 0], int(matrix[i, 1])


def _positive_integer(n, function):
    """Return ``n`` in PARI, or raise if it is not a positive integer."""
    n = to_pari(n)
    if n.type() != "t_INT" or n <= 0:
        raise ValueError(f"{function}() needs a positive integer")
    return n


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
    pairs = [(int(p), e) for p, e in _factor_rows(matrix)]
    unit = 1
    if pairs and pairs[0][0] == -1:
        unit = -1
        pairs.pop(0)
    unfactored = ()
    if limit is not None:
        unfactored = [p for p, _ in pairs if not PARI.ispseudoprime(p)]
    return Factorization(pairs, unit=unit, unfactored=unfactored)


def is_rational_univariate(expr):
    """Whether ``expr`` is a univariate polynomial over Q.

    That is the case where PARI factors much faster than SymPy.
    """
    if not isinstance(expr, sympy.Expr) or len(expr.free_symbols) != 1:
        return False
    (var,) = expr.free_symbols
    if not expr.is_polynomial(var):
        return False
    return sympy.Poly(expr, var).domain in (sympy.ZZ, sympy.QQ)


def factor_polynomial(expr):
    """Factor a univariate polynomial over Q with PARI, as SymPy would.

    The result has SymPy's form, ``-(x - 1)*(x + 1)``: PARI's primitive
    factors with the rational unit kept in front.
    """
    from sympy.core.mul import _keep_coeff

    poly = to_pari(expr)
    matrix = PARI.factor(poly)
    factors = [(from_pari(f), e) for f, e in _factor_rows(matrix)]
    unit = from_pari(poly / PARI.factorback(matrix))
    product = sympy.Mul(*(f**e for f, e in factors))
    return _keep_coeff(sympy.sympify(unit), product)


def factorial(n):
    """Return ``n!`` exactly (GP's ``n!``; PARI's ``factorial`` is real)."""
    if isinstance(n, bool) or int(n) != n or n < 0:
        raise ValueError("factorial() needs a nonnegative integer")
    return from_pari(_GP_FACTORIAL(int(n)))


def dedekind_psi(n):
    """Dedekind psi: ``n * prod(1 + 1/p)`` over the primes ``p`` of ``n``.

    ``psi`` is not used as a name, because PARI's ``psi`` is the digamma
    function (``pari.digamma``), as is SciPy's (D5).
    """
    n = _positive_integer(n, "dedekind_psi")
    result = n
    for p in PARI.factor(n)[0]:
        result = result / p * (p + 1)
    return from_pari(result)


def jordan_totient(n, k):
    """Jordan's totient ``J_k(n) = n^k * prod(1 - 1/p^k)`` over ``p | n``.

    ``J_k(n)`` counts the ``k``-tuples in ``[1, n]`` whose gcd with ``n``
    is 1.  ``J_1`` is Euler's totient ``phi`` (PARI ``eulerphi``), and
    ``J_2(n) / phi(n)`` is ``dedekind_psi(n)``.
    """
    n, k = _positive_integer(n, "jordan_totient"), to_pari(k)
    if k.type() != "t_INT" or k < 0:
        raise ValueError("jordan_totient() needs a nonnegative integer k")
    result = n**k
    for p in PARI.factor(n)[0]:
        power = p**k
        result = result / power * (power - 1)
    return from_pari(result)


def radical(n):
    """Return ``rad(n)``, the product of the distinct primes of ``n``.

    GP: ``factorback(factorint(n)[, 1])``.
    """
    n = _positive_integer(n, "radical")
    return from_pari(PARI.factorback(PARI.factor(n)[0]))


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
        return list(csv.DictReader(fh))


_TABLE = _read_table()
# Every GP function and constant: GP reserves these names (``variable``).
_GP_NAMES = frozenset(row["pari_name"] for row in _TABLE)
_ALL_ROWS = [
    row
    for row in _TABLE
    if row["status"] in ("prelude", "namespace", "wrapper")
]
# The rows that cypari2 methods implement directly.
_ROWS = [row for row in _ALL_ROWS if row["status"] != "wrapper"]

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
    out).  Functions that take a GP expression in GP take a Python
    function instead: ``pari.sum(lambda n: 1/n^2, 1, 10)``.  ``pari.raw``
    is the cypari2 instance itself, for the rare cases that need raw PARI
    objects.
    """

    def __init__(self, rows):
        """Index the ``prelude``, ``namespace`` and ``wrapper`` rows."""
        self._rows = {row["er2_name"]: row for row in rows}
        self.raw = PARI
        self.set_stack = set_stack
        self.set_precision = set_precision

    def __getattr__(self, name):
        """Return the ER2 function for ``name`` (created on first use)."""
        row = self.__dict__.get("_rows", {}).get(name)
        if row is None:
            raise AttributeError(f"PARI has no ER2 function {name!r}")
        if row["status"] == "wrapper":
            from er2.backends import pari_closures

            function = pari_closures.function(name, row["summary"])
        else:
            function = PRELUDE.get(name) or _function(row)
        setattr(self, name, function)
        return function

    def __dir__(self):
        """List the available functions."""
        return sorted({*self._rows, "raw", "set_precision", "set_stack"})

    def __repr__(self):
        """Return a short description."""
        return f"<PARI functions ({len(self._rows)}), use dir(pari)>"


pari = PariNamespace(_ALL_ROWS)
