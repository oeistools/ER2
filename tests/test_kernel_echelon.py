"""The rational fast path of ``kernel`` gives SymPy's echelon basis."""

import random

import sympy

from er2 import dispatch


def test_rational_echelon_matches_sympy_rref():
    rng = random.Random(7)
    for _ in range(40):
        k, n = rng.randint(1, 4), rng.randint(4, 8)
        rows = [
            [
                sympy.Rational(rng.randint(-9, 9), rng.randint(1, 4))
                for _ in range(n)
            ]
            for _ in range(k)
        ]
        if rng.random() < 0.3:
            rows[-1] = [2 * v for v in rows[0]]  # dependent rows too
        vectors = [sympy.Matrix(n, 1, row) for row in rows]
        got = dispatch._rational_echelon(vectors)
        echelon = sympy.Matrix.hstack(*vectors).T.rref()[0]
        assert got == [echelon[i, :].T for i in range(k)]


def test_symbolic_vectors_take_the_general_route():
    x = sympy.Symbol("x")
    assert dispatch._rational_echelon([sympy.Matrix([x, 1])]) is None
