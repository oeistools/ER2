"""Exact numbers: ``Integer`` and ``Rational`` (ARCHITECTURE.md §1.1, D6).

Every integer literal in ER2 source becomes an ``Integer``.  ``Integer``
is a real ``int`` subclass, so it keeps working wherever Python or a
library expects an ``int`` (``range``, indexing, ``json``, NumPy, ...).
The only difference is that ``/`` and negative powers are exact: they
return a ``Rational`` instead of a ``float``.
"""

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
            return Rational(value.numerator, value.denominator)
    return value


def _exact(op):
    """Wrap an ``int`` or ``Fraction`` operator so results stay ER2 numbers."""

    def method(self, *args):
        return normalize(op(self, *args))

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

    def method(self):
        return Integer(op(self))

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
    __rshift__ = _int_binary(int.__rshift__)
    __neg__ = _int_unary(int.__neg__)
    __pos__ = _int_unary(int.__pos__)
    __abs__ = _int_unary(int.__abs__)
    __invert__ = _int_unary(int.__invert__)

    def __divmod__(self, other):
        """Return ``(self // other, self % other)`` as ER2 numbers."""
        return tuple(map(normalize, int.__divmod__(self, other)))

    def __rdivmod__(self, other):
        """Return ``(other // self, other % self)`` as ER2 numbers."""
        return tuple(map(normalize, int.__rdivmod__(self, other)))


class Rational(Fraction):
    """Exact rational number; integral results become ``Integer``."""

    __slots__ = ()

    def __repr__(self):
        """Return ``1/3`` instead of ``Rational(1, 3)``."""
        return str(self)

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()

    __add__ = _exact(Fraction.__add__)
    __radd__ = _exact(Fraction.__radd__)
    __sub__ = _exact(Fraction.__sub__)
    __rsub__ = _exact(Fraction.__rsub__)
    __mul__ = _exact(Fraction.__mul__)
    __rmul__ = _exact(Fraction.__rmul__)
    __truediv__ = _exact(Fraction.__truediv__)
    __rtruediv__ = _exact(Fraction.__rtruediv__)
    __floordiv__ = _exact(Fraction.__floordiv__)
    __rfloordiv__ = _exact(Fraction.__rfloordiv__)
    __mod__ = _exact(Fraction.__mod__)
    __rmod__ = _exact(Fraction.__rmod__)
    __pow__ = _exact(Fraction.__pow__)
    __rpow__ = _exact(Fraction.__rpow__)
    __neg__ = _exact(Fraction.__neg__)
    __pos__ = _exact(Fraction.__pos__)
    __abs__ = _exact(Fraction.__abs__)


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
