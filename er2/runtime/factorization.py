r"""Factorizations of numbers: ``2^3 * 3^2`` (ARCHITECTURE.md §3.4).

``factor(n)`` on an integer or a rational returns a ``Factorization``.  It
is a sequence of ``(prime, exponent)`` pairs, like PARI's two-column
matrix, with the sign kept apart as ``unit``.  It prints as ``2^3 * 3^2``
and its LaTeX is ``2^{3} \cdot 3^{2}``.

A partial factorization (``factor(n, limit=B)``, D7) may contain factors
that are not prime; they are listed in ``unfactored``.
"""

from __future__ import annotations

from collections.abc import Sequence

from er2.printing import latex
from er2.runtime.numbers import exact_pow, normalize

TYPE_CHECKING = False
if TYPE_CHECKING:  # annotations only: ``typing`` costs startup
    from collections.abc import Iterable
    from typing import Any

    from er2.runtime.numbers import Rational


class Factorization(Sequence):
    """A product ``unit * p1^e1 * p2^e2 * ...`` of prime powers."""

    __slots__ = ("_factors", "_unfactored", "_unit")

    def __init__(
        self,
        factors: Iterable[tuple[int, int]],
        unit: int = 1,
        unfactored: Iterable[int] = (),
    ) -> None:
        """Create a factorization from ``(prime, exponent)`` pairs."""
        self._factors = tuple((int(p), int(e)) for p, e in factors)
        self._unit = int(unit)
        self._unfactored = tuple(int(n) for n in unfactored)

    @property
    def unit(self) -> int:
        """The sign of the number: ``1`` or ``-1``."""
        return self._unit

    @property
    def unfactored(self) -> tuple[int, ...]:
        """Factors not known to be prime (partial factorizations only)."""
        return self._unfactored

    @property
    def is_complete(self) -> bool:
        """Whether every factor is prime."""
        return not self._unfactored

    def value(self) -> int | Rational:
        """Return the number this factorization represents."""
        result = self._unit
        for p, e in self._factors:
            # exact: a rational has negative exponents
            result = result * exact_pow(p, e)
        return normalize(result)

    def __getitem__(self, index: Any) -> Any:
        """Return the ``(prime, exponent)`` pair at ``index``."""
        return self._factors[index]

    def __len__(self) -> int:
        """Return the number of distinct factors."""
        return len(self._factors)

    def __eq__(self, other: object) -> bool:
        """Compare the factors and the unit."""
        if isinstance(other, Factorization):
            return (self._unit, self._factors) == (
                other._unit,
                other._factors,
            )
        return NotImplemented

    def __hash__(self) -> int:
        """Hash consistently with ``__eq__``."""
        return hash((Factorization, self._unit, self._factors))

    def _terms(self, power, sign):
        terms = [power(p, e) for p, e in self._factors]
        if self._unit == -1:
            terms.insert(0, sign)
        return terms

    def __repr__(self) -> str:
        """Return ``2^3 * 3^2``."""

        def power(p, e):
            return str(p) if e == 1 else f"{p}^{e}"

        return " * ".join(self._terms(power, "-1")) or "1"

    def _sympystr(self, printer: Any) -> str:
        return repr(self)

    def _latex(self, printer: Any) -> str:
        def power(p, e):
            return str(p) if e == 1 else f"{p}^{{{e}}}"

        return r" \cdot ".join(self._terms(power, "-1")) or "1"

    def _repr_latex_(self) -> str:
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()
