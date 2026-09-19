"""The SymPy backend and its conversion boundary (§3.4, §3.7).

Expected values were computed with SymPy 1.14.
"""

import pytest
import sympy

from er2 import dispatch
from er2.backends.sympy_backend import from_sympy, to_sympy
from er2.runtime.numbers import Integer, Rational

x, y = sympy.symbols("x y")


def test_to_sympy_converts_numbers_and_containers():
    assert to_sympy(Integer(5)) == sympy.Integer(5)
    assert isinstance(to_sympy(Integer(5)), sympy.Integer)
    assert isinstance(to_sympy(7), sympy.Integer)
    assert to_sympy(Rational(1, 3)) == sympy.Rational(1, 3)
    assert to_sympy((x, Integer(0), Integer(1))) == (x, 0, 1)
    assert isinstance(to_sympy([Integer(1)])[0], sympy.Integer)
    assert to_sympy({x: Integer(2)}) == {x: sympy.Integer(2)}
    assert to_sympy(True) is True
    assert to_sympy(x) is x


def test_from_sympy_converts_numbers_and_containers():
    assert type(from_sympy(sympy.Integer(-4))) is Integer
    assert type(from_sympy(sympy.S.One)) is Integer
    assert from_sympy(sympy.Rational(2, 6)) == Rational(1, 3)
    assert type(from_sympy(sympy.Rational(1, 3))) is Rational
    assert [type(v) for v in from_sympy([sympy.Integer(1), x])] == [
        Integer,
        sympy.Symbol,
    ]
    assert type(from_sympy({x: sympy.Integer(2)})[x]) is Integer
    assert from_sympy(sympy.pi) is sympy.pi
    assert from_sympy(sympy.oo) is sympy.oo


def test_round_trip():
    for value in (Integer(0), Integer(-7), Integer(2**200), Rational(-5, 3)):
        back = from_sympy(to_sympy(value))
        assert back == value and type(back) is type(value)


f = x**2 + 2 * x + 1


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda: dispatch.expand((x + 1) ** 2), f),
        (lambda: dispatch.factor(f), (x + 1) ** 2),
        (
            lambda: dispatch.factor(x**4 - 1),
            (x - 1) * (x + 1) * (x**2 + 1),
        ),
        (
            lambda: dispatch.factor(x**2 * y - y**3),
            y * (x - y) * (x + y),
        ),
        (lambda: dispatch.simplify(sympy.sin(x) ** 2 + sympy.cos(x) ** 2), 1),
        (
            lambda: dispatch.collect(x * y + x + 2 * x**2 - x**2 * y, x),
            x**2 * (2 - y) + x * (y + 1),
        ),
        (lambda: dispatch.cancel((x**2 - 1) / (x - 1)), x + 1),
        (lambda: dispatch.diff(x**3, x), 3 * x**2),
        (lambda: dispatch.diff(x**3, x, Integer(2)), 6 * x),
        (lambda: dispatch.diff(x**2 * y, x, y), 2 * x),
        (lambda: dispatch.integrate(f, x), x**3 / 3 + x**2 + x),
        (lambda: dispatch.limit(sympy.sin(x) / x, x, Integer(0)), 1),
        (lambda: dispatch.limit(1 / x, x, sympy.oo), 0),
        (lambda: dispatch.limit(1 / x, x, 0, dir="-"), -sympy.oo),
        (lambda: dispatch.solve(x**2 - 4, x), [-2, 2]),
        (
            lambda: dispatch.solve(sympy.Eq(x**2, 2), x),
            [-sympy.sqrt(2), sympy.sqrt(2)],
        ),
        (
            lambda: dispatch.series(sympy.sin(x), x, 0, 6),
            x - x**3 / 6 + x**5 / 120 + sympy.O(x**6),
        ),
    ],
)
def test_cas_values(call, expected):
    assert call() == expected


def test_exact_results_are_er2_numbers():
    area = dispatch.integrate(f, (x, Integer(0), Integer(1)))
    assert area == Rational(7, 3) and type(area) is Rational
    assert type(dispatch.diff(f, x, 2)) is Integer
    roots = dispatch.solve(3 * x - 1, x)
    assert roots == [Rational(1, 3)] and type(roots[0]) is Rational
    assert type(dispatch.expand(Integer(5))) is Integer
    solution = dispatch.solve([x + y - 3, x - y - 1], [x, y], dict=True)
    assert solution == [{x: 2, y: 1}]
    assert type(solution[0][x]) is Integer
