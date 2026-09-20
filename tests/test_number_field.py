"""Number fields (M5, task 7, D14).

Expected values come from cypari2's PARI.  Nothing here computes a class
group above degree 4 or discriminant 10^6 (D7), so the suite stays fast.
"""

import pytest
import sympy

from er2 import dispatch, prelude
from er2.runtime.modular import Mod
from er2.runtime.number_field import NumberField, PrimeIdeal
from er2.runtime.numbers import Integer

x, y = sympy.symbols("x y")

# Q(sqrt(-5)): the textbook field where unique factorization fails.
QI5 = x**2 + 5


def test_it_is_in_the_prelude():
    assert prelude.namespace()["NumberField"] is NumberField


def test_degree_and_discriminant():
    # GP: nfinit(x^2+5).disc, nfinit(x^2-2).disc, nfinit(x^2-x-1).disc
    assert NumberField(QI5).degree == 2
    assert NumberField(QI5).discriminant == -20
    assert NumberField(x**2 - 2).discriminant == 8
    # The field discriminant, not the polynomial's: disc(x^2-x-1) = 5.
    assert NumberField(x**2 - x - 1).discriminant == 5
    assert NumberField(x**3 - x - 1).discriminant == -23
    assert isinstance(NumberField(QI5).discriminant, Integer)


def test_the_discriminant_is_the_field_not_the_polynomial():
    """``x^2 + 3`` has polynomial discriminant -12 but field -3."""
    assert sympy.discriminant(x**2 + 3, x) == -12
    assert NumberField(x**2 + 3).discriminant == -3


def test_integral_basis_and_generator():
    field = NumberField(QI5)
    basis = field.integral_basis()
    assert basis == [Mod(1, QI5), Mod(x, QI5)]
    assert all(isinstance(b, Mod) and b.is_polynomial for b in basis)
    assert field.gen() == Mod(x, QI5)
    # The golden ratio: x already denotes (1 + sqrt(5))/2, so Z[x] is
    # the whole ring of integers and the basis is again [1, x].
    golden = NumberField(x**2 - x - 1)
    assert golden.integral_basis() == [
        Mod(1, x**2 - x - 1),
        Mod(x, x**2 - x - 1),
    ]


def test_elements_are_mod_objects_and_do_arithmetic():
    field = NumberField(QI5)
    a = field.gen()
    assert a**2 == field(-5)
    assert (a + 1) * (a - 1) == field(-6)
    assert isinstance(a * a, Mod)


def test_class_number_and_class_group():
    # GP: bnfinit(x^2+5).no is 2, .cyc is [2].
    field = NumberField(QI5)
    assert field.class_number() == 2
    assert field.class_group() == [2]
    assert isinstance(field.class_number(), Integer)
    # h = 1: unique factorization, and the class group is trivial.
    for polynomial in (x**2 - 2, x**2 + 1, x**2 - x - 1):
        assert NumberField(polynomial).class_number() == 1
        assert NumberField(polynomial).class_group() == []


def test_units():
    # An imaginary quadratic field has no fundamental unit, only +-1.
    field = NumberField(QI5)
    assert field.units() == []
    assert field.roots_of_unity() == 2
    assert NumberField(x**2 + 1).roots_of_unity() == 4
    # Q(sqrt(2)): the fundamental unit is 1 + sqrt(2), but only up to
    # sign and inversion, and PARI's bnfinit is randomised — three calls
    # in one process returned sqrt(2)+1, sqrt(2)-1 and -sqrt(2)-1. So
    # assert the mathematics, never a particular representative.
    real = NumberField(x**2 - 2)
    (unit,) = real.units()
    modulus = x**2 - 2
    assert unit in [
        Mod(x + 1, modulus),  # 1 + sqrt(2)
        Mod(x - 1, modulus),  # its inverse
        Mod(-x - 1, modulus),  # their negatives
        Mod(1 - x, modulus),
    ]
    # Whatever the representative, it is a unit: its norm is +-1, which
    # for a quadratic element is the constant term of its minimal
    # polynomial.
    minimal = dispatch.minpoly(unit, x)
    assert sympy.Poly(minimal, x).degree() == 2
    assert abs(minimal.subs(x, 0)) == 1


