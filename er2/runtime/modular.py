r"""Integers modulo ``n``: ``Mod(3, 7)`` (ARCHITECTURE.md §3.6).

``Mod`` follows PARI's ``Mod``: operations between residues with different
moduli work modulo the gcd of the moduli, and a rational number becomes a
residue when its denominator is invertible.  It prints as ``Mod(3, 7)``
and its LaTeX is ``3 \pmod{7}``.
"""

import math
from fractions import Fraction

from er2.printing import latex
from er2.runtime.numbers import Integer


class Mod:
    """The residue class of ``value`` modulo ``modulus``."""

    __slots__ = ("_modulus", "_value")

    def __init__(self, value, modulus):
        """Create ``value mod modulus``; ``value`` may be a rational."""
        if isinstance(modulus, bool) or not isinstance(modulus, int):
            raise TypeError("the modulus must be an integer")
        if modulus == 0:
            raise ZeroDivisionError("the modulus must be nonzero")
        modulus = abs(int(modulus))
        if isinstance(value, Mod):
            modulus = math.gcd(modulus, value._modulus)
            value = value._value
        if isinstance(value, Fraction):
            value = value.numerator * _inverse(value.denominator, modulus)
        elif isinstance(value, int) and not isinstance(value, bool):
            value = int(value)
        else:
            raise TypeError(
                f"cannot reduce {type(value).__name__} modulo an integer"
            )
        self._modulus = Integer(modulus)
        self._value = Integer(value % modulus)

    @property
    def modulus(self):
        """The modulus ``n``."""
        return self._modulus

    def lift(self):
        """Return the representative in ``[0, modulus)`` as an Integer."""
        return self._value

    def __int__(self):
        """Return ``lift()`` as an ``int``."""
        return int(self._value)

    def __bool__(self):
        """Return whether the residue is nonzero."""
        return self._value != 0

    def __eq__(self, other):
        """Residues are equal when value and modulus are both equal."""
        if isinstance(other, Mod):
            return (self._value, self._modulus) == (
                other._value,
                other._modulus,
            )
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__``."""
        return hash((Mod, self._value, self._modulus))

    def __repr__(self):
        """Return ``Mod(3, 7)``, like PARI."""
        return f"Mod({self._value}, {self._modulus})"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer):
        return rf"{self._value} \pmod{{{self._modulus}}}"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()

    def _coerce(self, other):
        """Return ``(a, b, n)``: both operands modulo a common ``n``."""
        if isinstance(other, Mod):
            n = math.gcd(self._modulus, other._modulus)
            return int(self._value) % n, int(other._value) % n, n
        if isinstance(other, (int, Fraction)) and not isinstance(other, bool):
            n = int(self._modulus)
            return int(self._value), int(Mod(other, n)._value), n
        return None

    def __add__(self, other):
        """Return ``self + other``."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(a + b, n)

    __radd__ = __add__

    def __sub__(self, other):
        """Return ``self - other``."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(a - b, n)

    def __rsub__(self, other):
        """Return ``other - self``."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(b - a, n)

    def __mul__(self, other):
        """Return ``self * other``."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(a * b, n)

    __rmul__ = __mul__

    def __truediv__(self, other):
        """Return ``self / other``; ``other`` must be invertible."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(a * _inverse(b, n), n)

    def __rtruediv__(self, other):
        """Return ``other / self``; ``self`` must be invertible."""
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        return Mod(b * _inverse(a, n), n)

    def __pow__(self, exponent, modulo=None):
        """Return ``self ** exponent``; negative exponents invert."""
        if modulo is not None or isinstance(exponent, bool):
            return NotImplemented
        if not isinstance(exponent, int):
            return NotImplemented
        n = int(self._modulus)
        base = int(self._value)
        if exponent < 0:
            base = _inverse(base, n)
            exponent = -exponent
        return Mod(pow(base, int(exponent), n), n)

    def __neg__(self):
        """Return ``-self``."""
        return Mod(-self._value, self._modulus)

    def __pos__(self):
        """Return ``self``."""
        return self


def _inverse(a, n):
    """Return the inverse of ``a`` modulo ``n``."""
    try:
        return pow(int(a), -1, int(n))
    except ValueError:
        raise ZeroDivisionError(f"{a} is not invertible modulo {n}") from None
