r"""Finite fields: ``GF(9)`` and its elements (ARCHITECTURE.md §6, D13).

``GF(q)`` (or ``GF(p, k)``) is the field with ``q = p^k`` elements.  Its
defining polynomial is PARI's ``ffinit``, and PARI does the arithmetic
(``t_FFELT``).  An element prints as a polynomial in the generator,
``a^2 + 2*a + 1`` (LaTeX ``a^{2} + 2 a + 1``); the generator is named
``a`` unless another name is given, ``GF(9, "t")``.

Elements are stored as their coefficients, not as PARI objects, so they
never outlive PARI's stack.  Integers, rationals and ``Mod(n, p)`` enter
the field when they meet an element of it, and ``F(3) == 3`` is true, as
in PARI and SageMath.
"""

import itertools
from fractions import Fraction

from er2.printing import latex
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer

__all__ = ["GF", "FiniteField", "FiniteFieldElement"]


def _backend():
    """Return the PARI backend (imported lazily: it imports this module)."""
    from er2.backends import pari_backend

    return pari_backend


def GF(order, degree=None, name="a"):  # noqa: N802 (the usual notation)
    """Return the finite field with ``order`` elements.

    ``GF(9)`` and ``GF(3, 2)`` are the same field; ``GF(9, "t")`` names
    the generator ``t`` (default ``a``).
    """
    if isinstance(degree, str):
        degree, name = None, degree
    if isinstance(order, bool) or not isinstance(order, int):
        raise TypeError("the order of a finite field must be an integer")
    backend = _backend()
    if degree is None:
        p, k = backend.prime_power(order)
    else:
        p, k = int(order), int(degree)
        if k < 1 or backend.prime_power(p) != (p, 1):
            raise ValueError("GF(p, k) needs a prime p and a degree k >= 1")
    if not name.isidentifier():
        raise ValueError(f"not a valid generator name: {name!r}")
    return FiniteField(p, k, name, backend.ff_modulus(p, k, name))