def test_bnfinit_runs_once_per_field(monkeypatch):
    """D14: the expensive call is cached, as plain data (not a PARI object)."""
    from er2.backends import pari_backend

    field = NumberField(QI5)
    calls = []
    original = pari_backend.number_field_class_group

    def counted(*args, **kwargs):
        calls.append(kwargs.get("certify", False))
        return original(*args, **kwargs)

    monkeypatch.setattr(pari_backend, "number_field_class_group", counted)
    field.class_number()
    field.class_group()
    field.units()
    field.roots_of_unity()
    assert calls == [False]
    # Certifying needs the structure that was thrown away, so it reruns.
    assert field.class_number(certify=True) == 2
    assert calls == [False, True]
    field.class_group(certify=True)
    assert calls == [False, True]


def test_no_pari_object_is_kept(monkeypatch):
    """Clearing PARI's stack must not damage a field (CLAUDE.md, M4)."""
    import cypari2

    from er2.backends import pari_backend

    field = NumberField(QI5)
    assert field.class_number() == 2
    pari_backend.set_stack()
    assert field.class_number() == 2
    assert field.discriminant == -20
    assert field.factor(3)[0][0].p == 3
    for slot in NumberField.__slots__:
        value = getattr(field, slot)
        assert not isinstance(value, cypari2.gen.Gen)


# GP: idealprimedec(nfinit(x^2+5), p) gives (e, f) for each prime above p.
DECOMPOSITION = [
    (2, [(2, 1)]),  # ramified
    (3, [(1, 1), (1, 1)]),  # split
    (5, [(2, 1)]),  # ramified
    (7, [(1, 1), (1, 1)]),  # split
    (11, [(1, 2)]),  # inert
]


@pytest.mark.parametrize(("p", "expected"), DECOMPOSITION)
def test_prime_decomposition(p, expected):
    field = NumberField(QI5)
    factors = field.factor(p)
    assert [
        (int(ideal.ramification_index), int(ideal.residue_degree))
        for ideal, _ in factors
    ] == expected
    # The exponent in the pair is the ramification index.
    assert [int(e) for _, e in factors] == [e for e, _ in expected]
    # sum of e*f over the primes above p is the degree.
    assert sum(
        int(i.ramification_index) * int(i.residue_degree) for i, _ in factors
    ) == int(field.degree)


def test_prime_ideal_properties():
    field = NumberField(QI5)
    (ramified, exponent) = field.factor(2)[0]
    assert isinstance(ramified, PrimeIdeal)
    assert ramified.p == 2 and exponent == 2
    assert ramified.is_ramified() and not ramified.is_inert()
    assert ramified.norm() == 2  # p^f = 2^1
    assert ramified.field == field
    assert repr(ramified) == "(2, x + 1)"
    (inert, _) = field.factor(11)[0]
    assert inert.is_inert() and not inert.is_ramified()
    assert inert.norm() == 121


def test_factor_rejects_non_primes():
    field = NumberField(QI5)
    with pytest.raises(ValueError, match="not prime"):
        field.factor(4)
    with pytest.raises(TypeError, match="rational prime"):
        field.factor(x)


def test_the_polynomial_must_define_a_number_field():
    for bad, message in (
        (2 * x**2 + 1, "monic"),
        (x**2 - sympy.Rational(1, 2), "monic"),
        (x**2 - 1, "irreducible"),
        (sympy.Integer(3), "one variable"),
    ):
        with pytest.raises((TypeError, ValueError), match=message):
            NumberField(bad)
    with pytest.raises(TypeError, match="one variable"):
        NumberField(x * y)
    with pytest.raises(TypeError, match="polynomial over Q"):
        NumberField("x^2 + 5")


def test_equality_and_repr():
    assert NumberField(QI5) == NumberField(x**2 + 5)
    assert NumberField(QI5) != NumberField(x**2 + 1)
    assert len({NumberField(QI5), NumberField(x**2 + 5)}) == 1
    assert repr(NumberField(QI5)) == "NumberField(x**2 + 5)"
