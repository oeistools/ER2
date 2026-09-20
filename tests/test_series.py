"""Power series (M6, ARCHITECTURE.md §6 D18).

A power series is a SymPy expression with an ``O()`` term (D18), so
these tests are about the *dispatch*: ``expand`` of a product of series
goes to PARI, and must return what SymPy would have returned — with the
one deliberate exception D21 records, division, which SymPy's ``expand``
cannot do at all.  See ``TestDivisionIsDeliberatelyStrongerThanSymPy``.
"""

import random

import pytest
import sympy

from er2 import dispatch, prelude
from er2.backends import pari_backend, sympy_backend

x = sympy.Symbol("x")
y = sympy.Symbol("y")


def series(expr, n, var=x, point=0):
    return sympy.series(expr, var, point, n)


def random_series(rng, n, var=x):
    body = sum(sympy.Integer(rng.randint(-9, 9)) * var**k for k in range(n))
    return body + sympy.O(var**n)


class TestDispatch:
    """Only a univariate product of series around 0 goes to PARI."""

    @pytest.mark.parametrize(
        "expr",
        [
            series(sympy.exp(x), 6) * series(1 / (1 - x), 6),
            series(sympy.exp(x), 6) ** 3,
            series(sympy.sin(x), 4) * series(sympy.cos(x), 9),
            (1 + x + sympy.O(x**3)) * (1 - x + sympy.O(x**5)),
        ],
    )
    def test_a_series_product_goes_to_pari(self, expr):
        chosen = dispatch.implementation("expand", (expr,), {})
        assert chosen is pari_backend.expand_series

    @pytest.mark.parametrize(
        "expr",
        [
            x * (x + 1),  # no series at all
            series(sympy.exp(x), 6) + series(sympy.exp(x), 6),  # Add: done
            series(sympy.exp(x), 6),  # a bare series
            # Two variables: PARI's t_SER is univariate.
            (y + sympy.O(x**3)) * (1 + sympy.O(x**3)),
            # Around a point other than 0: to_pari refuses these.
            series(sympy.exp(x), 4, point=1)
            * series(sympy.exp(x), 4, point=1),
        ],
    )
    def test_everything_else_stays_with_sympy(self, expr):
        chosen = dispatch.implementation("expand", (expr,), {})
        assert chosen is sympy_backend.expand

    def test_options_stay_with_sympy(self):
        """``expand(expr, deep=False)`` is SymPy's contract, not PARI's."""
        expr = series(sympy.exp(x), 6) * series(1 / (1 - x), 6)
        chosen = dispatch.implementation("expand", (expr,), {"deep": False})
        assert chosen is sympy_backend.expand


class TestSameAnswerAsSymPy:
    """CLAUDE.md: the PARI route must return what SymPy returns."""

    @pytest.mark.parametrize("n", [2, 3, 5, 12, 25])
    def test_random_products_agree(self, n):
        rng = random.Random(20260920 + n)
        expand = prelude.namespace()["expand"]
        for _ in range(12):
            s, t = random_series(rng, n), random_series(rng, n)
            assert expand(s * t) == sympy.expand(s * t)

    @pytest.mark.parametrize(
        ("left", "right"),
        [(4, 9), (9, 3), (2, 7), (6, 6)],
    )
    def test_mixed_precisions_truncate_as_sympy_does(self, left, right):
        """The result's O() is the smaller of the two, in both routes."""
        expand = prelude.namespace()["expand"]
        s = series(sympy.exp(x), left)
        t = series(1 / (1 - x), right)
        result = expand(s * t)
        assert result == sympy.expand(s * t)
        assert result.getO() == sympy.O(x ** min(left, right))

    @pytest.mark.parametrize("power", [0, 1, 2, 3, 5])
    def test_powers_agree(self, power):
        expand = prelude.namespace()["expand"]
        s = series(sympy.exp(x), 6)
        assert expand(s**power) == sympy.expand(s**power)

    def test_a_nested_product_agrees(self):
        expand = prelude.namespace()["expand"]
        s, t = series(sympy.exp(x), 6), series(sympy.sin(x), 6)
        assert expand((s * t) ** 2) == sympy.expand((s * t) ** 2)
        assert expand(2 * s * t) == sympy.expand(2 * s * t)
        assert expand(s * t * x) == sympy.expand(s * t * x)


class TestTheFallback:
    """``expand_series`` must never give a different answer (§1.5)."""

    def test_an_unconvertible_leaf_falls_back_to_sympy(self):
        """The predicate cannot prove every leaf converts.

        A ``Mul`` whose factors include something PARI has no type for
        must still come back with SymPy's answer, not an exception.
        """
        expr = sympy.Symbol("z", positive=True) ** sympy.Rational(1, 2)
        product = (1 + x + sympy.O(x**3)) * expr
        assert pari_backend.expand_series(product) == sympy.expand(product)

    def test_the_fallback_is_used_and_not_merely_present(self, monkeypatch):
        """Force the PARI route to fail and check the answer survives."""

        def explode(node):
            raise TypeError("no PARI type for this")

        monkeypatch.setattr(pari_backend, "_series_tree", explode)
        s, t = series(sympy.exp(x), 6), series(1 / (1 - x), 6)
        assert pari_backend.expand_series(s * t) == sympy.expand(s * t)


