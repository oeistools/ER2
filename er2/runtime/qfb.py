r"""Binary quadratic forms: ``Qfb(a, b, c)`` is ``a*x^2 + b*x*y + c*y^2``.

``Qfb`` mirrors PARI's ``t_QFB``: ``*`` is Gauss composition and ``^``
repeated composition, both computed by PARI (ARCHITECTURE.md §3.7).  It
prints as ``Qfb(1, 1, 6)`` and its LaTeX is ``\left(1, 1, 6\right)``, the
usual notation for a form.
"""

from er2.printing import latex
from er2.runtime.numbers import Integer


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


class Qfb:
    """The binary quadratic form ``a*x^2 + b*x*y + c*y^2``."""

    __slots__ = ("_a", "_b", "_c")

    def __init__(self, a, b, c):
        """Create the form with integer coefficients ``a, b, c``."""
        for value in (a, b, c):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("Qfb coefficients must be integers")
        self._a, self._b, self._c = Integer(a), Integer(b), Integer(c)

    @property
    def a(self):
        """The coefficient of ``x^2``."""
        return self._a

    @property
    def b(self):
        """The coefficient of ``x*y``."""
        return self._b

    @property
    def c(self):
        """The coefficient of ``y^2``."""
        return self._c

    def discriminant(self):
        """Return ``b^2 - 4*a*c``."""
        return self._b**2 - 4 * self._a * self._c

    def reduce(self):
        """Return the reduced form equivalent to this one (PARI ``qfbred``)."""
        backend = _backend()
        return backend.from_pari(backend.PARI.qfbred(backend.to_pari(self)))

    def __call__(self, x, y):
        """Evaluate the form at ``(x, y)``."""
        return self._a * x**2 + self._b * x * y + self._c * y**2

    def __mul__(self, other):
        """Return the composition of two forms, reduced (PARI ``*``)."""
        if not isinstance(other, Qfb):
            return NotImplemented
        backend = _backend()
        return backend.from_pari(
            backend.to_pari(self) * backend.to_pari(other)
        )

    def __pow__(self, n, modulo=None):
        """Return the ``n``-th power under composition (PARI ``^``)."""
        if modulo is not None or isinstance(n, bool):
            return NotImplemented
        if not isinstance(n, int):
            return NotImplemented
        backend = _backend()
        return backend.from_pari(backend.to_pari(self) ** int(n))

    def __eq__(self, other):
        """Forms are equal when their coefficients are equal."""
        if isinstance(other, Qfb):
            return (self._a, self._b, self._c) == (
                other._a,
                other._b,
                other._c,
            )
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__``."""
        return hash((Qfb, self._a, self._b, self._c))

    def __repr__(self):
        """Return ``Qfb(1, 1, 6)``, like PARI."""
        return f"Qfb({self._a}, {self._b}, {self._c})"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer):
        return rf"\left({self._a}, {self._b}, {self._c}\right)"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()
