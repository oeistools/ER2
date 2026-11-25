"""Rational ``+ - * /`` fast path: same results as ``fractions.Fraction``."""

import operator
import random
from fractions import Fraction

import pytest

from er2.runtime.numbers import Integer, Rational

OPS = [operator.add, operator.sub, operator.mul, operator.truediv]


def er2_value(x):
    """Return the ER2 number for an ``int`` or ``Fraction``."""
    if isinstance(x, Fraction):
        if x.denominator == 1:
            return Integer(x.numerator)
        return Rational(x.numerator, x.denominator)
    return Integer(x)


def same(result, expected):
    """Check the value and the ER2 type (Integer when integral)."""
    assert result == expected
    if expected.denominator == 1:
        assert type(result) is Integer
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
            same(op(er2_value(x), er2_value(y)), op(Fraction(x), Fraction(y)))


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
