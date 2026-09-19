"""Public mathematical functions and their backends (ARCHITECTURE.md §3.4).

This is the only place that knows which backend computes what.  Each
entry of ``TABLE`` is a list of ``(predicate, implementation)`` pairs; a
public function calls the first implementation whose predicate accepts
its positional arguments.

``FUNCTIONS`` maps every public name to its function; the prelude
exposes them all.
"""

import sys
from fractions import Fraction

from er2 import _lazy
from er2.backends import pari_backend

__all__ = ["FUNCTIONS", "TABLE", "implementation"]


class _SympyBackend:
    """A SymPy backend function, imported on first use (``er2._lazy``)."""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def resolve(self):
        from er2.backends import sympy_backend

        return getattr(sympy_backend, self.name)


def symbolic(args, kwargs):
    """Whether an argument is a symbolic (non-numeric) SymPy object."""
    if not _lazy.sympy_loaded():
        return False  # no SymPy object can exist yet
    basic = sys.modules["sympy"].Basic
    return any(isinstance(arg, basic) and not arg.is_Number for arg in args)


def number(args, kwargs):
    """Whether the first argument is an exact number."""
    if not args:
        return False
    if isinstance(args[0], (int, Fraction)):
        return True
    return _lazy.sympy_loaded() and isinstance(
        args[0], sys.modules["sympy"].Rational
    )


def anything(args, kwargs):
    """Accept any arguments."""
    return True


def rational_univariate(args, kwargs):
    """Whether ``args`` is one univariate polynomial over Q, no options.

    PARI factors these 14-125x faster than SymPy (docs/BENCHMARKS.md);
    options such as ``extension=`` or ``modulus=`` stay with SymPy.
    """
    return (
        len(args) == 1
        and not kwargs
        and _lazy.sympy_loaded()
        and pari_backend.is_rational_univariate(args[0])
    )


sympy_backend = _SympyBackend  # TABLE entries: sympy_backend("factor")

TABLE = {
    "expand": [(anything, sympy_backend("expand"))],
    "factor": [
        (rational_univariate, pari_backend.factor_polynomial),
        (symbolic, sympy_backend("factor")),
        (number, pari_backend.factor),
    ],
    "simplify": [(anything, sympy_backend("simplify"))],
    "collect": [(anything, sympy_backend("collect"))],
    "cancel": [(anything, sympy_backend("cancel"))],
    "diff": [(anything, sympy_backend("diff"))],
    "integrate": [(anything, sympy_backend("integrate"))],
    "limit": [(anything, sympy_backend("limit"))],
    "solve": [(anything, sympy_backend("solve"))],
    "series": [(anything, sympy_backend("series"))],
    # Exact: PARI's ``n!`` for integers, SymPy for symbols (``factorial``
    # in PARI returns a real number).
    "factorial": [
        (number, pari_backend.factorial),
        (anything, sympy_backend("factorial")),
    ],
    "dedekind_psi": [(anything, pari_backend.dedekind_psi)],
    "jordan_totient": [(anything, pari_backend.jordan_totient)],
    "radical": [(anything, pari_backend.radical)],
}
# The other PARI prelude functions; gcd and lcm of expressions use SymPy.
for _name, _function in pari_backend.PRELUDE.items():
    if _name not in TABLE:
        TABLE[_name] = [(anything, _function)]
for _name in ("gcd", "lcm"):
    TABLE[_name].insert(0, (symbolic, sympy_backend(_name)))


def implementation(name, args, kwargs=None):
    """Return the implementation of ``name`` for these arguments."""
    kwargs = kwargs or {}
    for accepts, function in TABLE[name]:
        if accepts(args, kwargs):
            if isinstance(function, _SympyBackend):
                return function.resolve()
            return function
    kind = type(args[0]).__name__ if args else "no"
    raise TypeError(f"{name}() does not support {kind} arguments")


def _call(name, *args, **kwargs):
    return implementation(name, args, kwargs)(*args, **kwargs)


