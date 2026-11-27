r"""Binary quadratic forms: ``Qfb(a, b, c)`` is ``a*x^2 + b*x*y + c*y^2``.

``Qfb`` mirrors PARI's ``t_QFB``: ``*`` is Gauss composition and ``^``
repeated composition, both computed by PARI (ARCHITECTURE.md §3.7).  It
prints as ``Qfb(1, 1, 6)`` and its LaTeX is ``\left(1, 1, 6\right)``, the
usual notation for a form.
"""

from __future__ import annotations

from er2.printing import latex

TYPE_CHECKING = False
if TYPE_CHECKING:  # annotations only: ``typing`` costs startup
    from typing import Any


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


class Qfb:
    """The binary quadratic form ``a*x^2 + b*x*y + c*y^2``."""

    __slots__ = ("_a", "_b", "_c")

    def __init__(self, a: int, b: int, c: int) -> None:
        """Create the form with integer coefficients ``a, b, c``."""
        for value in (a, b, c):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("Qfb coefficients must be integers")
        self._a, self._b, self._c = int(a), int(b), int(c)

    @property
    def a(self) -> int:
        """The coefficient of ``x^2``."""
        return self._a

    @property
    def b(self) -> int:
        """The coefficient of ``x*y``."""
        return self._b

    @property
    def c(self) -> int:
        """The coefficient of ``y^2``."""
        return self._c

    def discriminant(self) -> int:
        """Return ``b^2 - 4*a*c``."""
        return self._b**2 - 4 * self._a * self._c

    def reduce(self) -> Qfb:
        """Return the reduced form equivalent to this one (PARI ``qfbred``)."""
        backend = _backend()
        return backend.from_pari(backend.PARI.qfbred(backend.to_pari(self)))

    def __call__(self, x: Any, y: Any) -> Any:
        """Evaluate the form at ``(x, y)``."""
        return self._a * x**2 + self._b * x * y + self._c * y**2

    def __mul__(self, other: object) -> Qfb:
        """Return the composition of two forms, reduced (PARI ``*``)."""
        if not isinstance(other, Qfb):
            return NotImplemented
        backend = _backend()
        return backend.from_pari(
            backend.to_pari(self) * backend.to_pari(other)
        )

    def __pow__(self, n: int, modulo: None = None) -> Qfb:
        """Return the ``n``-th power under composition (PARI ``^``)."""
        if modulo is not None or isinstance(n, bool):
            return NotImplemented
        if not isinstance(n, int):
            return NotImplemented
        backend = _backend()
        return backend.from_pari(backend.to_pari(self) ** int(n))

    def __eq__(self, other: object) -> bool:
        """Forms are equal when their coefficients are equal."""
        if isinstance(other, Qfb):
            return (self._a, self._b, self._c) == (
                other._a,
                other._b,
                other._c,
            )
        return NotImplemented

    def __hash__(self) -> int:
        """Hash consistently with ``__eq__``."""
        return hash((Qfb, self._a, self._b, self._c))

    def __repr__(self) -> str:
        """Return ``Qfb(1, 1, 6)``, like PARI."""
        return f"Qfb({self._a}, {self._b}, {self._c})"

    def _sympystr(self, printer: Any) -> str:
        return repr(self)

    def _latex(self, printer: Any) -> str:
        return rf"\left({self._a}, {self._b}, {self._c}\right)"

    def _repr_latex_(self) -> str:
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()