def test_series_still_works_end_to_end():
    """The user-facing path, as a program would use it."""
    namespace = prelude.namespace()
    expand, series_of = namespace["expand"], namespace["series"]
    s = series_of(sympy.exp(x), x, 0, 5)
    t = series_of(1 / (1 - x), x, 0, 5)
    product = expand(s * t)
    # exp(x)/(1 - x) = sum_{n} (sum_{k<=n} 1/k!) x^n
    coefficients = [
        sum(sympy.Rational(1, sympy.factorial(k)) for k in range(m + 1))
        for m in range(5)
    ]
    expected = sum(c * x**m for m, c in enumerate(coefficients))
    assert product.removeO() == sympy.expand(expected)
    assert product.getO() == sympy.O(x**5)


class TestDivisionIsDeliberatelyStrongerThanSymPy:
    """D21: ER2's ``expand`` divides series; SymPy's cannot.

    This is the one place ER2's ``expand`` does not return what
    ``sympy.expand`` returns, and it is a decision (2026-09-20), not an
    accident.  SymPy is not giving a different answer — it declines to
    expand a quotient of series at all, leaving nested fractions.  Each
    test below therefore checks PARI's answer against
    ``sympy.series()`` of the equivalent expression, which is the
    mathematics both must agree with.
    """

    @pytest.mark.parametrize(
        ("quotient", "equivalent"),
        [
            (sympy.exp(x) / (1 / (1 - x)), sympy.exp(x) * (1 - x)),
            (1 / sympy.exp(x), sympy.exp(-x)),
            (sympy.sin(x) / sympy.exp(x), sympy.sin(x) * sympy.exp(-x)),
        ],
    )
    def test_a_quotient_is_the_series_of_the_quotient(
        self, quotient, equivalent
    ):
        expand = prelude.namespace()["expand"]
        n = 6
        numerator, denominator = sympy.fraction(sympy.together(quotient))
        built = series(numerator, n) / series(denominator, n)
        assert expand(built) == sympy.series(equivalent, x, 0, n)

    def test_inversion_is_the_reciprocal_series(self):
        expand = prelude.namespace()["expand"]
        s = series(sympy.exp(x), 6)
        assert expand(s**-1) == sympy.series(sympy.exp(-x), x, 0, 6)

    def test_sympy_expand_really_cannot_do_this(self):
        """Pin the premise of D21, so the decision can be revisited.

        If a future SymPy learns to expand a quotient of series, this
        test fails and D21 should be reconsidered rather than silently
        kept.
        """
        s, t = series(sympy.exp(x), 5), series(1 / (1 - x), 5)
        sympy_answer = sympy.expand(s / t)
        assert sympy_answer != sympy.series(sympy.exp(x) * (1 - x), x, 0, 5)
        # It leaves a sum of fractions rather than a series.
        assert sympy_answer.removeO().is_Add
        assert any(
            term.is_Mul and any(f.is_Pow and f.args[1] < 0 for f in term.args)
            for term in sympy_answer.removeO().args
        )


class TestGeneratingFunctions:
    """``generating_function`` joins a sequence to a series (M6 task 5)."""

    def test_an_ordinary_generating_function(self):
        generating_function = prelude.namespace()["generating_function"]
        got = generating_function([1, 1, 2, 3, 5, 8], x)
        expected = 1 + x + 2 * x**2 + 3 * x**3 + 5 * x**4 + 8 * x**5
        assert got.removeO() == sympy.expand(expected)
        assert got.getO() == sympy.O(x**6)

    def test_an_exponential_generating_function(self):
        """All-ones EGF is exp(x)."""
        generating_function = prelude.namespace()["generating_function"]
        got = generating_function([1] * 6, x, exponential=True)
        assert got == sympy.series(sympy.exp(x), x, 0, 6)

    def test_laplace_turns_an_egf_into_an_ogf(self):
        """``series_laplace`` is the bridge between the two kinds."""
        namespace = prelude.namespace()
        terms = [1, 1, 2, 6, 24]
        egf = namespace["generating_function"](terms, x, exponential=True)
        ogf = namespace["generating_function"](terms, x)
        assert namespace["series_laplace"](egf) == ogf

    def test_n_truncates_the_sequence(self):
        generating_function = prelude.namespace()["generating_function"]
        got = generating_function([1, 1, 2, 3, 5, 8, 13], x, 4)
        assert got.getO() == sympy.O(x**4)
        assert got.removeO() == sympy.expand(1 + x + 2 * x**2 + 3 * x**3)

    def test_an_empty_sequence_is_refused(self):
        generating_function = prelude.namespace()["generating_function"]
        with pytest.raises(ValueError, match="at least one term"):
            generating_function([], x)

    def test_the_fibonacci_generating_function_is_x_over_1_minus_x_minus_x2(
        self,
    ):
        """The point of M6 task 5, checked as mathematics.

        The generating function of the Fibonacci numbers is
        ``x/(1 - x - x^2)``, so multiplying the series by
        ``1 - x - x^2`` must leave ``x``.
        """
        namespace = prelude.namespace()
        fibonacci = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        f = namespace["generating_function"](fibonacci, x)
        product = namespace["expand"](f * (1 - x - x**2))
        assert product.removeO() == x

    def test_it_accepts_anything_iterable(self):
        """A list, a tuple or a generator: sequences come in many shapes."""
        generating_function = prelude.namespace()["generating_function"]
        expected = generating_function([1, 2, 3], x)
        assert generating_function((1, 2, 3), x) == expected
        assert generating_function(iter([1, 2, 3]), x) == expected
        assert generating_function(range(1, 4), x) == expected
