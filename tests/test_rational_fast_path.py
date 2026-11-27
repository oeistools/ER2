"""Rational ``+ - * /`` fast path: same results as ``fractions.Fraction``."""

import operator
import random
from fractions import Fraction

import pytest

from er2.runtime.numbers import Integer, Rational, exact_div

OPS = [operator.add, operator.sub, operator.mul, operator.truediv]


def er2_value(x):
    """Return the ER2 number for an ``int`` or ``Fraction``."""
    if isinstance(x, Fraction):
        if x.denominator == 1:
            return int(x.numerator)
        return Rational(x.numerator, x.denominator)
    return int(x)  # an ER2 integer is a plain int (D22)


def same(result, expected):
    """Check the value and the ER2 type (Integer when integral)."""
    assert result == expected
    if expected.denominator == 1:
        assert type(result) is int
    else:
        assert type(result) is Rational
        assert result.denominator > 0


@pytest.mark.parametrize("op", OPS, ids=lambda f: f.__name__)
def test_random_operations_match_fraction(op):
    rng = random.Random(2026)
    for _ in range(3000):
        a = Fraction(rng.randint(-(10**6), 10**6), rng.randint(1, 10**4))
        b = Fraction(rng.randint(-(10**6), 10**6), rng.randint(1, 10**4))
        k = rng.randint(-50, 50)
        for x, y in ((a, b), (a, k), (k, a)):
            if op is operator.truediv and y == 0:
                continue
            # in ER2 source ``/`` is the exact call (D22)
            er2_op = exact_div if op is operator.truediv else op
            same(
                er2_op(er2_value(x), er2_value(y)),
                op(Fraction(x), Fraction(y)),
            )


def test_plain_int_and_float_operands():
    half = Rational(1, 2)
    same(half + 3, Fraction(7, 2))
    same(3 - half, Fraction(5, 2))
    same(half * 2, Fraction(1))
    assert half + 0.25 == 0.75 and isinstance(half + 0.25, float)
    assert 0.5 * half == 0.25


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        Rational(1, 3) / 0
    with pytest.raises(ZeroDivisionError):
        Integer(1) / Rational(0, 1)


def _random_rationals(rng, count):
    for _ in range(count):
        yield (
            Fraction(rng.randint(-(10**6), 10**6), rng.randint(1, 10**4)),
            Fraction(rng.randint(-(10**6), 10**6), rng.randint(1, 10**4)),
            rng.randint(-50, 50),
        )


@pytest.mark.parametrize(
    "op", [operator.floordiv, operator.mod], ids=lambda f: f.__name__
)
def test_floordiv_and_mod_match_fraction(op):
    for a, b, k in _random_rationals(random.Random(7), 2000):
        for x, y in ((a, b), (a, k), (k, a)):
            if y == 0:
                continue
            expected = op(Fraction(x), Fraction(y))
            result = op(er2_value(x), er2_value(y))
            assert result == expected
            assert type(result) is (
                int if expected.denominator == 1 else Rational
            )


def test_power_negation_and_abs_match_fraction():
    for a, _, k in _random_rationals(random.Random(11), 2000):
        x = er2_value(a)
        if not isinstance(x, Rational):
            continue
        e = k % 13 - 6  # exponents -6 .. 6
        if a or e >= 0:
            same(x**e, a**e)
        same(-x, -a)
        same(abs(x), abs(a))
        assert +x is x
    assert Rational(1, 4) ** 0.5 == 0.5  # other exponents: Fraction's way
    assert Rational(1, 4) ** Rational(1, 2) == 0.5
    with pytest.raises(ZeroDivisionError):
        Rational(1, 3) // 0
    with pytest.raises(ZeroDivisionError):
        Rational(1, 3) % 0
