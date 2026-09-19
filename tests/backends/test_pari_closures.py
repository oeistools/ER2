"""PARI functions that take Python callables (the ``wrapper`` rows).

Expected values were computed with cypari2 (PARI 2.17.2).
"""

import csv
from pathlib import Path

import pytest
import sympy

from er2.backends import pari_closures
from er2.backends.pari_backend import pari
from er2.runtime.numbers import Integer, Rational

TABLE = Path(__file__).resolve().parents[2] / "er2/data/pari_functions.csv"
x = sympy.Symbol("x")
EPS = sympy.Float("1e-30")


def close(value, expected):
    return abs(value - expected) < EPS


def test_every_wrapper_row_has_a_signature():
    with TABLE.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["status"] == "wrapper"]
    assert {r["er2_name"] for r in rows} == set(pari_closures.SIGNATURES)
    for row in rows:
        function = getattr(pari, row["er2_name"])
        assert callable(function) and "f" in function.__doc__


def test_exact_sums_and_products():
    total = pari.sum(lambda n: 1 / n**2, 1, 10)
    assert total == Rational(1968329, 1270080) and type(total) is Rational
    assert pari.prod(lambda n: 1 + Rational(1, n), 1, 9) == 10
    assert pari.sumdiv(12, lambda d: d**2) == 210
    assert pari.sumdivmult(12, lambda d: d) == 28
    assert pari.vectorv(4, lambda k: k**2) == [1, 4, 9, 16]
    assert pari.vectorsmall(3, lambda k: 2 * k) == [2, 4, 6]
    assert pari.sum(lambda n: x**n, 0, 3) == x**3 + x**2 + x + 1


def test_callables_receive_er2_values():
    seen = []
    pari.sum(lambda n: seen.append(type(n)) or 0, 1, 2)
    assert seen == [Integer, Integer]


def test_numerical_functions_use_er2_precision():
    zeta2 = (sympy.pi**2 / 6).evalf(40)
    assert close(pari.sumpos(lambda n: Rational(1, n**2), 1), zeta2)
    assert close(pari.sumnum(lambda n: 1 / n**2, 1), zeta2)
    assert close(pari.intnum(lambda t: t**2, 0, 1), sympy.Rational(1, 3))
    assert close(pari.intnum(lambda t: pari.exp(-t), 0, [sympy.oo, 1]), 1)
    assert close(pari.solve(lambda t: t**2 - 2, 1, 2), sympy.sqrt(2).evalf(40))
    assert close(pari.derivnum(lambda t: t**3, 2), 12)
    assert close(
        pari.sumalt(lambda n: (-1) ** n / n, 1), -sympy.log(2).evalf(40)
    )
    assert close(pari.intcirc(lambda z: 1 / z, 0, 1), 1)
    assert close(
        pari.intnumosc(lambda t: pari.sin(t) / t, 0, sympy.pi),
        (sympy.pi / 2).evalf(40),
    )


def test_euler_products_and_dirichlet_series():
    assert pari.direuler(lambda p, t: 1 / (1 - t), 2, 10) == [1] * 10
    # sum of d(n) n^-s = zeta(s)^2: coefficients d(1..6)
    square = pari.direuler(lambda p, t: 1 / (1 - t) ** 2, 2, 6)
    assert square == [1, 2, 2, 3, 2, 4]
    euler = pari.prodeuler(lambda p: 1 / (1 - Rational(1, p**2)), 2, 10**4)
    assert abs(euler - (sympy.pi**2 / 6).evalf(40)) < 1e-4


def test_loops_and_nesting():
    seen = []
    q = sympy.Matrix([[2, 1], [1, 2]])
    assert pari.forqfvec(lambda v: seen.append(v), q, 4) is None
    assert seen == [[0, 1], [1, -1], [1, 0]]
    inner = pari.sum(lambda k: pari.intnum(lambda t: t**k, 0, 1), 1, 3)
    assert close(inner, sympy.Rational(13, 12))
    assert pari.sum(lambda n: pari.sum(lambda m: m * n, 1, n), 1, 4) == 65


def test_errors():
    with pytest.raises(ValueError, match="boom"):
        pari.sum(lambda n: (_ for _ in ()).throw(ValueError("boom")), 1, 3)
    with pytest.raises(TypeError, match="cannot convert NoneType"):
        pari.sum(lambda n: None, 1, 3)
    with pytest.raises(TypeError, match=r"takes 3 arguments \(f, a, b\)"):
        pari.sum(lambda n: n, 1)