class FiniteField:
    """The finite field with ``p^k`` elements; ``GF`` creates it."""

    __slots__ = ("_degree", "_modulus", "_name", "_p", "_primitive")

    def __init__(self, p, k, name, modulus):
        """Create the field from its defining polynomial's coefficients.

        ``modulus`` lists the coefficients of a monic irreducible
        polynomial of degree ``k`` over ``F_p``, constant term first.
        """
        self._p, self._degree, self._name = Integer(p), Integer(k), name
        self._modulus = tuple(Integer(c) for c in modulus)
        self._primitive = None

    @property
    def characteristic(self):
        """The prime ``p``."""
        return self._p

    @property
    def degree(self):
        """The degree ``k`` over the prime field."""
        return self._degree

    @property
    def order(self):
        """The number of elements, ``p^k``."""
        return self._p**self._degree

    @property
    def name(self):
        """The name of the generator."""
        return self._name

    def modulus_coefficients(self):
        """Return the defining polynomial's coefficients, constant first."""
        return list(self._modulus)

    def modulus(self):
        """Return the defining polynomial, in the generator's name."""
        from er2 import _lazy

        sympy = _lazy.sympy()
        var = sympy.Symbol(self._name)
        return sympy.Add(*(c * var**i for i, c in enumerate(self._modulus)))

    def gen(self):
        """Return the generator: a root of ``modulus()`` (1 if ``k = 1``)."""
        if self._degree == 1:
            return self(1)
        return FiniteFieldElement(self, (0, 1))

    def primitive_element(self):
        """Return a generator of the multiplicative group.

        It is the first one in the order of ``elements()``, so it is the
        same in every run (PARI's ``ffprimroot`` is random).  Finding it
        factors ``q - 1``, which can take long for huge fields (D7).
        """
        if self._primitive is None:
            target = self.order - 1
            for element in itertools.islice(self.elements(), 1, None):
                if element.order() == target:
                    self._primitive = element
                    break
        return self._primitive

    def elements(self):
        """Iterate over the elements, as the integers ``0, ..., q - 1``.

        The element with coefficients ``c_0, c_1, ...`` comes at position
        ``c_0 + c_1 p + c_2 p^2 + ...``.
        """
        for n in range(self.order):
            coefficients = []
            for _ in range(self._degree):
                n, c = divmod(n, int(self._p))
                coefficients.append(c)
            yield FiniteFieldElement(self, coefficients)

    def __iter__(self):
        """Iterate over the elements (see ``elements``)."""
        return self.elements()

    def __call__(self, value):
        """Return ``value`` as an element of this field."""
        element = self._coerce(value)
        if element is None:
            raise TypeError(
                f"cannot convert {type(value).__name__} to an element of "
                f"{self!r}"
            )
        return element

    def _coerce(self, value):
        """Return ``value`` in this field, or ``None`` if it cannot be."""
        p = int(self._p)
        if isinstance(value, FiniteFieldElement):
            return value if value.parent == self else None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return FiniteFieldElement(self, (int(value) % p,))
        if isinstance(value, Fraction):
            if value.denominator % p == 0:
                raise ZeroDivisionError(
                    f"{value} has no value in {self!r}: {p} divides "
                    "its denominator"
                )
            inverse = pow(value.denominator, -1, p)
            return FiniteFieldElement(self, (value.numerator * inverse % p,))
        if isinstance(value, Mod) and not value.is_polynomial:
            if value.modulus != p:
                return None
            return FiniteFieldElement(self, (int(value.lift()),))
        return None

    def __contains__(self, value):
        """Whether ``value`` is an element of this field."""
        return isinstance(value, FiniteFieldElement) and value.parent == self

    def __eq__(self, other):
        """Fields are equal when they have the same defining polynomial."""
        if isinstance(other, FiniteField):
            return self._key() == other._key()
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__``."""
        return hash((FiniteField, *self._key()))

    def _key(self):
        return self._p, self._modulus, self._name

    def __repr__(self):
        """Return ``GF(9)``, or ``GF(9, "t")`` for another generator name."""
        if self._name == "a":
            return f"GF({self.order})"
        return f'GF({self.order}, "{self._name}")'

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer):
        return rf"\mathbb{{F}}_{{{self.order}}}"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()


class FiniteFieldElement:
    """An element of a finite field, as a polynomial in the generator."""

    __slots__ = ("_coefficients", "_field")

    def __init__(self, field, coefficients):
        """Create the element ``sum(c_i * a^i)`` of ``field``.

        ``coefficients`` are integers, constant term first; they are
        reduced modulo ``p`` and padded to the field's degree.
        """
        p, k = int(field.characteristic), int(field.degree)
        values = [int(c) % p for c in coefficients]
        if len(values) > k:
            raise ValueError(f"an element of {field!r} has {k} coefficients")
        values += [0] * (k - len(values))
        self._field = field
        self._coefficients = tuple(Integer(c) for c in values)

    @property
    def parent(self):
        """The field this element belongs to."""
        return self._field

    def coefficients(self):
        """Return the coefficients in the generator, constant term first."""
        return list(self._coefficients)

    def _pari(self):
        return _backend().ff_element(self)

    def _from_pari(self, gen):
        return FiniteFieldElement(self._field, _backend().ff_coefficients(gen))

    def _pari_call(self, function, *args):
        """Call a PARI function on this element; map PARI's errors."""
        backend = _backend()
        try:
            return function(self._pari(), *args)
        except backend.PariError as exc:
            raise ValueError(str(exc)) from None

    # Arithmetic.  ``+`` and ``-`` work on the coefficients; ``*``, ``/``
    # and ``^`` use PARI.

    def _other(self, other):
        """Return ``other`` in this field, or ``None``."""
        return self._field._coerce(other)

    def _linear(self, other, sign, reflected=False):
        other = self._other(other)
        if other is None:
            return NotImplemented
        a, b = self._coefficients, other._coefficients
        if reflected:
            a, b = b, a
        return FiniteFieldElement(
            self._field, [x + sign * y for x, y in zip(a, b, strict=True)]
        )

    def _product(self, other, divide=False, reflected=False):
        other = self._other(other)
        if other is None:
            return NotImplemented
        a, b = self._pari(), other._pari()
        if reflected:
            a, b = b, a
        if not divide:
            return self._from_pari(a * b)
        if not (other if not reflected else self):
            raise ZeroDivisionError(f"division by zero in {self._field!r}")
        return self._from_pari(a / b)

    def __add__(self, other):
        """Return ``self + other``."""
        return self._linear(other, 1)

    def __radd__(self, other):
        """Return ``other + self``."""
        return self._linear(other, 1, True)

    def __sub__(self, other):
        """Return ``self - other``."""
        return self._linear(other, -1)

    def __rsub__(self, other):
        """Return ``other - self``."""
        return self._linear(other, -1, True)

    def __mul__(self, other):
        """Return ``self * other``."""
        return self._product(other)

    def __rmul__(self, other):
        """Return ``other * self``."""
        return self._product(other, reflected=True)

    def __truediv__(self, other):
        """Return ``self / other``."""
        return self._product(other, divide=True)

    def __rtruediv__(self, other):
        """Return ``other / self``."""
        return self._product(other, divide=True, reflected=True)

    def __pow__(self, exponent, modulo=None):
        """Return ``self ** exponent``; negative exponents invert."""
        if modulo is not None or isinstance(exponent, bool):
            return NotImplemented
        if not isinstance(exponent, int):
            return NotImplemented
        if exponent < 0 and not self:
            raise ZeroDivisionError(f"division by zero in {self._field!r}")
        return self._from_pari(self._pari() ** int(exponent))

    def __neg__(self):
        """Return ``-self``."""
        return FiniteFieldElement(
            self._field, [-c for c in self._coefficients]
        )

    def __pos__(self):
        """Return ``self``."""
        return self

    def __bool__(self):
        """Return whether the element is nonzero."""
        return any(self._coefficients)

    def __int__(self):
        """Return the element as an integer in ``[0, p)``, if it is one."""
        if any(self._coefficients[1:]):
            raise TypeError(f"{self} is not in the prime field")
        return int(self._coefficients[0])

    def __eq__(self, other):
        """Compare with an element of the same field, or an integer."""
        if isinstance(other, FiniteFieldElement):
            return (self._field, self._coefficients) == (
                other._field,
                other._coefficients,
            )
        if isinstance(other, int) and not isinstance(other, bool):
            return self == self._field(other)
        return NotImplemented

    def __hash__(self):
        """Hash consistently with ``__eq__`` (an integer's hash if equal)."""
        if not any(self._coefficients[1:]):
            return hash(int(self._coefficients[0]))
        return hash((self._field, self._coefficients))

    # Mathematical functions, computed by PARI.

    def order(self):
        """Return the multiplicative order (PARI ``fforder``)."""
        if not self:
            raise ValueError("0 has no multiplicative order")
        return Integer(self._pari_call(_backend().PARI.fforder))

    def minpoly(self, x=None):
        """Return the minimal polynomial over ``F_p``, in ``x``."""
        return _backend().ff_polynomial("minpoly", self, x)

    def charpoly(self, x=None):
        """Return the characteristic polynomial over ``F_p``, in ``x``."""
        return _backend().ff_polynomial("charpoly", self, x)

    def trace(self):
        """Return the trace to ``F_p``, as an integer in ``[0, p)``."""
        return _backend().ff_lift("trace", self)

    def norm(self):
        """Return the norm to ``F_p``, as an integer in ``[0, p)``."""
        return _backend().ff_lift("norm", self)

    def is_square(self):
        """Return whether the element is a square in the field."""
        return bool(self._pari_call(_backend().PARI.issquare))

    def sqrt(self):
        """Return a square root; raise ``ValueError`` if there is none."""
        if not self.is_square():
            raise ValueError(f"{self} is not a square in {self._field!r}")
        return self._from_pari(self._pari_call(_backend().PARI.sqrt))

    def log(self, base=None):
        """Return ``n`` with ``base^n == self`` (PARI ``fflog``).

        ``base`` defaults to the field's ``primitive_element()``.
        """
        if not self:
            raise ValueError("0 has no logarithm")
        base = self._field.primitive_element() if base is None else base
        base = self._field(base)
        backend = _backend()
        return Integer(self._pari_call(backend.PARI.fflog, base._pari()))

    # Printing.

    def _terms(self, power):
        terms = []
        for i in reversed(range(len(self._coefficients))):
            c = self._coefficients[i]
            if not c:
                continue
            if i == 0:
                terms.append(str(c))
                continue
            monomial = power(self._field.name, i)
            terms.append(monomial if c == 1 else f"{c}{{}}{monomial}")
        return terms

    def __repr__(self):
        """Return ``a^2 + 2*a + 1``, like PARI."""

        def power(name, i):
            return name if i == 1 else f"{name}^{i}"

        terms = [t.replace("{}", "*") for t in self._terms(power)]
        return " + ".join(terms) or "0"

    def _sympystr(self, printer):
        return repr(self)

    def _latex(self, printer):
        def power(name, i):
            return name if i == 1 else f"{name}^{{{i}}}"

        terms = [t.replace("{}", " ") for t in self._terms(power)]
        return " + ".join(terms) or "0"

    def _repr_latex_(self):
        """Render as math in Jupyter and Quarto."""
        return latex(self)._repr_latex_()
