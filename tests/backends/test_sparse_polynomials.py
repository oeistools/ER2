"""Polynomials read straight from their terms match SymPy's Poly."""

import random

import sympy

from er2.backends.pari_backend import (
    _integer_coefficients,
    _sparse_coefficients,
    to_pari,
)

x, y = sympy.symbols("x y")


def poly_coefficients(expr):
    """Return what Poly gives, as the direct reader's dict."""
    poly = sympy.Poly(expr, x)
    degree = poly.degree()
    return {
        degree - i: (int(c) if c.is_Integer else c)
        for i, c in enumerate(poly.all_coeffs())
        if c != 0
    }


def test_random_polynomials_match_poly():
    rng = random.Random(2026)
    for _ in range(300):
        terms = [
            sympy.Rational(rng.randint(-50, 50), rng.choice([1, 1, 2, 3]))
            * x ** rng.randint(0, 30)
            for _ in range(rng.randint(1, 8))
        ]
        expr = sympy.Add(*terms)
        if expr.free_symbols != {x}:
            continue  # all terms cancelled or were constant
        read = _sparse_coefficients(expr, x)
        assert read is not None, expr
        nonzero = {k: c for k, c in read.items() if c != 0}
        expected = poly_coefficients(expr)
        assert {k: sympy.Rational(str(c)) for k, c in nonzero.items()} == {
            k: sympy.Rational(c) for k, c in expected.items()
        }


def test_other_forms_fall_back_to_poly():
    for expr in (x * (x - 1), (x + 1) ** 3, sympy.sqrt(2) * x, x**-1, x * y):
        assert _sparse_coefficients(expr, x) is None
    assert to_pari(x * (x - 1)) == to_pari(x**2 - x)
    assert _integer_coefficients(x * (x - 1)) == [1, -1, 0]
    assert _integer_coefficients(x**2 / 2) is None  # not over Z
