"""Linear algebra (M5, D12).  Expected values computed with cypari2's PARI.

Matrices over Q go to PARI and the others to SymPy; both routes must give
the same results (checked on random matrices).
"""

import random

import pytest
import sympy
from sympy.matrices.exceptions import (
    NonInvertibleMatrixError,
    NonSquareMatrixError,
)
from sympy.matrices.normalforms import hermite_normal_form, smith_normal_form

from er2 import dispatch
from er2.backends import pari_backend, sympy_backend
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational

Matrix = sympy.Matrix
x, t, a = sympy.symbols("x t a")

A = Matrix([[2, 4, 4], [-6, 6, 12], [10, -4, -16]])  # regular
C = Matrix([[1, 2, 3], [2, 4, 6], [1, 1, 1]])  # rank 2
R = Matrix(
    [[Rational(1, 2), Rational(1, 3)], [Rational(1, 4), Rational(1, 5)]]
)
S = Matrix([[a, 1], [1, a]])  # symbolic: SymPy


def test_backend_choice():
    impl = dispatch.implementation
    assert impl("det", (A,)) is pari_backend.det
    assert impl("det", (R,)) is pari_backend.det
    assert impl("det", (S,)) is sympy_backend.det
    assert impl("det", (Matrix([[0.5, 1], [2, 3]]),)) is sympy_backend.det
    assert impl("rank", (Matrix([[1, 2, 3]]),)) is pari_backend.rank
    # Not square: SymPy, which raises its own error.
    assert impl("det", (Matrix([[1, 2, 3]]),)) is sympy_backend.det
    assert impl("solve", (A, Matrix([1, 2, 3]))) is pari_backend.solve_linear
    assert impl("solve", (S, Matrix([1, 2]))) is sympy_backend.solve_linear
    # A list keeps SymPy's meaning: solve equations for symbols.
    assert impl("solve", ([x - 1], [x])) is sympy_backend.solve


def test_determinant_and_inverse():
    # GP: matdet(A), A^-1, matdet(R), R^-1
    assert dispatch.det(A) == -144 and type(dispatch.det(A)) is Integer
    assert dispatch.det(R) == Rational(1, 60)
    assert type(dispatch.det(R)) is Rational
    assert dispatch.inverse(A) == Matrix(
        [
            [Rational(1, 3), Rational(-1, 3), Rational(-1, 6)],
            [Rational(-1, 6), Rational(1, 2), Rational(1, 3)],
            [Rational(1, 4), Rational(-1, 3), Rational(-1, 4)],
        ]
    )
    assert dispatch.inverse(R) == Matrix([[12, -20], [-15, 30]])
    assert dispatch.det(S) == a**2 - 1
    assert sympy.simplify(dispatch.inverse(S) * S) == sympy.eye(2)


def test_rank_kernel_and_echelon_form():
    # GP: matrank(C) = 2, matker(C) = [1; -2; 1]
    assert dispatch.rank(C) == 2 and type(dispatch.rank(C)) is Integer
    assert dispatch.rank(A) == 3
    assert dispatch.kernel(C) == [Matrix([1, -2, 1])]
    assert dispatch.kernel(A) == []
    assert dispatch.echelon_form(C) == Matrix(
        [[1, 0, -1], [0, 1, 2], [0, 0, 0]]
    )
    # A kernel basis is given in reduced echelon form.
    ones = Matrix([[1, 1, 1, 1], [2, 2, 2, 2]])
    assert dispatch.kernel(ones) == [
        Matrix([1, 0, 0, -1]),
        Matrix([0, 1, 0, -1]),
        Matrix([0, 0, 1, -1]),
    ]
    assert type(dispatch.rank(S)) is Integer


def test_characteristic_and_minimal_polynomials():
    # GP: charpoly(A), minpoly(A), minpoly(matid(3)), minpoly([0,1;0,0])
    char = x**3 + 8 * x**2 - 84 * x + 144
    assert dispatch.charpoly(A) == char
    assert dispatch.minpoly(A) == char
    assert dispatch.charpoly(A, t) == char.subs(x, t)
    assert dispatch.minpoly(sympy.eye(3)) == x - 1
    nilpotent = Matrix([[0, 1], [0, 0]])
    assert dispatch.charpoly(nilpotent) == x**2
    assert dispatch.minpoly(nilpotent) == x**2
    assert (
        sympy.expand(dispatch.charpoly(S) - (x**2 - 2 * a * x + a**2 - 1)) == 0
    )
    # Algebraic numbers (SymPy) and polynomial residues (PARI).
    assert dispatch.minpoly(sympy.sqrt(2) + 1) == x**2 - 2 * x - 1
    assert dispatch.minpoly(Mod(x, x**2 + 1)) == x**2 + 1
    with pytest.raises(TypeError, match="square matrix over Q"):
        dispatch.minpoly(S)


