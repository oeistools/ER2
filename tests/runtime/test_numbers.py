"""Exact numbers and the compatibility contract (§1.1, D6)."""

import json
import math
from fractions import Fraction

import cypari2
import pytest
import sympy

from er2.runtime.numbers import Integer, Rational


def test_integer_is_an_int():
    n = Integer(5)
    assert isinstance(n, int)
    assert n == 5 and hash(n) == hash(5)
    assert {5: "ok"}[n] == "ok"
    assert repr(n) == "5" and str(n) == "5"


@pytest.mark.parametrize(
    ("value", "expected", "kind"),
    [
        (Integer(5) / 3, Fraction(5, 3), Rational),
        (Integer(6) / 3, 2, Integer),
        (1 / Integer(4), Fraction(1, 4), Rational),
        (Integer(2) ** -2, Fraction(1, 4), Rational),
        (2 ** Integer(-1), Fraction(1, 2), Rational),
        (Integer(2) ** 10, 1024, Integer),
        (Integer(7) // 2, 3, Integer),
        (Integer(7) % 2, 1, Integer),
        (-Integer(3), -3, Integer),
        (Integer(5) ^ 3, 6, Integer),
        (Integer(3) + 4, 7, Integer),
        (4 * Integer(3), 12, Integer),
        (Rational(1, 3) * 3, 1, Integer),
        (Rational(1, 3) + Rational(2, 3), 1, Integer),
        (Rational(1, 3) ** 2, Fraction(1, 9), Rational),
    ],
)
def test_exact_arithmetic(value, expected, kind):
    assert value == expected
    assert type(value) is kind


def test_floats_stay_floats():
    assert Integer(5) / 2.0 == 2.5
    assert isinstance(Rational(1, 2) + 0.5, float)


def test_divmod_and_pow_mod():
    assert divmod(Integer(7), 2) == (3, 1)
    assert all(type(v) is Integer for v in divmod(Integer(7), 2))
    assert pow(Integer(3), 4, 5) == 1


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        Integer(1) / 0


def test_rational_repr():
    assert repr(Rational(1, 3)) == "1/3"
    assert repr(Rational(-1, 3)) == "-1/3"


def test_python_interop():
    n = Integer(5)
    assert list(range(10))[n] == 5
    assert len(range(n)) == 5
    assert json.dumps([n]) == "[5]"
    assert f"{n:03d}" == "005"
    assert math.sqrt(Integer(16)) == 4.0
    assert float(Rational(1, 4)) == 0.25


def test_sympy_and_pari_interop():
    x = sympy.Symbol("x")
    assert x ** Integer(2) + Integer(2) * x == x**2 + 2 * x
    assert Rational(1, 3) * x == x / 3
    pari = cypari2.Pari()
    assert pari.eulerphi(Integer(123456789)) == 82260072
