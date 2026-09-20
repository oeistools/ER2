"""The dispatch table (ARCHITECTURE.md §3.4)."""

import pytest
import sympy

from er2 import dispatch, prelude
from er2.backends import pari_backend, sympy_backend
from er2.runtime.factorization import Factorization
from er2.runtime.numbers import Integer, Rational

x = sympy.Symbol("x")


def test_every_public_function_has_a_table_entry():
    assert set(dispatch.TABLE) == set(dispatch.FUNCTIONS)
    for name, function in dispatch.FUNCTIONS.items():
        assert callable(function)
        assert function.__name__ == name
        assert function.__doc__


def test_prelude_exposes_the_dispatching_functions():
    ns = prelude.namespace()
    assert set(prelude.FUNCTIONS) == set(dispatch.FUNCTIONS)
    for name, function in dispatch.FUNCTIONS.items():
        assert ns[name] is function


def test_every_pari_prelude_row_is_public():
    assert set(pari_backend.PRELUDE) <= set(dispatch.FUNCTIONS)


def test_factor_of_an_expression_uses_sympy():
    assert dispatch.factor(x**2 - 1) == (x - 1) * (x + 1)


@pytest.mark.parametrize(
    ("n", "text"),
    [
        (Integer(12), "2^2 * 3"),
        (12, "2^2 * 3"),
        (Rational(1, 12), "2^-2 * 3^-1"),
    ],
)
def test_factor_of_a_number_uses_pari(n, text):
    result = dispatch.factor(n)
    assert isinstance(result, Factorization)
    assert str(result) == text


def test_factor_of_a_sympy_number_uses_pari():
    assert str(dispatch.factor(sympy.Integer(12))) == "2^2 * 3"


def test_gcd_and_lcm_of_expressions_use_sympy():
    gcd, lcm = dispatch.FUNCTIONS["gcd"], dispatch.FUNCTIONS["lcm"]
    assert gcd(x**2 - 1, x**2 - 2 * x + 1) == x - 1
    assert lcm(x, x**2) == x**2
    assert gcd(Integer(12), 18) == 6 and type(gcd(12, 18)) is Integer


def test_unsupported_arguments_raise_type_error():
    with pytest.raises(TypeError, match=r"factor\(\) does not support"):
        dispatch.factor("12")


def test_univariate_polynomials_over_q_are_factored_by_pari():
    """Same result as SymPy, computed by PARI (M4)."""
    y = sympy.Symbol("y")
    cases = [
        x**2 - 1,
        1 - x**2,
        2 * x**2 - 2,
        x**2 / 4 - 1,
        x**6 - 1,
        7 * x**2 + 14 * x + 7,
        x**2 + 1,
        (x - sympy.Rational(1, 2)) ** 3,
    ]
    for p in cases:
        chosen = dispatch.implementation("factor", (p,), {})
        assert chosen is pari_backend.factor_polynomial
        assert dispatch.factor(p) == sympy.factor(p)
    # Multivariate, irrational coefficients, or options: SymPy.
    for args, kwargs in [
        ((x**2 - y**2,), {}),
        ((sympy.sqrt(2) * x**2 - 1,), {}),
        ((x**2 - 2,), {"extension": sympy.sqrt(2)}),
    ]:
        chosen = dispatch.implementation("factor", args, kwargs)
        assert chosen is sympy_backend.factor
    assert dispatch.factor(x**2 - 2, extension=sympy.sqrt(2)) == (
        x - sympy.sqrt(2)
    ) * (x + sympy.sqrt(2))


class TestMatrixDomainShortcut:
    """Dispatch reads SymPy's domain instead of scanning (§2.1).

    The shortcut is sound in one direction only, so these tests pin
    both: a ``ZZ``/``QQ`` domain proves the entries are rational, and
    any other domain proves nothing and must fall back to the scan.
    """

    def test_a_domain_of_z_or_q_is_recognised(self):
        assert dispatch.matrix_domain(
            sympy.Matrix([[1, 2], [3, 4]]), ("is_ZZ", "is_QQ")
        )
        assert dispatch.matrix_domain(
            sympy.Matrix([[sympy.Rational(1, 2)]]), ("is_ZZ", "is_QQ")
        )
        assert not dispatch.matrix_domain(
            sympy.Matrix([[sympy.Rational(1, 2)]]), ("is_ZZ",)
        )
        assert not dispatch.matrix_domain(
            sympy.Matrix([[sympy.sqrt(2)]]), ("is_ZZ", "is_QQ")
        )

    def test_a_rational_matrix_with_a_wider_domain_still_goes_to_pari(self):
        """The shortcut must not become the only test.

        Writing an integer into a symbolic matrix leaves SymPy's domain
        at ``EXRAW`` even though every entry is now rational.  Dispatch
        has to scan such a matrix and still choose PARI, or a matrix
        would take a different backend depending on how it was built.
        """
        matrix = sympy.Matrix([[sympy.sqrt(2), 0], [0, 1]])
        matrix[0, 0] = 2
        assert not dispatch.matrix_domain(matrix, ("is_ZZ", "is_QQ"))
        assert dispatch.rational_matrix((matrix,), {})
        chosen = dispatch.implementation("det", (matrix,), {})
        assert chosen is pari_backend.det
        assert dispatch.det(matrix) == 2
        assert pari_backend.to_pari(matrix) == pari_backend.to_pari(
            sympy.Matrix([[2, 0], [0, 1]])
        )

    @pytest.mark.parametrize("obj", [object(), None, 5, sympy.Symbol("z")])
    def test_an_object_without_a_domain_answers_no(self, obj):
        """``_rep`` is private, so the reader must not raise.

        Should SymPy rename it, ``matrix_domain`` answers False and the
        entry scan takes over: slower, same answer.  (A live SymPy
        matrix cannot be used to check that, because ``flat()`` reads
        ``_rep`` too.)
        """
        assert not dispatch.matrix_domain(obj, ("is_ZZ", "is_QQ"))

    @pytest.mark.parametrize(
        "entries",
        [
            [[1, 2], [3, 4]],
            [[sympy.Rational(1, 2), 2], [0, sympy.Rational(-3, 7)]],
            [[sympy.sqrt(2), 1], [1, 1]],
        ],
    )
    def test_conversion_agrees_with_the_general_route(self, entries):
        """Every domain route must build the same PARI matrix."""
        matrix = sympy.Matrix(entries)
        general = pari_backend.PARI.matrix(
            matrix.rows,
            matrix.cols,
            [pari_backend.to_pari(e) for e in matrix.flat()],
        )
        assert pari_backend.to_pari(matrix) == general
