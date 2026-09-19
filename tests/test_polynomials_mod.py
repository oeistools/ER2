"""Polynomials over a prime field (M5, task 4).

``factor(f, modulus=p)`` and ``gcd`` go to PARI, and must give exactly
what SymPy gives: monic factors with coefficients in ``(-p/2, p/2]`` and
the leading coefficient in front.
"""

import random

import pytest
import sympy

from er2 import dispatch
from er2.backends import pari_backend, sympy_backend
from er2.runtime.finite_field import GF

x, y = sympy.symbols("x y")


def test_backend_choice():
    impl = dispatch.implementation
    mod = {"modulus": 5}
    assert (
        impl("factor", (x**4 + 1,), mod) is pari_backend.factor_polynomial_mod
    )
    assert impl("gcd", (x**2 - 1, x**2 + x), mod) is pari_backend.gcd_mod
    assert (
        impl("isirreducible", (x**4 + 1,), mod) is pari_backend.isirreducible
    )
    assert impl("isirreducible", (x**4 + 1,), {}) is pari_backend.isirreducible
    # Not PARI's case: a composite modulus, a multivariate polynomial, a
    # polynomial that vanishes modulo p, or other options.
    for args, kwargs in (
        ((x**2 + 1,), {"modulus": 9}),
        ((x**2 - y**2,), {"modulus": 5}),
        ((5 * x**2,), {"modulus": 5}),
        ((x**2 + 1,), {"modulus": 5, "extension": True}),
    ):
        assert impl("factor", args, kwargs) is sympy_backend.factor
    assert impl("isirreducible", (x**2 - y**2,), {}) is (
        sympy_backend.isirreducible
    )


def test_factor_modulo_a_prime():
    # GP: factormod(x^8 - x, 2), factormod(x^4 + 1, 5)
    assert dispatch.factor(x**8 - x, modulus=2) == (
        x * (x + 1) * (x**3 + x + 1) * (x**3 + x**2 + 1)
    )
    assert dispatch.factor(x**4 + 1, modulus=5) == (x**2 - 2) * (x**2 + 2)
    assert dispatch.factor(x**2 + 1, modulus=2) == (x + 1) ** 2
    # The integer content stays in front, as in SymPy, which does not
    # reduce it modulo p.  SymPy builds these products unevaluated, so it
    # is the oracle for the comparison (as for ``factor`` in M4).
    for f, p in ((2 * x**2 - 2, 5), (3 * x**2 + 3 * x, 7), (9 * x - 9, 5)):
        assert dispatch.factor(f, modulus=p) == sympy.factor(f, modulus=p)
    assert str(dispatch.factor(2 * x**2 - 2, modulus=5)) == (
        "2*(x - 1)*(x + 1)"
    )
    assert str(dispatch.factor(9 * x - 9, modulus=5)) == "9*(x - 1)"
    # A polynomial that vanishes mod p is left to SymPy, which keeps it.
    assert dispatch.factor(5 * x**2, modulus=5) == 5 * x**2


def test_factor_over_a_prime_field_by_domain():
    assert dispatch.factor(x**4 + 1, domain=GF(5)) == dispatch.factor(
        x**4 + 1, modulus=5
    )
    with pytest.raises(NotImplementedError, match="GF\\(9\\)"):
        dispatch.factor(x**4 + 1, domain=GF(9))
    with pytest.raises(NotImplementedError, match="pari.raw.factormod"):
        dispatch.isirreducible(x**4 + 1, domain=GF(9))


def test_irreducibility():
    # GP: polisirreducible(Mod(1, 2)*(x^2 + x + 1)) = 1
    assert dispatch.isirreducible(x**2 + x + 1, modulus=2) is True
    assert dispatch.isirreducible(x**2 + 1, modulus=2) is False
    assert dispatch.isirreducible(x**4 + 1, modulus=5) is False
    assert dispatch.isirreducible(x**4 + 1, domain=GF(5)) is False
    # Over Q (PARI), and SymPy for the rest.
    assert dispatch.isirreducible(x**4 + 1) is True
    assert dispatch.isirreducible(x**2 - 2) is True
    assert dispatch.isirreducible(x**2 - 1) is False
    assert dispatch.isirreducible(x**2 - y**2) is False
    assert dispatch.isirreducible(x**2 + y**2) is True
    # A constant is not irreducible (PARI asks for degree >= 1); SymPy
    # answers True for the same polynomial.
    assert dispatch.isirreducible(6 * x**2 - 6 * x - 1, modulus=3) is False
    assert sympy_backend.isirreducible(6 * x**2 - 6 * x - 1, modulus=3) is True


def test_gcd_modulo_a_prime():
    # ``gcd`` comes from the PARI table, so it lives in FUNCTIONS.
    gcd = dispatch.FUNCTIONS["gcd"]
    # GP: gcd(Mod(1,3)*(x^2 - 1), Mod(1,3)*(x^2 + x)) = 2*x + 2, made monic
    assert gcd(x**2 - 1, x**2 + x, modulus=3) == x + 1
    assert gcd(x**2 + 1, x + 1, modulus=2) == x + 1
    assert gcd(x**2 + 1, x, modulus=5) == 1
    assert gcd(12, 18) == 6  # numbers still work


def _random_polynomial(rng, degree):
    return sympy.Add(*(rng.randint(-9, 9) * x**i for i in range(degree + 1)))


@pytest.mark.parametrize("seed", range(40))
def test_pari_and_sympy_agree_modulo_a_prime(seed):
    rng = random.Random(seed)
    p = rng.choice([2, 3, 5, 7, 101])
    f = _random_polynomial(rng, rng.randint(1, 8))
    if not pari_backend.is_modular_polynomial(f, p):
        pytest.skip("f vanishes modulo p")
    assert pari_backend.factor_polynomial_mod(f, p) == sympy.factor(
        f, modulus=p
    )
    if sympy.Poly(f, x, modulus=p).degree() > 0:  # constants: see above
        assert pari_backend.isirreducible(f, p) == (
            sympy_backend.isirreducible(f, modulus=p)
        )
    g = _random_polynomial(rng, rng.randint(1, 5))
    if pari_backend.is_modular_polynomial(g, p):
        assert pari_backend.gcd_mod(f, g, p) == sympy.gcd(f, g, modulus=p)


def test_factorization_over_an_extension_field_through_pari():
    """Until ER2 has such polynomials, PARI's own result is available."""
    raw = pari_backend.pari.raw.factormod(
        pari_backend.to_pari(x**4 + 1), pari_backend.to_pari(GF(9).gen())
    )
    assert (
        str(raw) == "[x + a, 1; x + (a + 1), 1; x + 2*a, 1; x + (2*a + 2), 1]"
    )
    # Converting it explains why, instead of failing obscurely.
    with pytest.raises(TypeError, match="as a coefficient of a polynomial"):
        pari_backend.from_pari(raw)
