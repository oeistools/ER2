"""Finite fields (M5, D13).  Expected values computed with cypari2's PARI.

GF(9) is ``F_3[a] / (a^2 + a + 2)``, PARI's ``ffinit(3, 2)``, so
``a^2 = 2*a + 1``.
"""

import itertools

import pytest
import sympy

from er2 import dispatch
from er2.backends import pari_backend
from er2.runtime.finite_field import GF, FiniteField, FiniteFieldElement
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational

PARI = pari_backend.PARI
x = sympy.Symbol("x")


def test_field_construction():
    field = GF(9)
    assert (field.order, field.characteristic, field.degree) == (9, 3, 2)
    assert all(
        type(value) is Integer
        for value in (field.order, field.characteristic, field.degree)
    )
    assert field.name == "a"
    # GP: lift(ffinit(3, 2, 'a)) = a^2 + a + 2
    assert field.modulus() == sympy.Symbol("a") ** 2 + sympy.Symbol("a") + 2
    assert GF(3, 2) == field and GF(9) == field
    assert GF(9, "t") != field  # another generator name, another field
    assert GF(9, "t").name == "t"
    assert hash(GF(3, 2)) == hash(field)
    assert repr(field) == "GF(9)" and repr(GF(9, "t")) == 'GF(9, "t")'
    assert repr(GF(7)) == "GF(7)"
    assert GF(2, 127).order == 2**127


def test_construction_errors():
    for bad in (12, 1, 0, -7):
        with pytest.raises(ValueError, match="prime power"):
            GF(bad)
    with pytest.raises(TypeError, match="must be an integer"):
        GF(9.0)
    with pytest.raises(ValueError, match="prime p and a degree"):
        GF(9, 2)  # 9 is not prime
    with pytest.raises(ValueError, match="prime p and a degree"):
        GF(3, 0)
    with pytest.raises(ValueError, match="generator name"):
        GF(9, "2x")


def test_elements_and_generator():
    field = GF(9)
    a = field.gen()
    assert isinstance(a, FiniteFieldElement) and a.parent == field
    assert a in field and Integer(1) not in field
    # GP: a^2 = 2*a + 1, a^4 = 2, a^8 = 1
    assert a**2 == 2 * a + 1
    assert a**4 == 2
    assert a**8 == 1
    assert a.coefficients() == [0, 1]
    assert [str(e) for e in field] == [
        "0",
        "1",
        "2",
        "a",
        "a + 1",
        "a + 2",
        "2*a",
        "2*a + 1",
        "2*a + 2",
    ]
    assert len(set(field)) == 9
    assert GF(7).gen() == 1  # the prime field, as in SageMath


def test_arithmetic_and_coercion():
    field = GF(9)
    a = field.gen()
    assert a + 2 == field(2) + a and 2 + a == a + 2
    assert a - 1 == a + 2  # -1 = 2 in F_3
    assert 1 - a == 1 + 2 * a  # -a = 2*a in F_3
    assert a * 2 == 2 * a
    assert a / 2 == 2 * a  # 1/2 = 2 in F_3
    assert 1 / a == a**7
    assert a**-1 == a**7
    assert -a == 2 * a
    assert +a == a
    assert field(Rational(1, 2)) == 2
    assert a + Mod(2, 3) == a + 2  # Mod(n, p) enters the field
    assert bool(a) and not bool(field(0))
    assert int(field(5)) == 2
    with pytest.raises(TypeError, match="not in the prime field"):
        int(a)


def test_equality_and_hash():
    field = GF(9)
    a = field.gen()
    # As in PARI and SageMath, an element equals an integer of F_p.
    assert field(3) == 0 and field(4) == 1
    assert hash(field(4)) == hash(1)
    assert a != 1 and a != GF(25).gen()
    assert len({a, a + 0, field(1), Integer(1)}) == 2


def test_unsupported_operands():
    a, b = GF(9).gen(), GF(25).gen()
    for unsupported in (
        lambda: a + b,
        lambda: a * b,
        lambda: a + Mod(2, 5),
        lambda: a + 1.5,
        lambda: a * "x",
        lambda: a**0.5,
        lambda: pow(a, 2, 5),
    ):
        with pytest.raises(TypeError):
            unsupported()


def test_division_by_zero():
    field = GF(9)
    zero, a = field(0), field.gen()
    for bad in (lambda: a / zero, lambda: 1 / zero, lambda: zero**-1):
        with pytest.raises(ZeroDivisionError):
            bad()
    with pytest.raises(ZeroDivisionError, match="denominator"):
        field(Rational(1, 3))


