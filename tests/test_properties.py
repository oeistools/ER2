"""Mathematical invariants on generated input (PLAN backlog 13).

Hypothesis draws the inputs; each test states a property any correct
answer has, whichever backend computes it.  Sizes stay small (numbers
below 10^12, polynomials of degree 6, 3x3 matrices) so that no case is a
long factorization (D7).
"""

import math
from fractions import Fraction

import sympy
from hypothesis import given, settings
from hypothesis import strategies as st

from er2 import prelude
from er2.runtime.numbers import Rational, exact_div, exact_pow

ns = prelude.namespace()
factor, isprime, phi, mu = ns["factor"], ns["isprime"], ns["phi"], ns["mu"]
divisors, det, expand, Mod = (
    ns["divisors"],
    ns["det"],
    ns["expand"],
    ns["Mod"],
)
x = sympy.Symbol("x")

integers = st.integers(min_value=2, max_value=10**12)
small = st.integers(min_value=1, max_value=10**4)
nonzero = st.integers(min_value=-(10**6), max_value=10**6).filter(bool)
settings.register_profile("er2", max_examples=60, deadline=None)
settings.load_profile("er2")


@given(integers)
def test_factor_multiplies_back_to_n_with_prime_factors(n):
    f = factor(n)
    assert f.value() == n
    assert all(isprime(p) and e >= 1 for p, e in f)


@given(small, small)
def test_phi_is_multiplicative(a, b):
    if math.gcd(a, b) == 1:
        assert phi(a * b) == phi(a) * phi(b)


@given(small)
def test_moebius_sums_to_zero_over_divisors(n):
    assert sum(mu(d) for d in divisors(n)) == (1 if n == 1 else 0)


@given(small)
def test_gauss_phi_sums_to_n_over_divisors(n):
    assert sum(phi(d) for d in divisors(n)) == n


@given(nonzero, nonzero, nonzero)
def test_exact_division_and_power_match_fractions(a, b, c):
    q = exact_div(a, b)
    assert q == Fraction(a, b)
    assert type(q) is (int if a % b == 0 else Rational)
    assert exact_div(q, c) * c == q
    assert exact_pow(q, -2) == Fraction(b, a) ** 2


@given(st.integers(-50, 50), st.integers(-50, 50), st.integers(2, 200))
def test_mod_is_a_ring_homomorphism(a, b, n):
    assert Mod(a, n) * Mod(b, n) == Mod(a * b, n)
    assert Mod(a, n) + Mod(b, n) == Mod(a + b, n)


polynomials = st.lists(st.integers(-6, 6), min_size=2, max_size=7).filter(
    lambda c: c[-1] != 0
)


@given(polynomials, polynomials)
def test_factor_expands_back_to_the_polynomial(p, q):
    f = sympy.expand(
        sum(c * x**k for k, c in enumerate(p))
        * sum(c * x**k for k, c in enumerate(q))
    )
    assert expand(factor(f) - f) == 0


matrices = st.lists(st.integers(-9, 9), min_size=9, max_size=9).map(
    lambda v: sympy.Matrix(3, 3, v)
)


@given(matrices, matrices)
def test_det_is_multiplicative(a, b):
    assert det(a * b) == det(a) * det(b)
