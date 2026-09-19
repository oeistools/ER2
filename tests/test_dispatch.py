"""The dispatch table (ARCHITECTURE.md §3.4)."""

import pytest
import sympy

from er2 import dispatch, prelude
from er2.backends import pari_backend
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
