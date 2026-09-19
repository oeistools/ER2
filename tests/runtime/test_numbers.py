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


def test_divmod_with_other_number_types():
    # int.__divmod__ returns NotImplemented for these; Python then asks
    # the other operand instead of failing.
    assert divmod(Integer(7), Rational(1, 3)) == (21, 0)
    assert divmod(Integer(2), 7.5) == (0.0, 2.0)
    q, r = divmod(Rational(7, 2), Rational(1, 3))
    assert (q, r) == (10, Rational(1, 6))
    assert type(q) is Integer and type(r) is Rational
    assert all(type(v) is Integer for v in divmod(7, Rational(2, 1)))


def test_rounding_stays_exact():
    """``floor``, ``ceil``, ``trunc`` and ``round`` return ER2 numbers."""
    half = Rational(7, 2)
    for result, expected in (
        (math.floor(half), 3),
        (math.ceil(half), 4),
        (math.trunc(-half), -3),
        (round(half), 4),
        (math.floor(Integer(7)), 7),
        (round(Integer(17), -1), 20),
    ):
        assert result == expected and type(result) is Integer
    assert math.floor(half) / 2 == Rational(3, 2)
    assert round(Rational(7, 3), 1) == Rational(23, 10)
    assert type(round(Rational(7, 3), 1)) is Rational


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


def test_literals_are_created_once():
    """The preparser's literal helper caches immutable Integers (M4)."""
    from er2 import prelude, preparser

    literal = prelude.namespace()[preparser.INTEGER]
    five = literal(5)
    assert type(five) is Integer and five == 5
    assert literal(5) is five
    assert type(literal(10**30)) is Integer


def test_operators_return_integer():
    a, b = Integer(7), Integer(3)
    for result in (
        a + b,
        a - b,
        a * b,
        a // b,
        a % b,
        -a,
        +a,
        abs(-a),
        ~a,
        a & b,
        a | b,
        a ^ b,
        a << b,
        a >> b,
        3 + a,
        3 - a,
        3 * a,
        3 // a,
        3 % a,
        3 & a,
        3 | a,
        3 ^ a,
        3 << a,
        3 >> a,
    ):
        assert type(result) is Integer
    assert a + 0.5 == 7.5 and type(a + 0.5) is float
    assert (a + True) == 8 and type(a + True) is Integer


def test_raw_literals_are_plain_ints():
    """``5r`` gives a Python ``int`` (§1.1); ``5`` gives an ``Integer``."""
    from er2 import prelude
    from er2.preparser import preparse

    ns = prelude.namespace()
    exec(preparse("a = 5r\nb = 5\nc = 5r / 2\nd = f'{2^3=}'\n"), ns)
    assert type(ns["a"]) is int and type(ns["b"]) is Integer
    assert ns["c"] == 2.5  # Python's true division
    assert ns["d"] == "2^3=8"
