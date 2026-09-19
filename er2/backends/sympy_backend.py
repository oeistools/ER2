"""The SymPy backend: computer algebra (ARCHITECTURE.md §3.7).

Arguments are converted with ``to_sympy`` before calling SymPy, and
results with ``from_sympy`` afterwards, so exact numbers come back as
ER2 ``Integer`` and ``Rational``.  Symbolic expressions stay SymPy
objects (D11).
"""

import functools

import sympy

from er2.runtime.numbers import Integer, Rational

__all__ = [
    "cancel",
    "collect",
    "diff",
    "expand",
    "factor",
    "factorial",
    "from_sympy",
    "gcd",
    "integrate",
    "lcm",
    "limit",
    "series",
    "simplify",
    "solve",
    "to_sympy",
]


def to_sympy(obj):
    """Convert ER2 numbers in ``obj`` (and in its containers) to SymPy."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return sympy.Integer(int(obj))
    if isinstance(obj, Rational):
        return sympy.Rational(obj.numerator, obj.denominator)
    if isinstance(obj, (list, tuple, set, frozenset)):
        return type(obj)(map(to_sympy, obj))
    if isinstance(obj, dict):
        return {to_sympy(k): to_sympy(v) for k, v in obj.items()}
    return obj


def from_sympy(obj):
    """Convert SymPy numbers in ``obj`` (and in its containers) to ER2.

    ``sympy.Integer`` becomes ``Integer`` and ``sympy.Rational`` becomes
    ``Rational``; other SymPy objects are returned unchanged.
    """
    if isinstance(obj, sympy.Integer):
        return Integer(int(obj))
    if isinstance(obj, sympy.Rational):
        return Rational(int(obj.p), int(obj.q))
    if isinstance(obj, (list, tuple, set, frozenset)):
        return type(obj)(map(from_sympy, obj))
    if isinstance(obj, dict):
        return {from_sympy(k): from_sympy(v) for k, v in obj.items()}
    return obj


def _boundary(function):
    """Wrap a SymPy function with the ER2 conversions."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        args = [to_sympy(arg) for arg in args]
        kwargs = {key: to_sympy(value) for key, value in kwargs.items()}
        return from_sympy(function(*args, **kwargs))

    return wrapper


expand = _boundary(sympy.expand)
factor = _boundary(sympy.factor)
simplify = _boundary(sympy.simplify)
collect = _boundary(sympy.collect)
cancel = _boundary(sympy.cancel)
diff = _boundary(sympy.diff)
integrate = _boundary(sympy.integrate)
limit = _boundary(sympy.limit)
solve = _boundary(sympy.solve)
series = _boundary(sympy.series)
gcd = _boundary(sympy.gcd)
lcm = _boundary(sympy.lcm)
factorial = _boundary(sympy.factorial)
