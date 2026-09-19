r"""Factorizations of numbers: ``2^3 * 3^2`` (ARCHITECTURE.md §3.4).

``factor(n)`` on an integer or a rational returns a ``Factorization``.  It
is a sequence of ``(prime, exponent)`` pairs, like PARI's two-column
matrix, with the sign kept apart as ``unit``.  It prints as ``2^3 * 3^2``
and its LaTeX is ``2^{3} \cdot 3^{2}``.

A partial factorization (``factor(n, limit=B)``, D7) may contain factors
that are not prime; they are listed in ``unfactored``.
"""

from collections.abc import Sequence

from er2.printing import latex
from er2.runtime.numbers import Integer, normalize


class Factorization(Sequence):
    """A product ``unit * p1^e1 * p2^e2 * ...`` of prime powers."""

    __slots__ = ("_factors", "_unfactored", "_unit")

    def __init__(self, factors, unit=1, unfactored=()):
        """Create a factorization from ``(prime, exponent)`` pairs."""
        self._factors = tuple((Integer(p), Integer(e)) for p, e in factors)
        self._unit = Integer(unit)
        self._unfactored = tuple(Integer(n) for n in unfactored)

    @property
    def unit(self):
        """The sign of the number: ``1`` or ``-1``."""
        return self._unit

    @property
    def unfactored(self):
        """Factors not known to be prime (partial factorizations only)."""
        return self._unfactored

    @property
    def is_complete(self):
        """Whether every factor is prime."""
        return not self._unfactored

    def value(self):
        """Return the number this factorization represents."""
        result = self._unit
        for p, e in self._factors:
            result = result * p**e
        return normalize(result)

    def __getitem__(self, index):
        """Return the ``(prime, exponent)`` pair at ``index``."""
        return self._factors[index]

    def __len__(self):
        """Return the number of distinct factors."""
        return len(self._factors)

    def __eq__(self, other):
        """Compare the factors and the unit."""
        if isinstance(other, Factorization):
            return (self._unit, self._factors) == (
                other._unit,
                other._factors,
            )
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__``."""
        return hash((Factorization, self._unit, self._factors))

    def _terms(self, power, sign):
        terms = [power(p, e) for p, e in self._factors]
        if self._unit == -1:
            terms.insert(0, sign)
        return terms

    def __repr__(self):
        """Return ``2^3 * 3^2``."""

        def power(p, e):
            return str(p) if e == 1 else f"{p}^{e}"

        return " * ".join(self._terms(power, "-1")) or "1"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer):
        def power(p, e):
            return str(p) if e == 1 else f"{p}^{{{e}}}"

        return r" \cdot ".join(self._terms(power, "-1")) or "1"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()
