"""Resultants and discriminants (M5, task 5).

``resultant`` and ``discriminant`` go to PARI for polynomials over Q and
to SymPy for symbolic coefficients.  Both follow the standard sign
convention, which is PARI's: ``sympy.resultant`` answers ``Res(g, f)``
when ``deg f < deg g``, so the SymPy route puts the sign back
(ARCHITECTURE §3.4).  Expected values come from cypari2's PARI.
"""

import random

import pytest
import sympy

from er2 import dispatch
from er2.backends import pari_backend, sympy_backend
from er2.runtime.numbers import Integer

x, y = sympy.symbols("x y")


def test_backend_choice():
    impl = dispatch.implementation
    # Polynomials over Q in the variable alone, constants included.
    for args in (
        (x**2 + 1, x**3 - 2, x),
        (sympy.Rational(1, 2) * x, x - 1, x),
        (sympy.Integer(3), x**2 + 1, x),
    ):
        assert impl("resultant", args, {}) is pari_backend.resultant
    assert impl("discriminant", (x**3 + x + 1, x), {}) is (
        pari_backend.discriminant
    )
    # Symbolic coefficients and irrational ones stay with SymPy.
    for args in ((x**2 + y, x - y, x), (x**2 + sympy.sqrt(2), x - 1, x)):
        assert impl("resultant", args, {}) is sympy_backend.resultant
    assert impl("discriminant", (x**2 + y * x + 1, x), {}) is (
        sympy_backend.discriminant
    )


# GP: polresultant(f, g).
RESULTANTS = [
    (x**2 + 1, x**3 - 2, 5),
    (x**2 - 1, x**2 - 4, 9),
    (x - 1, x**3 - 8, -7),
    (x**3 - 8, x - 1, 7),
    (2 * x**2 + 3, 5 * x**3 - 1, 683),
]

# GP: poldisc(f).
DISCRIMINANTS = [
    (x**3 + x + 1, -31),
    (x**2 + 5, -20),
    (x**2 - 4, 16),
    (x**5 - x - 1, 2869),
    (x**4 + 1, 256),
    (x**2 + 2 * x + 1, 0),
]


@pytest.mark.parametrize(("f", "g", "expected"), RESULTANTS)
def test_resultant(f, g, expected):
    result = dispatch.resultant(f, g, x)
    assert result == expected
    assert isinstance(result, Integer)
    # Both backends agree, sign included.
    assert sympy_backend.resultant(f, g, x) == expected


@pytest.mark.parametrize(("f", "expected"), DISCRIMINANTS)
def test_discriminant(f, expected):
    result = dispatch.discriminant(f, x)
    assert result == expected
    assert isinstance(result, Integer)
    assert sympy_backend.discriminant(f, x) == expected


def test_the_variable_may_be_left_out():
    assert dispatch.resultant(x**2 + 1, x**3 - 2) == 5
    assert dispatch.discriminant(x**3 + x + 1) == -31
    z = sympy.Symbol("z")
    assert dispatch.resultant(z**2 + 1, z**3 - 2) == 5
    assert dispatch.resultant(x**2 + y, x - y, x) == y**2 + y
    assert dispatch.discriminant(x**2 + y * x + 1, x) == y**2 - 4


def test_the_variable_is_needed_when_it_is_ambiguous():
    for call in (
        lambda: dispatch.resultant(x + y, x - y),
        lambda: dispatch.resultant(Integer(2), Integer(3)),
        lambda: dispatch.discriminant(x * y + 1),
    ):
        with pytest.raises(TypeError, match="the variable is needed"):
            call()


def test_zero_when_there_is_a_common_root():
    assert dispatch.resultant(x**2 - 1, x**3 - 1, x) == 0
    # A repeated root makes the discriminant vanish.
    assert dispatch.discriminant((x - 2) ** 2 * (x + 1), x) == 0


def test_the_sign_follows_the_definition_not_sympy():
    """``Res(f, g) = (-1)^(deg f * deg g) * Res(g, f)`` (the user's D-call).

    ``sympy.resultant`` gives ``7`` both ways round; ER2 does not.
    """
    assert dispatch.resultant(x - 1, x**3 - 8, x) == -7
    assert dispatch.resultant(x**3 - 8, x - 1, x) == 7
    assert sympy.resultant(x - 1, x**3 - 8, x) == 7
    # The definition: lc(f)^deg(g) * prod over the roots of f of g.
    f, g = 2 * x - 1, x**3 + 1
    expected = sympy.LC(f, x) ** 3 * g.subs(x, sympy.Rational(1, 2))
    assert dispatch.resultant(f, g, x) == expected


def _random_polynomial(degree, rng, symbolic=False):
    """Return a polynomial in ``x`` of at most the given degree."""
    coefficients = []
    for _ in range(degree + 1):
        if symbolic:
            coefficients.append(rng.choice([y, y**2 - 1, rng.randint(-4, 4)]))
        else:
            coefficients.append(
                sympy.Rational(rng.randint(-6, 6), rng.choice([1, 1, 2, 3]))
            )
    return sympy.expand(sum(c * x**i for i, c in enumerate(coefficients)))


def test_the_two_backends_agree_on_random_polynomials():
    """As for ``factor`` in M4: PARI must answer what SymPy answers."""
    rng = random.Random(20260920)
    compared = 0
    for _ in range(200):
        f = _random_polynomial(rng.randint(0, 5), rng)
        g = _random_polynomial(rng.randint(0, 5), rng)
        if f == 0 or g == 0:
            continue
        assert pari_backend.resultant(f, g, x) == sympy_backend.resultant(
            f, g, x
        )
        assert pari_backend.discriminant(f, x) == sympy_backend.discriminant(
            f, x
        )
        compared += 1
    assert compared > 150


def test_the_backends_agree_with_symbolic_coefficients():
    """PARI is not used for these, but it is the oracle for the sign."""
    rng = random.Random(1729)
    for _ in range(40):
        f = _random_polynomial(rng.randint(0, 3), rng, symbolic=True)
        g = _random_polynomial(rng.randint(0, 3), rng, symbolic=True)
        if f == 0 or g == 0:
            continue
        expected = pari_backend.resultant(f, g, x)
        assert sympy.expand(dispatch.resultant(f, g, x) - expected) == 0


def test_antisymmetry_on_random_polynomials():
    rng = random.Random(31337)
    for _ in range(100):
        m, n = rng.randint(1, 5), rng.randint(1, 5)
        f, g = _random_polynomial(m, rng), _random_polynomial(n, rng)
        m, n = sympy.degree(f, x), sympy.degree(g, x)
        if f == 0 or g == 0 or m < 1 or n < 1:
            continue
        assert dispatch.resultant(f, g, x) == (-1) ** (m * n) * (
            dispatch.resultant(g, f, x)
        )


def test_discriminant_is_the_resultant_of_f_and_its_derivative():
    """``disc(f) = (-1)^(n(n-1)/2) / lc(f) * Res(f, f')``."""
    for f, expected in DISCRIMINANTS:
        n = sympy.degree(f, x)
        sign = (-1) ** (n * (n - 1) // 2)
        derivative = sympy.diff(f, x)
        resultant = dispatch.resultant(f, derivative, x)
        assert sign * resultant / sympy.LC(f, x) == expected
