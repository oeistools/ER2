"""Dirichlet series and Euler products (M6, D19).

Expected coefficients are the classical arithmetic functions, so the
tests check the mathematics rather than PARI's output: ``zeta * (1/zeta)``
is 1, ``1/zeta`` has the Moebius coefficients, and ``zeta^2`` has the
number of divisors.
"""

import pytest

from er2 import prelude
from er2.runtime.dirichlet import DirichletSeries
from er2.runtime.numbers import Integer

TERMS = 24


def reciprocal_zeta(p, local):
    """Return the Euler factor of 1/zeta(s): 1 - p^{-s}."""
    return 1 - local


def zeta_factor(p, local):
    """Return the Euler factor of zeta(s): 1/(1 - p^{-s})."""
    return 1 / (1 - local)


def divisor_count_factor(p, local):
    """Return the Euler factor of zeta(s)^2, whose a_n is d(n)."""
    return 1 / (1 - local) ** 2


@pytest.fixture
def zeta():
    return DirichletSeries([1] * TERMS)


class TestConstruction:
    def test_it_holds_er2_numbers_not_pari_objects(self, zeta):
        """M4: no PARI object outlives the call that made it."""
        import cypari2

        for value in zeta.coefficients:
            assert not isinstance(value, cypari2.gen.Gen)
            assert isinstance(value, int)

    def test_it_is_indexed_from_one(self, zeta):
        """D19: ``a[5]`` in a list would be a_6; here a_5 is a_5."""
        assert zeta[1] == 1
        assert zeta[TERMS] == 1
        with pytest.raises(IndexError):
            zeta[0]
        with pytest.raises(IndexError):
            zeta[TERMS + 1]

    def test_it_rejects_what_is_not_an_index(self, zeta):
        with pytest.raises(TypeError):
            zeta[1:3]
        with pytest.raises(TypeError):
            zeta["1"]

    def test_an_empty_series_is_refused(self):
        with pytest.raises(ValueError, match="at least"):
            DirichletSeries([])

    def test_length_and_iteration(self, zeta):
        assert len(zeta) == TERMS
        assert zeta.terms == TERMS
        assert list(zeta) == [1] * TERMS


class TestTheMathematics:
    def test_zeta_times_its_inverse_is_one(self, zeta):
        """The identity Dirichlet series: a_1 = 1, everything else 0."""
        mu = DirichletSeries.euler(reciprocal_zeta, TERMS)
        product = zeta * mu
        assert product[1] == 1
        assert all(product[n] == 0 for n in range(2, TERMS + 1))

    def test_the_inverse_of_zeta_has_moebius_coefficients(self):
        mu = DirichletSeries.euler(reciprocal_zeta, TERMS)
        namespace = prelude.namespace()
        for n in range(1, TERMS + 1):
            assert mu[n] == namespace["mu"](Integer(n))

    def test_dividing_by_zeta_agrees_with_the_euler_product(self, zeta):
        """Two routes to 1/zeta: ``dirdiv`` and ``direuler``."""
        identity = DirichletSeries([1] + [0] * (TERMS - 1))
        assert identity / zeta == DirichletSeries.euler(reciprocal_zeta, TERMS)

    def test_zeta_squared_counts_divisors(self, zeta):
        namespace = prelude.namespace()
        squared = zeta * zeta
        by_euler = DirichletSeries.euler(divisor_count_factor, TERMS)
        for n in range(1, TERMS + 1):
            expected = namespace["numdiv"](Integer(n))
            assert squared[n] == expected
            assert by_euler[n] == expected

    def test_the_euler_product_of_zeta_is_zeta(self, zeta):
        assert DirichletSeries.euler(zeta_factor, TERMS) == zeta

    def test_addition_and_subtraction_are_coefficientwise(self, zeta):
        doubled = zeta + zeta
        assert all(doubled[n] == 2 for n in range(1, TERMS + 1))
        assert all((zeta - zeta)[n] == 0 for n in range(1, TERMS + 1))


class TestTruncation:
    def test_an_operation_truncates_to_the_shorter_operand(self):
        short = DirichletSeries([1] * 5)
        long = DirichletSeries([1] * 20)
        assert len(short * long) == 5
        assert len(long * short) == 5
        assert len(short + long) == 5
        assert len(long / short) == 5


class TestPrinting:
    def test_zeta_reads_as_a_dirichlet_series(self, zeta):
        assert repr(zeta) == "1 + 2^-s + 3^-s + 4^-s + 5^-s + ...  (24 terms)"

    def test_negative_coefficients_print_with_a_minus(self):
        """``1 + -2^-s`` must never appear."""
        mu = DirichletSeries.euler(reciprocal_zeta, TERMS)
        assert repr(mu).startswith("1 - 2^-s - 3^-s - 5^-s")
        assert "+ -" not in repr(mu)
        assert "+ -" not in mu._latex()

    def test_an_ellipsis_means_something_was_left_out(self, zeta):
        """``zeta * (1/zeta)`` is 1, and must not print ``1 + ...``."""
        mu = DirichletSeries.euler(reciprocal_zeta, TERMS)
        assert repr(zeta * mu) == "1  (24 terms)"
        assert (zeta * mu)._latex() == "1"
        assert "..." in repr(zeta)

    def test_a_coefficient_other_than_one_is_shown(self):
        divisors = DirichletSeries.euler(divisor_count_factor, 12)
        assert repr(divisors).startswith("1 + 2*2^-s + 2*3^-s + 3*4^-s")
        assert r"2 \cdot 2^{-s}" in divisors._latex()

    def test_latex_renders_as_math(self, zeta):
        assert zeta._repr_latex_() == f"${zeta._latex()}$"

    def test_a_zero_series_prints_as_zero(self):
        assert repr(DirichletSeries([0, 0])) == "0  (2 terms)"


class TestEqualityAndHashing:
    def test_equal_coefficients_mean_equal_series(self):
        assert DirichletSeries([1, 2, 3]) == DirichletSeries([1, 2, 3])
        assert DirichletSeries([1, 2, 3]) != DirichletSeries([1, 2, 4])
        assert DirichletSeries([1, 2]) != DirichletSeries([1, 2, 3])

    def test_it_hashes_with_its_equality(self):
        assert hash(DirichletSeries([1, 2])) == hash(DirichletSeries([1, 2]))
        assert len({DirichletSeries([1, 2]), DirichletSeries([1, 2])}) == 1

    def test_it_does_not_compare_equal_to_a_list(self):
        assert DirichletSeries([1, 2]) != [1, 2]


class TestNumericEulerProducts:
    def test_the_euler_product_for_zeta_of_two(self):
        """Prod 1/(1 - p^-2) over p converges to pi^2/6."""
        from er2.backends import pari_backend

        namespace = prelude.namespace()
        value = pari_backend.euler_product(
            lambda p: 1 / (1 - p ** Integer(-2)), 2, 100000
        )
        assert (
            abs(float(value) - float(namespace["pi"].evalf(20)) ** 2 / 6)
            < 1e-5
        )


def test_the_prelude_exposes_the_type():
    assert prelude.namespace()["DirichletSeries"] is DirichletSeries
