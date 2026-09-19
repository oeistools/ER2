r"""Residue classes: ``Mod(3, 7)`` and ``Mod(x, x^2 + 1)``.

``Mod`` follows PARI's ``Mod`` (ARCHITECTURE.md §3.6, §3.7):

* With an integer modulus, arithmetic runs in pure Python.  Operations
  between residues with different moduli work modulo the gcd of the
  moduli, and a rational number becomes a residue when its denominator
  is invertible.
* With a polynomial modulus (a SymPy expression), ``Mod`` is PARI's
  ``t_POLMOD`` and PARI does the arithmetic.

It prints as ``Mod(3, 7)`` and its LaTeX is ``3 \pmod{7}``.
"""

import math
import operator
from fractions import Fraction

import sympy

from er2.printing import latex
from er2.runtime.numbers import Integer


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


def _is_symbolic(obj):
    return isinstance(obj, sympy.Basic) and not obj.is_Number


def _from_sympy_number(obj):
    """Turn a SymPy integer or rational into a Python one."""
    if isinstance(obj, sympy.Integer):
        return int(obj)
    if isinstance(obj, sympy.Rational):
        return Fraction(int(obj.p), int(obj.q))
    return obj


class Mod:
    """The residue class of ``value`` modulo ``modulus``."""

    __slots__ = ("_modulus", "_value")

    def __init__(self, value, modulus):
        """Create ``value mod modulus``.

        ``modulus`` is a nonzero integer or a polynomial; ``value`` may be
        a rational number, and a polynomial when the modulus is one.
        """
        modulus, value = _from_sympy_number(modulus), _from_sympy_number(value)
        if _is_symbolic(modulus):
            self._init_polynomial(value, modulus)
            return
        if isinstance(modulus, bool) or not isinstance(modulus, int):
            raise TypeError("the modulus must be an integer or a polynomial")
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

    def _init_polynomial(self, value, modulus):
        """Reduce ``value`` modulo the polynomial ``modulus`` with PARI."""
        backend = _backend()
        residue = backend.PARI.Mod(
            backend.to_pari(value), backend.to_pari(modulus)
        )
        self._value = backend.from_pari(backend.PARI.lift(residue))
        self._modulus = backend.from_pari(residue.mod())

    @property
    def modulus(self):
        """The modulus: an integer, or a polynomial."""
        return self._modulus

    @property
    def is_polynomial(self):
        """Whether the modulus is a polynomial (PARI's ``t_POLMOD``)."""
        return _is_symbolic(self._modulus)

    def lift(self):
        """Return the representative: in ``[0, n)``, or of lower degree."""
        return self._value

    def __int__(self):
        """Return ``lift()`` as an ``int`` (integer moduli only)."""
        if self.is_polynomial:
            raise TypeError("a polynomial residue is not an integer")
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
        value, modulus = map(printer._print, (self._value, self._modulus))
        return f"Mod({value}, {modulus})"

    def _latex(self, printer):
        value = printer._print(self._value)
        return rf"{value} \pmod{{{printer._print(self._modulus)}}}"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()

    def _uses_pari(self, other):
        """Whether ``self`` and ``other`` combine as PARI polynomials."""
        if isinstance(other, Mod):
            return self.is_polynomial or other.is_polynomial
        return self.is_polynomial or _is_symbolic(other)

    def _coerce(self, other):
        """Return ``(a, b, n)``: both operands modulo a common ``n``."""
        if isinstance(other, Mod):
            n = math.gcd(self._modulus, other._modulus)
            return int(self._value) % n, int(other._value) % n, n
        if isinstance(other, (int, Fraction)) and not isinstance(other, bool):
            n = int(self._modulus)
            return int(self._value), int(Mod(other, n)._value), n
        return None

    def _via_pari(self, op, left, right):
        """Compute ``op(left, right)`` with PARI; ``None`` if impossible."""
        backend = _backend()
        try:
            left, right = backend.to_pari(left), backend.to_pari(right)
        except TypeError:
            return None
        return backend.from_pari(op(left, right))

    def _binary(self, other, op, integer_op, reflected=False):
        if self._uses_pari(other):
            args = (other, self) if reflected else (self, other)
            result = self._via_pari(op, *args)
            return NotImplemented if result is None else result
        operands = self._coerce(other)
        if operands is None:
            return NotImplemented
        a, b, n = operands
        if reflected:
            a, b = b, a
        return Mod(integer_op(a, b, n), n)

    def __add__(self, other):
        """Return ``self + other``."""
        return self._binary(other, operator.add, lambda a, b, n: a + b)

    def __radd__(self, other):
        """Return ``other + self``."""
        return self._binary(other, operator.add, lambda a, b, n: a + b, True)

    def __sub__(self, other):
        """Return ``self - other``."""
        return self._binary(other, operator.sub, lambda a, b, n: a - b)

    def __rsub__(self, other):
        """Return ``other - self``."""
        return self._binary(other, operator.sub, lambda a, b, n: a - b, True)

    def __mul__(self, other):
        """Return ``self * other``."""
        return self._binary(other, operator.mul, lambda a, b, n: a * b)

    def __rmul__(self, other):
        """Return ``other * self``."""
        return self._binary(other, operator.mul, lambda a, b, n: a * b, True)

    def __truediv__(self, other):
        """Return ``self / other``; ``other`` must be invertible."""
        return self._binary(
            other, operator.truediv, lambda a, b, n: a * _inverse(b, n)
        )

    def __rtruediv__(self, other):
        """Return ``other / self``; ``self`` must be invertible."""
        return self._binary(
            other,
            operator.truediv,
            lambda a, b, n: a * _inverse(b, n),
            True,
        )

    def __pow__(self, exponent, modulo=None):
        """Return ``self ** exponent``; negative exponents invert."""
        if modulo is not None or isinstance(exponent, bool):
            return NotImplemented
        if not isinstance(exponent, int):
            return NotImplemented
        if self.is_polynomial:
            return self._via_pari(operator.pow, self, int(exponent))
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