def expand(expr, *args, **kwargs):
    """Expand products and powers: ``(x + 1)^2`` gives ``x^2 + 2*x + 1``."""
    return _call("expand", expr, *args, **kwargs)


def factor(obj, *args, **kwargs):
    """Factor an integer, a rational number, or an expression.

    ``factor(12)`` gives ``2^2 * 3`` (PARI); ``factor(x^2 - 1)`` gives
    ``(x - 1)*(x + 1)`` (SymPy).  For numbers, ``limit=B`` gives a
    partial factorization by trial division up to ``B`` (D7).
    """
    return _call("factor", obj, *args, **kwargs)


def simplify(expr, *args, **kwargs):
    """Return the simplest form of ``expr`` that SymPy finds."""
    return _call("simplify", expr, *args, **kwargs)


def collect(expr, syms, *args, **kwargs):
    """Collect the terms of ``expr`` by powers of ``syms``."""
    return _call("collect", expr, syms, *args, **kwargs)


def cancel(expr, *args, **kwargs):
    """Write a rational function as ``p/q`` in lowest terms."""
    return _call("cancel", expr, *args, **kwargs)


def diff(expr, *symbols, **kwargs):
    """Differentiate: ``diff(f, x)``, ``diff(f, x, 2)``, ``diff(f, x, y)``."""
    return _call("diff", expr, *symbols, **kwargs)


def integrate(expr, *limits, **kwargs):
    """Integrate: ``integrate(f, x)`` or ``integrate(f, (x, a, b))``."""
    return _call("integrate", expr, *limits, **kwargs)


def limit(expr, var, point, dir="+"):  # noqa: A002 (SymPy's name)
    """Return the limit of ``expr`` as ``var`` tends to ``point``."""
    return _call("limit", expr, var, point, dir=dir)


def solve(expr, *symbols, **kwargs):
    """Solve ``expr = 0`` (or an ``Eq``, or a list of them)."""
    return _call("solve", expr, *symbols, **kwargs)


def series(expr, x=None, x0=0, n=6, dir="+"):  # noqa: A002 (SymPy's name)
    """Return the power series of ``expr`` around ``x = x0``.

    The series is truncated with an ``O((x - x0)^n)`` term.
    """
    return _call("series", expr, x, x0, n, dir)


def factorial(n):
    """Return ``n!`` exactly; ``factorial(x)`` stays symbolic."""
    return _call("factorial", n)


def dedekind_psi(n):
    """Dedekind psi: ``n * prod(1 + 1/p)`` over the primes ``p | n``.

    ER2 has no ``psi``: PARI's and SciPy's ``psi`` is the digamma
    function, available as ``pari.digamma`` (D5).
    """
    return _call("dedekind_psi", n)


def jordan_totient(n, k):
    """Jordan's totient ``J_k(n)``: ``n^k * prod(1 - 1/p^k)`` over ``p | n``.

    ``jordan_totient(n, 1)`` is ``phi(n)``.  GP has no built-in; this is
    ``sumdiv(n, d, d^k * moebius(n/d))``.
    """
    return _call("jordan_totient", n, k)


def radical(n):
    """Return ``rad(n)``, the product of the distinct primes of ``n``.

    GP has no built-in; this is ``factorback(factorint(n)[, 1])``.
    """
    return _call("radical", n)


def _public(name):
    """Return the dispatching public function for a PARI prelude row."""
    source = pari_backend.PRELUDE[name]

    def function(*args, **kwargs):
        return _call(name, *args, **kwargs)

    function.__name__ = function.__qualname__ = name
    function.__doc__ = source.__doc__
    return function


FUNCTIONS = {
    function.__name__: function
    for function in (
        expand,
        factor,
        simplify,
        collect,
        cancel,
        diff,
        integrate,
        limit,
        solve,
        series,
        factorial,
        dedekind_psi,
        jordan_totient,
        radical,
    )
}
for _name in TABLE:
    if _name not in FUNCTIONS:
        FUNCTIONS[_name] = _public(_name)
