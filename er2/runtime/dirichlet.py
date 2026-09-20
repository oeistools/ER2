r"""Dirichlet series: ``sum_{n>=1} a_n n^{-s}``, truncated (M6, D19).

PARI passes a Dirichlet series as a bare vector of coefficients.  ER2
wraps it in a type (D19) for three reasons a list cannot meet: §3.6
makes ``latex()`` a hard requirement for every mathematical type, a list
does not say what it is, and its indexing is off by one — ``a[5]`` would
be the sixth coefficient, where the mathematics writes ``a_5``.

``*`` and ``/`` are PARI's ``dirmul`` and ``dirdiv``; ``+`` and ``-``
are coefficientwise.  The coefficients are stored as plain ER2 numbers,
so no PARI object outlives the call that made it (M4).
"""

from er2.printing import latex

__all__ = ["DirichletSeries"]

# How many terms ``repr`` and ``latex`` show before the ellipsis.
_SHOWN = 5


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


class DirichletSeries:
    r"""A truncated Dirichlet series ``a_1 + a_2 2^{-s} + ... + a_N N^{-s}``.

    ``DirichletSeries([1] * 20)`` is the Riemann zeta function to 20
    terms.  Indexing follows the mathematics and starts at 1, so
    ``z[6]`` is ``a_6``.
    """

    __slots__ = ("_coefficients",)

    def __init__(self, coefficients):
        """Create the series with coefficients ``a_1, a_2, ...``."""
        backend = _backend()
        values = tuple(backend.from_pari(c) for c in coefficients)
        if not values:
            raise ValueError("a Dirichlet series needs at least a_1")
        self._coefficients = values

    @classmethod
    def euler(cls, factor, terms):
        r"""Build a series from its Euler product (PARI ``direuler``).

        ``factor(p, x)`` returns the local factor at the prime ``p`` as
        a rational function of ``x``, which stands for ``p^{-s}``.  The
        zeta function is ``1/(1 - x)`` and its inverse is ``1 - x``::

            DirichletSeries.euler(lambda p, x: 1/(1 - x), 20)

        PARI writes that variable ``X``; ER2 documents it lowercase
        because the caller names it, and PEP 8 is a hard requirement
        for ER2 code too (§6.1).

        ``terms`` is how many coefficients to compute.
        """
        backend = _backend()
        return cls(backend.euler_product_series(factor, terms))

    @classmethod
    def zeta(cls, terms):
        """Return the Riemann zeta function: every coefficient 1.

        A classmethod rather than a prelude name, so the two series a
        user reaches for first are discoverable from the type without
        spending §1.4's budget on top-level names.
        """
        return cls([1] * terms)

    @classmethod
    def moebius(cls, terms):
        """Return ``1/zeta(s)``, whose coefficients are ``mu(n)``."""
        return cls.euler(lambda p, local: 1 - local, terms)

    @property
    def coefficients(self):
        """The coefficients ``a_1, ..., a_N`` as a tuple."""
        return self._coefficients

    @property
    def terms(self):
        """How many coefficients the series carries."""
        return len(self._coefficients)

    def __getitem__(self, n):
        """Return ``a_n``.  Indexed from 1, as the mathematics is."""
        if isinstance(n, slice):
            raise TypeError("a Dirichlet series does not support slicing")
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("a Dirichlet series is indexed by an integer")
        if not 1 <= n <= len(self._coefficients):
            raise IndexError(
                f"a_{n} is outside the {len(self._coefficients)} terms "
                "this series carries"
            )
        return self._coefficients[n - 1]

    def __len__(self):
        """Return the number of terms, which is the truncation."""
        return len(self._coefficients)

    def __iter__(self):
        """Iterate over ``a_1, a_2, ...``."""
        return iter(self._coefficients)

    def _pari(self):
        """Return this series as a PARI vector, for ``dirmul``."""
        backend = _backend()
        return backend.to_pari(list(self._coefficients))

    def _combine(self, other, operation):
        """Apply a PARI Dirichlet operation, truncating to the shorter."""
        if not isinstance(other, DirichletSeries):
            return NotImplemented
        backend = _backend()
        terms = min(len(self), len(other))
        result = operation(backend.PARI, self._pari(), other._pari())
        return DirichletSeries(list(result)[:terms])

    def __mul__(self, other):
        """Dirichlet convolution (PARI ``dirmul``)."""
        return self._combine(other, lambda pari, a, b: pari.dirmul(a, b))

    def __truediv__(self, other):
        """Dirichlet division (PARI ``dirdiv``); ``a_1`` must be non-zero."""
        return self._combine(other, lambda pari, a, b: pari.dirdiv(a, b))

    def _pointwise(self, other, operation):
        """Add or subtract coefficientwise, truncating to the shorter."""
        if not isinstance(other, DirichletSeries):
            return NotImplemented
        terms = min(len(self), len(other))
        return DirichletSeries(
            [
                operation(self._coefficients[i], other._coefficients[i])
                for i in range(terms)
            ]
        )

    def __add__(self, other):
        """Add coefficientwise."""
        return self._pointwise(other, lambda a, b: a + b)

    def __sub__(self, other):
        """Subtract coefficientwise."""
        return self._pointwise(other, lambda a, b: a - b)

    def __eq__(self, other):
        """Two series are equal when their coefficients are."""
        if isinstance(other, DirichletSeries):
            return self._coefficients == other._coefficients
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__``."""
        return hash((DirichletSeries, self._coefficients))

    def _parts(self):
        """Return the leading ``(index, coefficient)``, zeros dropped."""
        shown = [
            (n, a)
            for n, a in enumerate(self._coefficients[:_SHOWN], start=1)
            if a != 0
        ]
        # "..." only when something non-zero is actually left out: a
        # product that collapses to 1 must not print "1 + ...".
        more = any(a != 0 for a in self._coefficients[_SHOWN:])
        return shown, more

    def __repr__(self):
        """Return ``1 - 2^-s - 3^-s + ...  (20 terms)``."""
        body = _join(*self._parts(), "^-s", tex=False)
        return f"{body}  ({len(self)} terms)"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer=None):
        return _join(*self._parts(), "^{-s}", tex=True)

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()


def _join(shown, more, exponent, tex):
    """Join terms with real signs, so ``1 + -2^-s`` never appears."""
    if not shown:
        return r"\cdots" if more and tex else ("..." if more else "0")
    pieces = [_term(shown[0][0], shown[0][1], exponent, tex)]
    for n, a in shown[1:]:
        sign = " - " if a < 0 else " + "
        pieces.append(sign + _term(n, abs(a), exponent, tex))
    if more:
        pieces.append(r" + \cdots" if tex else " + ...")
    return "".join(pieces)


def _term(n, a, exponent, tex=False):
    """Format ``a_n n^{-s}``, leaving out what is understood.

    ``_join`` passes the absolute value for every term but the first,
    having put the sign in the separator, so ``a == -1`` here means a
    leading negative term.
    """
    if n == 1:
        return _coefficient(a, tex)
    power = f"{n}{exponent}"
    if a == 1:
        return power
    if a == -1:
        return f"-{power}"
    separator = r" \cdot " if tex else "*"
    return f"{_coefficient(a, tex)}{separator}{power}"


def _coefficient(a, tex):
    """Render a coefficient, as LaTeX when asked.

    ``Tex`` is a ``str`` subclass, so ``str()`` of it is the body
    without the ``$`` delimiters.
    """
    return str(latex(a)) if tex else str(a)
