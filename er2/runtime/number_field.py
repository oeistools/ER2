r"""Number fields: ``NumberField(x^2 + 5)`` (ARCHITECTURE.md §6, D14).

A number field is ``Q[x]/(f)`` for an irreducible ``f``.  Its elements
are ``Mod`` objects with a polynomial modulus (PARI's ``t_POLMOD``), so
``K.gen()`` is ``Mod(x, x^2 + 5)`` and arithmetic already works.

PARI computes everything.  ``nfinit`` runs on each call that needs it,
which is cheap; ``bnfinit``, which can take minutes, runs at most once
per field and its results are cached as plain Python data.  No PARI
structure is kept alive between calls (M4), so ``pari.set_stack`` can
never invalidate a field.

Class groups and units assume the GRH unless ``certify=True`` asks PARI
to prove them (``bnfcertify``), which is much slower.  ``bnfinit`` is
randomised, so a fundamental unit comes back as one of several
equivalent representatives, never a canonical one.
"""

from er2.printing import latex
from er2.runtime.numbers import Integer

__all__ = ["NumberField", "PrimeIdeal"]


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


def _sympy():
    from er2 import _lazy

    return _lazy.sympy()


class NumberField:
    """The number field ``Q[x]/(f)`` for a monic irreducible ``f``."""

    __slots__ = ("_basis", "_bnf", "_degree", "_discriminant", "_polynomial")

    def __init__(self, polynomial):
        """Create the field defined by ``polynomial``.

        ``polynomial`` must be monic, with integer coefficients, and
        irreducible over Q.  PARI presents a non-monic polynomial by a
        different one, which would no longer match the field's own
        elements, so ER2 asks for the monic form instead of changing it
        silently.
        """
        self._polynomial = _validate(polynomial)
        degree, discriminant, basis = _backend().number_field(self._polynomial)
        self._degree = degree
        self._discriminant = discriminant
        self._basis = tuple(basis)
        self._bnf = None

    @property
    def polynomial(self):
        """The defining polynomial."""
        return self._polynomial

    @property
    def degree(self):
        """The degree over Q."""
        return self._degree

    @property
    def discriminant(self):
        """The discriminant of the field (not of the polynomial)."""
        return self._discriminant

    @property
    def variable(self):
        """The symbol the defining polynomial is written in."""
        (symbol,) = self._polynomial.free_symbols
        return symbol

    def integral_basis(self):
        """Return a Z-basis of the ring of integers, as field elements."""
        return list(self._basis)

    def gen(self):
        """Return a root of the defining polynomial: ``Mod(x, f)``."""
        return self(self.variable)

    def __call__(self, value):
        """Return ``value`` as an element of the field."""
        from er2.runtime.modular import Mod

        return Mod(value, self._polynomial)

    def _class_group_data(self, certify):
        """Return the cached ``bnfinit`` results, computing them once.

        A field asked to certify after an uncertified run recomputes:
        the proof needs the structure that was already thrown away.
        """
        if self._bnf is None or (certify and not self._bnf[-1]):
            data = _backend().number_field_class_group(
                self._polynomial, certify=certify
            )
            self._bnf = (*data, bool(certify))
        return self._bnf

    def class_number(self, certify=False):
        """Return the class number ``h`` of the field."""
        return self._class_group_data(certify)[0]

    def class_group(self, certify=False):
        """Return the class group's invariant factors.

        ``[2]`` means ``Z/2Z``, and ``[]`` means the group is trivial,
        so the field has unique factorization.
        """
        return list(self._class_group_data(certify)[1])

    def units(self, certify=False):
        """Return a system of fundamental units, as field elements.

        The list is empty when the unit group is finite, as it is for
        an imaginary quadratic field.  ``roots_of_unity`` counts the
        torsion part, which is what the units miss.

        A fundamental unit is defined only up to sign and inversion, and
        PARI's ``bnfinit`` is randomised, so two calls may return
        different (equivalent) representatives: do not depend on which
        one comes back.
        """
        return list(self._class_group_data(certify)[2])

    def roots_of_unity(self, certify=False):
        """Return how many roots of unity the field contains."""
        return self._class_group_data(certify)[3]

    def factor(self, p):
        """Factor the rational prime ``p`` into prime ideals.

        Returns ``(ideal, exponent)`` pairs: in ``Q(sqrt(-5))`` the
        prime 2 gives one ideal with exponent 2, and 3 gives two.
        """
        if isinstance(p, bool) or not isinstance(p, int):
            raise TypeError("factor() needs a rational prime")
        backend = _backend()
        if not backend.is_prime_number(int(p)):
            raise ValueError(f"{p} is not prime")
        return [
            (PrimeIdeal(self, rational, e, f, alpha), e)
            for rational, e, f, alpha in backend.prime_ideals(
                self._polynomial, p
            )
        ]

    def __eq__(self, other):
        """Two fields are equal when their polynomials are."""
        if not isinstance(other, NumberField):
            return NotImplemented
        return self._polynomial == other._polynomial

    def __hash__(self):
        """Hash the field by its polynomial."""
        return hash((NumberField, self._polynomial))

    def __repr__(self):
        """Return ``NumberField(x^2 + 5)``."""
        return f"NumberField({self._polynomial})"

    def _sympystr(self, printer):
        return f"NumberField({printer._print(self._polynomial)})"

    def _latex(self, printer):
        body = printer._print(self._polynomial)
        return (
            rf"\mathbb{{Q}}[{printer._print(self.variable)}]/"
            rf"\left({body}\right)"
        )

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()