def test_linear_systems():
    # GP: matsolve(A, [1, 2, 3]~) = [-5/6, 11/6, -7/6]~
    b = Matrix([1, 2, 3])
    v = dispatch.solve(A, b)
    assert v == Matrix([Rational(-5, 6), Rational(11, 6), Rational(-7, 6)])
    assert A * v == b
    w = dispatch.solve(S, Matrix([1, 0]))
    assert sympy.simplify(S * w) == Matrix([1, 0])
    assert dispatch.solve([x - 1], [x]) == {x: 1}


def test_normal_forms():
    # GP: mathnf(A), matsnf(A) = [12, 6, 2], mathnf(C), matsnf(C) = [0, 1, 1]
    assert dispatch.hermite_form(A) == Matrix(
        [[12, 0, 10], [0, 6, 0], [0, 0, 2]]
    )
    assert dispatch.smith_form(A) == sympy.diag(2, 6, 12)
    assert dispatch.hermite_form(C) == Matrix([[1, 0], [2, 0], [0, 1]])
    assert dispatch.smith_form(C) == sympy.diag(1, 1, 0)
    assert dispatch.smith_form(Matrix([[1, 2, 3], [4, 5, 6]])) == Matrix(
        [[1, 0, 0], [0, 3, 0]]
    )
    for not_integer in (R, S):
        with pytest.raises(TypeError, match="does not support"):
            dispatch.smith_form(not_integer)


def test_errors_are_the_same_in_both_backends():
    # Singular: rational (PARI) and symbolic (SymPy).
    for matrix in (C, Matrix([[a, 2 * a, 0], [1, 2, 0], [0, 0, 1]])):
        with pytest.raises(NonInvertibleMatrixError):
            dispatch.inverse(matrix)
        with pytest.raises(ValueError):
            dispatch.solve(matrix, Matrix([1, 2, 3]))
    with pytest.raises(NonSquareMatrixError):
        dispatch.det(Matrix([[1, 2, 3]]))


def _random_matrix(rng, rows, cols, rational=False):
    def entry():
        n = rng.randint(-9, 9)
        return Rational(n, rng.randint(1, 5)) if rational else n

    return Matrix(rows, cols, lambda i, j: entry())


def _echelon(vectors):
    if not vectors:
        return []
    return Matrix.hstack(*vectors).T.rref()[0].tolist()


@pytest.mark.parametrize("seed", range(40))
def test_pari_and_sympy_agree_on_random_matrices(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 5)
    square = _random_matrix(rng, n, n, rational=seed % 2 == 1)
    if seed % 4 == 0:  # make some of them singular
        square[0, :] = 2 * square[n - 1, :]
    assert pari_backend.det(square) == sympy_backend.det(square)
    assert pari_backend.rank(square) == sympy_backend.rank(square)
    assert (
        sympy.expand(
            pari_backend.charpoly(square, x)
            - sympy_backend.charpoly(square, x)
        )
        == 0
    )
    assert _echelon(pari_backend.kernel(square)) == _echelon(
        sympy_backend.kernel(square)
    )
    if sympy_backend.det(square) != 0:
        assert pari_backend.inverse(square) == sympy_backend.inverse(square)
        b = _random_matrix(rng, n, 1)
        assert pari_backend.solve_linear(square, b) == (
            sympy_backend.solve_linear(square, b)
        )


@pytest.mark.parametrize("seed", range(40))
def test_normal_forms_agree_with_sympy(seed):
    rng = random.Random(seed)
    rows, cols = rng.randint(1, 5), rng.randint(1, 5)
    matrix = _random_matrix(rng, rows, cols)
    assert pari_backend.smith_form(matrix) == smith_normal_form(matrix)
    if matrix.rank() == rows:  # SymPy's HNF needs full row rank
        assert pari_backend.hermite_form(matrix) == hermite_normal_form(matrix)
