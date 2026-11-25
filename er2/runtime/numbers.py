"""Exact numbers: ``Integer`` and ``Rational`` (ARCHITECTURE.md §1.1, D6).

Every integer literal in ER2 source becomes an ``Integer``.  ``Integer``
is a real ``int`` subclass, so it keeps working wherever Python or a
library expects an ``int`` (``range``, indexing, ``json``, NumPy, ...).
The only difference is that ``/`` and negative powers are exact: they
return a ``Rational`` instead of a ``float``.
"""

import math
from fractions import Fraction

from er2.printing import latex


def normalize(value):
    """Return ``value`` as an ER2 number when it is an exact integer/ratio.

    ``int`` becomes ``Integer``; a ``Fraction`` becomes ``Integer`` when
    its denominator is 1 and ``Rational`` otherwise.  Anything else
    (``bool``, ``float``, SymPy objects, ...) is returned unchanged.
    """
    if type(value) is int:
        return Integer(value)
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return Integer(value.numerator)
        if type(value) is not Rational:
            # already in lowest terms with a positive denominator: skip
            # the gcd and checks of the constructor (the hot path of
            # rational arithmetic; Python >= 3.12)
            return Rational._from_coprime_ints(
                value.numerator, value.denominator
            )
    return value


def _exact(op):
    """Wrap an ``int`` or ``Fraction`` operator so results stay ER2 numbers."""

    def method(self, *args):
        return normalize(op(self, *args))

    method.__name__ = op.__name__
    method.__doc__ = f"Exact version of ``{op.__name__}``."
    return method


def _exact_pair(op):
    """Wrap ``divmod`` so that both parts of the result are ER2 numbers."""

    def method(self, other):
        result = op(self, other)
        if result is NotImplemented:
            return result
        return tuple(map(normalize, result))

    method.__name__ = op.__name__
    method.__doc__ = f"Exact version of ``{op.__name__}``."
    return method


# ``Integer`` operators are the hot path of numeric loops (D2 risk, M4):
# they call the ``int`` slot directly and wrap the result, with no generic
# ``normalize`` step.


def _int_binary(op):
    """Wrap a binary ``int`` operator so that it returns an ``Integer``."""

    def method(self, other):
        result = op(self, other)
        if result is NotImplemented:
            return result
        return Integer(result)

    method.__name__ = op.__name__
    method.__doc__ = f"Return ``{op.__name__}`` as an ``Integer``."
    return method


def _int_unary(op):
    """Wrap a unary ``int`` operator so that it returns an ``Integer``."""

    def method(self, *args):
        return Integer(op(self, *args))

    method.__name__ = op.__name__
    method.__doc__ = f"Return ``{op.__name__}`` as an ``Integer``."
    return method


class Integer(int):
    """Exact integer; ``/`` and negative powers give a ``Rational``."""

    __slots__ = ()

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()

    def __truediv__(self, other):
        """Return ``self / other``, exactly when ``other`` is an integer."""
        if isinstance(other, int):
            if other == 0:
                raise ZeroDivisionError("division by zero")
            return normalize(Fraction(int(self), int(other)))
        if isinstance(other, Fraction):
            return normalize(Fraction(int(self)) / other)
        return int.__truediv__(self, other)

    def __rtruediv__(self, other):
        """Return ``other / self``, exactly when ``other`` is an integer."""
        if isinstance(other, int):
            if self == 0:
                raise ZeroDivisionError("division by zero")
            return normalize(Fraction(int(other), int(self)))
        return int.__rtruediv__(self, other)

    def __pow__(self, other, modulo=None):
        """Return ``self ** other``; a negative exponent gives a Rational."""
        if modulo is None and isinstance(other, int) and other < 0:
            return normalize(Fraction(1, int(self) ** -int(other)))
        return normalize(int.__pow__(self, other, modulo))

    def __rpow__(self, other):
        """Return ``other ** self``; a negative exponent gives a Rational."""
        if isinstance(other, int) and self < 0:
            return normalize(Fraction(1, int(other) ** -int(self)))
        return normalize(int.__rpow__(self, other))

    __add__ = _int_binary(int.__add__)
    __radd__ = _int_binary(int.__radd__)
    __sub__ = _int_binary(int.__sub__)
    __rsub__ = _int_binary(int.__rsub__)
    __mul__ = _int_binary(int.__mul__)
    __rmul__ = _int_binary(int.__rmul__)
    __floordiv__ = _int_binary(int.__floordiv__)
    __rfloordiv__ = _int_binary(int.__rfloordiv__)
    __mod__ = _int_binary(int.__mod__)
    __rmod__ = _int_binary(int.__rmod__)
    __and__ = _int_binary(int.__and__)
    __rand__ = _int_binary(int.__rand__)
    __or__ = _int_binary(int.__or__)
    __ror__ = _int_binary(int.__ror__)
    __xor__ = _int_binary(int.__xor__)
    __rxor__ = _int_binary(int.__rxor__)
    __lshift__ = _int_binary(int.__lshift__)
    __rlshift__ = _int_binary(int.__rlshift__)
    __rshift__ = _int_binary(int.__rshift__)
    __rrshift__ = _int_binary(int.__rrshift__)
    __neg__ = _int_unary(int.__neg__)
    __pos__ = _int_unary(int.__pos__)
    __abs__ = _int_unary(int.__abs__)
    __invert__ = _int_unary(int.__invert__)
    # ``math.floor``, ``math.ceil``, ``math.trunc`` and ``round``.
    __floor__ = _int_unary(int.__floor__)
    __ceil__ = _int_unary(int.__ceil__)
    __trunc__ = _int_unary(int.__trunc__)
    __round__ = _int_unary(int.__round__)
    __divmod__ = _exact_pair(int.__divmod__)
    __rdivmod__ = _exact_pair(int.__rdivmod__)