class PrimeIdeal:
    """A prime ideal ``(p, alpha)`` of a number field's ring of integers."""

    __slots__ = ("_alpha", "_e", "_f", "_field", "_p")

    def __init__(self, field, p, e, f, alpha):
        """Create the ideal above ``p`` with the given invariants."""
        self._field = field
        self._p = Integer(p)
        self._e = Integer(e)
        self._f = Integer(f)
        self._alpha = alpha

    @property
    def field(self):
        """The number field this ideal belongs to."""
        return self._field

    @property
    def p(self):
        """The rational prime below this ideal."""
        return self._p

    @property
    def ramification_index(self):
        """The exponent ``e`` of this ideal in the factorization of ``p``."""
        return self._e

    @property
    def residue_degree(self):
        """The degree ``f`` of the residue field over ``F_p``."""
        return self._f

    @property
    def alpha(self):
        """The second generator: the ideal is ``(p, alpha)``."""
        return self._alpha

    def norm(self):
        """Return the norm of the ideal, ``p^f``."""
        return self._p**self._f

    def is_inert(self):
        """Whether ``p`` stays prime: ``e = 1`` and ``f`` is the degree."""
        return self._e == 1 and self._f == self._field.degree

    def is_ramified(self):
        """Whether ``e > 1``."""
        return self._e > 1

    def __eq__(self, other):
        """Two ideals are equal when field, p, e, f and alpha all are.

        ``alpha`` is not decoration: the primes above a split prime
        share ``p``, ``e`` and ``f``, and only their generators tell
        them apart.  In ``Q(sqrt(-5))`` the two primes above 3 are
        ``(3, x - 1)`` and ``(3, x + 1)``.
        """
        if not isinstance(other, PrimeIdeal):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self):
        """Hash the ideal by everything ``__eq__`` compares."""
        return hash((PrimeIdeal, *self._key()))

    def _key(self):
        return (self._field, self._p, self._e, self._f, self._alpha)

    def __repr__(self):
        """Return the two-element form, ``(2, x + 1)``."""
        return f"({self._p}, {self._alpha.lift()})"

    def _sympystr(self, printer):
        parts = printer._print(self._p), printer._print(self._alpha.lift())
        return f"({parts[0]}, {parts[1]})"

    def _latex(self, printer):
        p = printer._print(self._p)
        alpha = printer._print(self._alpha.lift())
        return rf"\left({p},\ {alpha}\right)"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()


def _validate(polynomial):
    """Return ``polynomial`` if it defines a number field, else raise."""
    sympy = _sympy()
    backend = _backend()
    if not isinstance(polynomial, sympy.Expr):
        raise TypeError("NumberField() needs a polynomial over Q")
    symbols = polynomial.free_symbols
    if len(symbols) != 1:
        raise TypeError("NumberField() needs a polynomial in one variable")
    (variable,) = symbols
    if not polynomial.is_polynomial(variable):
        raise TypeError("NumberField() needs a polynomial")
    poly = sympy.Poly(polynomial, variable)
    if poly.degree() < 1:
        raise ValueError("NumberField() needs a polynomial of degree >= 1")
    if poly.domain != sympy.ZZ or poly.LC() != 1:
        raise ValueError(
            "NumberField() needs a monic polynomial over Z; "
            f"{polynomial} is not one"
        )
    if not backend.isirreducible(polynomial):
        raise ValueError(f"{polynomial} is not irreducible over Q")
    return polynomial
