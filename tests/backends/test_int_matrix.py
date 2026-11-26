"""D23: integer matrices reach PARI as GP text, and only integers do."""

import random

import pytest
import sympy

from er2.backends.pari_backend import PARI, _int_matrix, to_pari


@pytest.mark.parametrize("shape", [(1, 1), (1, 4), (4, 1), (3, 3), (2, 5)])
def test_same_matrix_as_entry_by_entry(shape):
    rows, cols = shape
    rng = random.Random(rows * 10 + cols)
    entries = [rng.randint(-(10**30), 10**30) for _ in range(rows * cols)]
    built = _int_matrix(rows, cols, entries)
    assert built == PARI.matrix(rows, cols, entries)
    assert built.type() == "t_MAT" and list(PARI.matsize(built)) == [
        rows,
        cols,
    ]


def test_only_ints_reach_the_text():
    with pytest.raises(TypeError):
        _int_matrix(1, 1, ['1); system("x"'])
    with pytest.raises(TypeError):
        _int_matrix(1, 2, [1, 2.0])
    with pytest.raises(TypeError):
        _int_matrix(1, 1, [True])


def test_sympy_matrices_over_z_and_q():
    z = sympy.Matrix([[1, -2], [3, 4]])
    assert to_pari(z) == PARI.matrix(2, 2, [1, -2, 3, 4])
    q = sympy.Matrix([[sympy.Rational(1, 2), 1]])
    assert to_pari(q) == PARI.matrix(1, 2, [PARI(1) / 2, 1])
    assert to_pari(sympy.zeros(0, 0)) == PARI.matrix(0, 0)


def test_matrices_come_back_from_their_text():
    """PARI to SymPy: Z and Q read from the text, the rest entry by entry."""
    from er2.backends.pari_backend import _rational_entries, from_pari

    z = PARI.matrix(2, 2, [1, -2, 10**40, 4])
    assert from_pari(z) == sympy.Matrix([[1, -2], [10**40, 4]])
    q = PARI.matrix(1, 2, [PARI(1) / 2, -3])
    assert from_pari(q) == sympy.Matrix([[sympy.Rational(1, 2), -3]])
    for other in (
        PARI.matrix(1, 2, [PARI.Mod(1, 3), 2]),
        PARI("[x, 1; 2, 3]"),
        PARI("[1.5, 2]"),
    ):
        size = PARI.matsize(other)
        assert _rational_entries(other, int(size[0]) * int(size[1])) is None
