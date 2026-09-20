"""ER2 numbers cross into the scientific stack (ARCHITECTURE.md §1.1).

The README promises that ER2 values pass straight into libraries, which
rests on ``Integer`` implementing ``__index__``, ``__int__``, ``__float__``
and the rest of the contract in §1.1 point 5.  Nothing in ER2 wraps NumPy:
these tests guard interoperability ER2 already has, so that a change to
the number types cannot silently break it.

NumPy is not a dependency of ER2, nor of its test suite (CLAUDE.md keeps
the runtime to ``sympy`` + ``cypari2``).  The module is skipped when NumPy
is absent, as the Quarto tests are skipped without Quarto; CI installs it
so that these run there.
"""

import pytest

from er2.runtime.numbers import Integer, Rational

np = pytest.importorskip("numpy", reason="NumPy is an optional test extra")


def test_integers_are_accepted_as_sizes_and_indices():
    """``__index__``: shapes, ``arange`` and indexing."""
    assert np.zeros(Integer(8)).shape == (8,)
    assert np.zeros((Integer(2), Integer(3))).shape == (2, 3)
    assert len(np.arange(Integer(5))) == 5
    assert np.arange(10)[Integer(3)] == 3
    assert list(np.arange(10)[Integer(2) : Integer(5)]) == [2, 3, 4]


def test_an_array_of_integers_keeps_an_integer_dtype():
    array = np.array([Integer(8), Integer(9)])
    assert array.dtype == np.int64
    assert array.sum() == 17


def test_integers_survive_numpy_arithmetic():
    assert np.int64(3) + Integer(4) == 7
    assert float(np.sqrt(Integer(16))) == 4.0
    assert np.gcd(Integer(12), Integer(18)) == 6


def test_rationals_fall_back_to_an_object_array():
    """NumPy has no exact-rational dtype, so it keeps the objects.

    This is the right answer rather than a gap: converting to
    ``float64`` would silently drop exactness, which is the one thing
    ER2 exists to keep.  An object array is slower, but ``1/3`` stays
    ``1/3``.  ``Integer`` needs none of this, because it subclasses
    ``int`` and NumPy already knows that dtype.
    """
    assert float(Rational(1, 2)) == 0.5
    exact = np.array([Rational(1, 2), Rational(1, 4)])
    assert exact.dtype == object
    assert list(exact) == [Rational(1, 2), Rational(1, 4)]
    assert str(exact[0]) == "1/2"
    # Mixed with floats the elements go through __rmul__ and land as
    # Python floats, still in an object array.
    scaled = np.array([1.0, 2.0]) * Rational(1, 2)
    assert scaled.dtype == object
    assert list(scaled) == [0.5, 1.0]
    # Ask for floats explicitly and NumPy gives a real dtype.
    assert np.array([1.0, 2.0]).astype(float).dtype == np.float64
    assert (np.array([1.0, 2.0]) * float(Rational(1, 2))).dtype == np.float64


def test_er2_numbers_keep_python_equality_and_hashing():
    """Libraries that use ER2 numbers as dict keys must see plain ints."""
    assert hash(Integer(5)) == hash(5)
    lookup = {5: "five"}
    assert lookup[Integer(5)] == "five"
    assert np.array([1, 2, 3]).tolist() == [Integer(1), Integer(2), 3]


def test_a_whole_er2_program_can_use_numpy(tmp_path):
    """The README's example, run the way a user would run it."""
    import subprocess
    import sys
    import textwrap

    program = tmp_path / "science.er2"
    program.write_text(
        textwrap.dedent(
            """
            import numpy as np
            print(np.zeros(2^3).shape)
            print(np.array([2^3, 3^2]).dtype)
            print(np.arange(5)[2^1])
            print(np.array([1.0, 2.0]) * (1/2))
            """
        ).lstrip(),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "er2", str(program)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    # The last line is an object array, so its elements print with
    # ER2's own repr: "1.0", not NumPy's "1.".
    assert result.stdout == "(8,)\nint64\n2\n[0.5 1.0]\n"
