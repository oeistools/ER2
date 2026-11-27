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
        (Integer(6) / 3, 2, int),
        (1 / Integer(4), Fraction(1, 4), Rational),
        (Integer(2) ** -2, Fraction(1, 4), Rational),
        (2 ** Integer(-1), Fraction(1, 2), Rational),
        (Integer(2) ** 10, 1024, int),
        (Integer(7) // 2, 3, Integer),
        (Integer(7) % 2, 1, Integer),
        (-Integer(3), -3, Integer),
        (Integer(5) ^ 3, 6, Integer),
        (Integer(3) + 4, 7, Integer),
        (4 * Integer(3), 12, Integer),
        (Rational(1, 3) * 3, 1, int),
        (Rational(1, 3) + Rational(2, 3), 1, int),
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
    assert all(type(v) is int for v in divmod(Integer(7), 2))
    assert pow(Integer(3), 4, 5) == 1


def test_divmod_with_other_number_types():
    # int.__divmod__ returns NotImplemented for these; Python then asks
    # the other operand instead of failing.
    assert divmod(Integer(7), Rational(1, 3)) == (21, 0)
    assert divmod(Integer(2), 7.5) == (0.0, 2.0)
    q, r = divmod(Rational(7, 2), Rational(1, 3))
    assert (q, r) == (10, Rational(1, 6))
    assert type(q) is int and type(r) is Rational
    assert all(type(v) is int for v in divmod(7, Rational(2, 1)))


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
        assert result == expected and isinstance(result, int)
    assert math.floor(half) / 2 == Rational(3, 2)
    assert round(Rational(7, 3), 1) == Rational(23, 10)
    assert type(round(Rational(7, 3), 1)) is Rational


def test_integer_divided_by_other_numbers():
    for result, expected, kind in (
        (Integer(1) / Rational(1, 2), 2, int),
        (Integer(3) / Rational(2, 5), Rational(15, 2), Rational),
        (Integer(3) / 0.5, 6.0, float),
        (1.5 / Integer(3), 0.5, float),
    ):
        assert result == expected and type(result) is kind


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        Integer(1) / 0
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        1 / Integer(0)


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
    """``__er2_int__`` stays bound and gives a plain ``int`` (D22).

    The preparser no longer wraps literals in it; old preparsed code
    that calls it still runs, and gets the same ``int`` the literal is.
    """
    from er2 import prelude, preparser

    literal = prelude.namespace()[preparser.INTEGER]
    five = literal(5)
    assert type(five) is int and five == 5
    assert literal(5) is five
    assert type(literal(10**30)) is int


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


@pytest.mark.filterwarnings("ignore:.*is deprecated:FutureWarning")
def test_raw_literals_are_plain_ints():
    """``5r`` and ``5`` are both a Python ``int`` (D22).

    Since D22 every integer literal is a plain ``int`` and ``/`` is exact
    between integers wherever it is written, so ``5r`` is still accepted
    but no longer changes anything: ``5r / 2r`` is ``5/2``.
    """
    from er2 import prelude
    from er2.preparser import compile_er2, preparse

    ns = prelude.namespace()
    source = "a = 5r\nb = 5\nc = 5r / 2r\nd = 5r / 2\ne = f'{2^3=}'\n"
    exec(compile_er2(preparse(source), "<test>"), ns)
    assert type(ns["a"]) is int and type(ns["b"]) is int
    assert ns["c"] == Rational(5, 2) and type(ns["c"]) is Rational
    assert ns["d"] == Rational(5, 2) and type(ns["d"]) is Rational
    assert ns["e"] == "2^3=8"


def test_exact_div_and_pow():
    """§3.7 R2, R3: the calls ``/`` and ``**`` compile to."""
    import sympy

    from er2.runtime.numbers import exact_div, exact_pow

    assert exact_div(1, 3) == Rational(1, 3)
    assert exact_div(6, 3) == 2 and type(exact_div(6, 3)) is int
    assert exact_div(Rational(1, 2), 2) == Rational(1, 4)
    assert exact_div(1, 0.5) == 2.0 and type(exact_div(1, 0.5)) is float
    x = sympy.Symbol("x")
    assert exact_div(x, 2) == x / 2
    with pytest.raises(ZeroDivisionError):
        exact_div(1, 0)
    assert exact_pow(2, -2) == Rational(1, 4)
    assert exact_pow(Rational(2, 3), -1) == Rational(3, 2)
    assert exact_pow(2, 10) == 1024 and type(exact_pow(2, 10)) is int
    assert exact_pow(2.0, -1) == 0.5