# Rational arithmetic is the other hot path (benchmarks: ``a + b`` was
# about 3 times ``Fraction``'s).  ``+ - * /`` between rationals and
# integers run the same algorithms as ``fractions.Fraction`` (so the
# results are identical) and build the ER2 number directly, instead of
# making a ``Fraction`` and converting it.  Anything else (``float``,
# ``complex``, SymPy, ...) takes the generic route below.


def _parts(x):
    """Return ``(numerator, denominator)`` of an exact rational, or None."""
    if isinstance(x, Fraction):
        return x._numerator, x._denominator
    if isinstance(x, int) and not isinstance(x, bool):
        return int(x), 1
    return None


def _number(n, d):
    """Return ``n/d`` (lowest terms, ``d > 0``) as an ER2 number."""
    if d == 1:
        return Integer(n)
    return Rational._from_coprime_ints(n, d)


def _add_parts(na, da, nb, db):
    """``na/da + nb/db`` as Fraction._add computes it."""
    g = math.gcd(da, db)
    if g == 1:
        return _number(na * db + da * nb, da * db)
    s = da // g
    t = na * (db // g) + nb * s
    g2 = math.gcd(t, g)
    if g2 == 1:
        return _number(t, s * db)
    return _number(t // g2, s * (db // g2))


def _mul_parts(na, da, nb, db):
    """``na/da * nb/db`` as Fraction._mul computes it."""
    g1 = math.gcd(na, db)
    if g1 > 1:
        na //= g1
        db //= g1
    g2 = math.gcd(nb, da)
    if g2 > 1:
        nb //= g2
        da //= g2
    return _number(na * nb, db * da)


def _div_parts(na, da, nb, db):
    """``(na/da) / (nb/db)`` as Fraction._div computes it."""
    if nb == 0:
        raise ZeroDivisionError(f"Fraction({db}, 0)")
    g1 = math.gcd(na, nb)
    if g1 > 1:
        na //= g1
        nb //= g1
    g2 = math.gcd(db, da)
    if g2 > 1:
        da //= g2
        db //= g2
    n, d = na * db, nb * da
    if d < 0:
        n, d = -n, -d
    return _number(n, d)


def _fast(compute, fallback, reflected=False):
    """Operator with the exact fast path and ``fallback`` for the rest."""

    def method(self, other):
        b = _parts(other)
        if b is None:
            return fallback(self, other)
        a = (self._numerator, self._denominator)
        return compute(*b, *a) if reflected else compute(*a, *b)

    method.__name__ = fallback.__name__
    method.__doc__ = f"Exact version of ``{fallback.__name__}``."
    return method


def _sub_parts(na, da, nb, db):
    """``na/da - nb/db``."""
    return _add_parts(na, da, -nb, db)


class Rational(Fraction):
    """Exact rational number; integral results become ``Integer``."""

    __slots__ = ()

    def __repr__(self):
        """Return ``1/3`` instead of ``Rational(1, 3)``."""
        return str(self)

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()

    __add__ = _fast(_add_parts, _exact(Fraction.__add__))
    __radd__ = _fast(_add_parts, _exact(Fraction.__radd__), reflected=True)
    __sub__ = _fast(_sub_parts, _exact(Fraction.__sub__))
    __rsub__ = _fast(_sub_parts, _exact(Fraction.__rsub__), reflected=True)
    __mul__ = _fast(_mul_parts, _exact(Fraction.__mul__))
    __rmul__ = _fast(_mul_parts, _exact(Fraction.__rmul__), reflected=True)
    __truediv__ = _fast(_div_parts, _exact(Fraction.__truediv__))
    __rtruediv__ = _fast(
        _div_parts, _exact(Fraction.__rtruediv__), reflected=True
    )
    __floordiv__ = _exact(Fraction.__floordiv__)
    __rfloordiv__ = _exact(Fraction.__rfloordiv__)
    __mod__ = _exact(Fraction.__mod__)
    __rmod__ = _exact(Fraction.__rmod__)
    __pow__ = _exact(Fraction.__pow__)
    __rpow__ = _exact(Fraction.__rpow__)
    __neg__ = _exact(Fraction.__neg__)
    __pos__ = _exact(Fraction.__pos__)
    __abs__ = _exact(Fraction.__abs__)
    # ``math.floor``, ``math.ceil``, ``math.trunc`` and ``round``.
    __floor__ = _exact(Fraction.__floor__)
    __ceil__ = _exact(Fraction.__ceil__)
    __trunc__ = _exact(Fraction.__trunc__)
    __round__ = _exact(Fraction.__round__)
    __divmod__ = _exact_pair(Fraction.__divmod__)
    __rdivmod__ = _exact_pair(Fraction.__rdivmod__)


class _LiteralCache(dict):
    """Integer literals, created once: ``cache[5]`` is ``Integer(5)``.

    The preparser wraps every integer literal in a call, which runs on
    every evaluation.  ``Integer`` is immutable, so a literal can be shared,
    and a dict lookup costs half of creating a new ``Integer``.
    """

    __slots__ = ()

    def __missing__(self, value):
        """Create and remember the ``Integer`` for a new literal."""
        integer = self[value] = Integer(value)
        return integer


literal = _LiteralCache().__getitem__