def test_element_functions():
    field = GF(9)
    a = field.gen()
    # GP: fforder(a) = 8, lift(trace(a)) = 2, lift(norm(a)) = 2,
    # lift(minpoly(a)) = x^2 + x + 2, lift(charpoly(a + 1)) = x^2 + 2*x + 2
    assert a.order() == 8 and type(a.order()) is Integer
    assert a.trace() == 2 and a.norm() == 2
    assert type(a.trace()) is Integer
    assert a.minpoly() == x**2 + x + 2
    assert (a + 1).charpoly() == x**2 + 2 * x + 2
    t = sympy.Symbol("t")
    assert a.minpoly(t) == t**2 + t + 2
    assert dispatch.minpoly(a) == a.minpoly()
    assert dispatch.charpoly(a + 1) == (a + 1).charpoly()
    # GP: issquare(a) = 0, issquare(a^2) = 1, sqrt(a^2) = a
    assert not a.is_square() and (a**2).is_square()
    assert (a**2).sqrt() == a
    with pytest.raises(ValueError, match="not a square"):
        a.sqrt()
    with pytest.raises(ValueError, match="no multiplicative order"):
        field(0).order()


def test_primitive_element_and_logarithm():
    field = GF(9)
    a = field.gen()
    # The first primitive element in the order of elements(); PARI's
    # ffprimroot is random, so ER2 does not use it.
    assert field.primitive_element() == a
    assert field.primitive_element() is field.primitive_element()
    assert (a**3).log() == 3
    assert (a**5).log(a) == 5
    assert field(2).log() == 4  # 2 = a^4
    with pytest.raises(ValueError, match="no logarithm"):
        field(0).log()
    small = GF(7)
    root = small.primitive_element()
    assert root == 3 and root.order() == 6  # GP: znprimroot(7) = Mod(3, 7)
    assert small(5).log() == 5  # 3^5 = 243 = 5 (mod 7)


def test_printing_and_latex():
    from er2.printing import latex

    field = GF(9)
    a = field.gen()
    assert repr(a**2 + 1) == str(a**2 + 1) == "2*a + 2"
    assert repr(a + 1) == "a + 1"
    assert repr(field(0)) == "0" and repr(field(1)) == "1"
    assert repr(GF(9, "t").gen() ** 3) == "2*t + 2"
    assert latex(a**2 + 1) == "2 a + 2"
    assert latex(field) == r"\mathbb{F}_{9}"
    assert (a**2 + 1)._repr_latex_() == "$2 a + 2$"
    assert field._repr_latex_() == r"$\mathbb{F}_{9}$"
    high = GF(2, 5).gen() ** 4
    assert repr(high) == "a^4" and latex(high) == "a^{4}"


def _pari_element(element):
    """Return the same element, built independently through PARI."""
    return pari_backend.ff_element(element)


@pytest.mark.parametrize("order", [7, 9, 32])
def test_arithmetic_matches_pari_on_every_element(order):
    field = GF(order)
    elements = list(field)
    assert len(elements) == order
    for u, v in itertools.product(elements, elements):
        pu, pv = _pari_element(u), _pari_element(v)
        assert _pari_element(u + v) == pu + pv
        assert _pari_element(u * v) == pu * pv
        if v:
            assert _pari_element(u / v) == pu / pv
    for u in elements:
        assert _pari_element(-u) == -_pari_element(u)
        if u:
            assert u.order() == Integer(PARI.fforder(_pari_element(u)))
            assert u.log(field.primitive_element()) >= 0
        assert u.trace() == Integer(PARI.lift(PARI.trace(_pari_element(u))))
        assert u.norm() == Integer(PARI.lift(PARI.norm(_pari_element(u))))


def test_conversions_at_the_boundary():
    field = GF(9)
    a = field.gen()
    gen = pari_backend.to_pari(a)
    assert gen.type() == "t_FFELT"
    back = pari_backend.from_pari(gen)
    assert back == a and back.parent == field
    assert type(back) is FiniteFieldElement
    # A PARI result comes back as an ER2 element (pari.ffprimroot).
    root = pari_backend.pari.ffprimroot(a)
    assert isinstance(root, FiniteFieldElement)
    assert root.parent == field and root.order() == 8


def test_no_pari_object_is_kept(monkeypatch):
    """Elements hold coefficients, not PARI objects (M4's stack rule)."""
    a = GF(9).gen()
    assert all(type(c) is Integer for c in (a**3).coefficients())
    assert not any(
        isinstance(getattr(a, slot, None), type(pari_backend.PARI(1)))
        for slot in FiniteFieldElement.__slots__
    )
    assert isinstance(GF(9), FiniteField)
