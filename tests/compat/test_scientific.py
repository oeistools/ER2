"""ER2 numbers cross into the scientific stack (ARCHITECTURE.md §1.1).

The README promises that the whole ecosystem works through a normal
import and names NumPy, SciPy, pandas and Matplotlib.  That promise rests
on ``Integer`` subclassing ``int`` and on the contract in §1.1 point 5
(``__index__``, ``__float__``, ``__hash__``, ...).  ER2 wraps none of
these libraries: these tests guard interoperability ER2 already has, so
that a change to the number types cannot silently break it.

None of them is a runtime dependency (CLAUDE.md keeps that to ``sympy``
and ``cypari2``); they are in the dev group, so CI runs these tests.
**Each library is skipped on its own**, through a fixture rather than a
module-level ``importorskip``: one placed mid-module aborts the import
and takes every test in the file with it, including the ones that do not
need that library.  NumPy is the exception and is guarded at module
level, because Matplotlib, pandas and SciPy all require it anyway.

One asymmetry runs through the whole file, and it is deliberate.
``Integer`` is an ``int``, so every library gives it a real integer
dtype.  ``Rational`` is not a machine number: NumPy and pandas keep it in
an object array (exactly, arithmetic included) and SciPy's ufuncs reject
it outright.  A ``float64`` conversion would silently drop the exactness
ER2 exists to keep, so the user asks for ``float(...)`` when they want
speed.
"""

import pytest

from er2.runtime.numbers import Integer, Rational

np = pytest.importorskip("numpy", reason="NumPy is an optional test extra")


# --------------------------------------------------------------------
# NumPy
# --------------------------------------------------------------------
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


# --------------------------------------------------------------------
# Matplotlib (ARCHITECTURE §1.3): a paper needs plots, and the numbers
# that go into them are ER2 numbers.
# --------------------------------------------------------------------
@pytest.fixture
def axes():
    """Return a throwaway Agg figure, skipped without Matplotlib."""
    mpl = pytest.importorskip("matplotlib", reason="Matplotlib is optional")
    mpl.use("Agg")
    plt = pytest.importorskip("matplotlib.pyplot")
    figure, ax = plt.subplots()
    yield ax
    plt.close(figure)


def test_er2_numbers_plot(axes):
    """``Integer`` and ``Rational`` work as coordinates."""
    xs = [Integer(k) for k in range(1, 8)]
    ys = [Integer(k) ** 2 for k in range(1, 8)]
    (line,) = axes.plot(xs, ys)
    assert list(line.get_ydata()) == [1, 4, 9, 16, 25, 36, 49]
    (exact,) = axes.plot([Rational(1, 2), Rational(3, 2)], [Rational(1, 4), 2])
    assert list(exact.get_xdata()) == [0.5, 1.5]


def test_a_tex_string_is_a_usable_label(axes):
    """``latex()`` returns a ``str``, so Matplotlib renders it as math."""
    from er2.printing import latex

    body = latex(Rational(7, 3))
    assert isinstance(body, str)
    axes.set_xlabel(f"${body}$")
    assert axes.get_xlabel() == r"$\frac{7}{3}$"


def test_a_figure_with_er2_values_saves(tmp_path, axes):
    """The whole path a figure in an article takes."""
    axes.plot([Integer(1), Integer(2)], [Rational(1, 2), Rational(3, 2)])
    target = tmp_path / "figure.png"
    axes.figure.savefig(target, dpi=50)
    assert target.stat().st_size > 0


# --------------------------------------------------------------------
# pandas
# --------------------------------------------------------------------
@pytest.fixture
def pd():
    """Return the pandas module, skipped when it is absent."""
    return pytest.importorskip("pandas", reason="pandas is optional")


def test_a_column_of_integers_keeps_an_integer_dtype(pd):
    """``Integer`` is an ``int``, so pandas gives it a real dtype."""
    series = pd.Series([Integer(1), Integer(2), Integer(3)])
    assert series.dtype == "int64"
    assert series.sum() == 6
    frame = pd.DataFrame({"n": [Integer(10), Integer(20)]})
    assert frame["n"].dtype == "int64"
    assert frame["n"].max() == 20


def test_a_column_of_rationals_stays_exact(pd):
    """Rationals stay objects in pandas, and the arithmetic is exact.

    This is the NumPy asymmetry again, and here it pays off visibly:
    summing 1/2 and 1/3 in an object column gives 5/6, not
    0.8333333333333333.
    """
    series = pd.Series([Rational(1, 2), Rational(1, 3)])
    assert series.dtype == object
    assert series.iloc[0] == Rational(1, 2)
    total = series.sum()
    assert total == Rational(5, 6)
    assert isinstance(total, Rational)


def test_integers_index_and_label(pd):
    """``Integer`` works both positionally and as an index label."""
    frame = pd.DataFrame({"n": [Integer(10), Integer(20), Integer(30)]})
    assert frame["n"].iloc[Integer(1)] == 20
    labelled = pd.Series([5, 6], index=[Integer(1), Integer(2)])
    assert labelled.loc[Integer(2)] == 6


# --------------------------------------------------------------------
# SciPy
# --------------------------------------------------------------------
@pytest.fixture
def scipy_special():
    """Return ``scipy.special``, skipped when SciPy is absent."""
    return pytest.importorskip("scipy.special", reason="SciPy is optional")


def test_integers_pass_into_scipy(scipy_special):
    """SciPy accepts ``Integer`` as an argument and as a size."""
    assert scipy_special.gamma(Integer(5)) == 24.0
    assert scipy_special.factorial(Integer(5)) == 120.0
    assert scipy_special.comb(Integer(10), Integer(3), exact=True) == 120
    sparse = pytest.importorskip("scipy.sparse")
    assert sparse.csr_matrix((Integer(2), Integer(3))).shape == (2, 3)


def test_scipy_answers_in_floating_point(scipy_special):
    """SciPy is numeric: ER2 numbers go in, machine floats come out.

    That is §5.3 of docs/LANGUAGE.md, not a defect — a library returns
    its own values.  ER2's own functions are the exact counterparts, and
    a program picks whichever it needs.
    """
    from er2.dispatch import FUNCTIONS

    scipy_value = scipy_special.comb(Integer(10), Integer(3))
    assert isinstance(scipy_value, float)
    exact = FUNCTIONS["binomial"](Integer(10), Integer(3))
    assert isinstance(exact, Integer)
    assert exact == 120 == int(scipy_value)


def test_rationals_are_rejected_by_scipy_ufuncs(scipy_special):
    """A ``Rational`` is not a machine number, and SciPy says so.

    NumPy falls back to an object array; a SciPy ufunc has no such
    fallback and raises.  The escape hatch is the documented one:
    ``float(...)`` when the exactness is no longer needed.
    """
    with pytest.raises(TypeError):
        scipy_special.gamma(Rational(1, 2))
    # gamma(1/2) is sqrt(pi), so squaring it comes back to pi.
    assert scipy_special.gamma(float(Rational(1, 2))) ** 2 == pytest.approx(
        3.141592653589793
    )


def test_scipy_uses_er2_numbers_as_bracket_and_data(scipy_special):
    """A root find and a linear solve, both fed ER2 numbers."""
    optimize = pytest.importorskip("scipy.optimize")
    linalg = pytest.importorskip("scipy.linalg")
    root = optimize.brentq(
        lambda t: t * t - Integer(2), Integer(0), Integer(2)
    )
    assert root == pytest.approx(2**0.5)
    matrix = np.array([[Integer(1), Integer(2)], [Integer(3), Integer(4)]])
    assert linalg.det(matrix) == pytest.approx(-2.0)
