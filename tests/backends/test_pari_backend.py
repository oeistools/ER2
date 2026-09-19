"""The PARI backend and its conversion boundary (§3.4, §3.5, §3.7).

Expected values were computed with cypari2 (PARI 2.17.2).
"""

import cypari2
import pytest
import sympy

from er2.backends import pari_backend
from er2.backends.pari_backend import PARI, from_pari, pari, to_pari
from er2.runtime.factorization import Factorization
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational

x = sympy.Symbol("x")


@pytest.mark.parametrize(
    "value",
    [
        Integer(0),
        Integer(-7),
        Integer(2) ** 300,
        Rational(-5, 3),
        Mod(3, 7),
        [Integer(1), Rational(1, 2), Mod(2, 5)],
    ],
)
def test_round_trip(value):
    back = from_pari(to_pari(value))
    assert back == value
    if not isinstance(value, list):
        assert type(back) is type(value)


def test_to_pari():
    assert to_pari(12).type() == "t_INT"
    assert to_pari(sympy.Rational(1, 3)) == PARI("1/3")
    assert to_pari(sympy.Integer(5)).type() == "t_INT"
    assert to_pari((1, 2)).type() == "t_VEC"
    with pytest.raises(TypeError, match="not a polynomial"):
        to_pari(sympy.sin(x))


def test_from_pari():
    assert type(from_pari(PARI(5))) is Integer
    assert from_pari(PARI("x^2 - x + 1")) == x**2 - x + 1
    assert from_pari(PARI("1/(x^2 + 1)")) == 1 / (x**2 + 1)
    assert from_pari(PARI("1 + 2*I")) == 1 + 2 * sympy.I
    assert from_pari(PARI("Vecsmall([3, 4])")) == [3, 4]
    assert from_pari(PARI("[1, 2; 3, 4]")) == sympy.Matrix([[1, 2], [3, 4]])
    assert from_pari(PARI('"text"')) == "text"


def test_unsupported_pari_types_raise():
    with pytest.raises(TypeError, match="t_FFELT.*pari.raw"):
        pari.ffgen(9)
    assert isinstance(pari.raw.ffgen(9), cypari2.gen.Gen)
    with pytest.raises(TypeError, match="t_PADIC"):
        from_pari(PARI("1 + O(3^5)"))


def test_reals_keep_pari_precision():
    zeta2 = pari.zeta(2)
    assert isinstance(zeta2, sympy.Float)
    expected = sympy.N(sympy.pi**2 / 6, 38)
    assert abs(zeta2 - expected) < sympy.Float("1e-37")
    assert str(pari.pi()) == "3.1415926535897932384626433832795028842"
    low = pari.zeta(2, precision=64)
    assert abs(low - expected) < 1e-18
    zero = from_pari(PARI(0.0))
    assert isinstance(zero, sympy.Float) and zero.is_zero


def test_set_precision():
    try:
        pari.set_precision(60)
        assert str(pari.pi()).startswith("3.14159265358979323846264338327950")
        assert len(str(pari.pi())) > 60
    finally:
        pari.set_precision(pari_backend.DEFAULT_PRECISION)


def test_stack_maximum_is_large():
    assert PARI.stacksizemax() >= pari_backend.DEFAULT_STACK_MAX


@pytest.mark.parametrize(
    ("n", "text"),
    [
        (Integer(2) ** 127 - 1, "170141183460469231731687303715884105727"),
        (Integer(-360), "-1 * 2^3 * 3^2 * 5"),
        (Integer(2) ** 64 + 1, "274177 * 67280421310721"),
        (Rational(-9, 8), "-1 * 2^-3 * 3^2"),
        (Integer(1), "1"),
        (Integer(-1), "-1"),
        (Integer(0), "0"),
    ],
)
def test_factor(n, text):
    f = pari_backend.factor(n)
    assert isinstance(f, Factorization) and f.is_complete
    assert str(f) == text
    assert f.value() == n


def test_partial_factor():
    n = Integer(10) ** 60 + 1
    f = pari_backend.factor(n, limit=10**5)
    cofactor = Integer(
        99990000999900009999000099990000999900009999000099990001
    )
    assert list(f) == [(73, 1), (137, 1), (cofactor, 1)]
    assert f.unfactored == (cofactor,) and not f.is_complete
    assert f.value() == n


def test_dedekind_psi():
    # psi(n) = n * prod(1 + 1/p): psi(1..12)
    values = [1, 3, 4, 6, 6, 12, 8, 12, 12, 18, 12, 24]
    assert [pari_backend.dedekind_psi(k) for k in range(1, 13)] == values
    for bad in (0, -4, Rational(1, 2)):
        with pytest.raises(ValueError):
            pari_backend.dedekind_psi(bad)


def test_jordan_totient():
    # sumdiv(n, d, d^k * moebius(n/d)) in GP, for n = 1..12
    j2 = [1, 3, 8, 12, 24, 24, 48, 48, 72, 72, 120, 96]
    j3 = [1, 7, 26, 56, 124, 182, 342, 448, 702, 868, 1330, 1456]
    assert [pari_backend.jordan_totient(n, 2) for n in range(1, 13)] == j2
    assert [pari_backend.jordan_totient(n, 3) for n in range(1, 13)] == j3
    assert pari_backend.jordan_totient(360, 2) == 82944
    assert pari_backend.jordan_totient(10**12 + 39, 4) == (
        1000000000156000000009126000000237276000002313440
    )
    assert [pari_backend.jordan_totient(n, 0) for n in (1, 12)] == [1, 0]
    for n in range(1, 50):
        phi = int(pari_backend.PARI.eulerphi(n))
        assert pari_backend.jordan_totient(n, 1) == phi
        assert pari_backend.jordan_totient(n, 2) == (
            pari_backend.dedekind_psi(n) * phi
        )
    for n, k in ((0, 2), (-4, 2), (Rational(1, 2), 2), (12, -1), (12, x)):
        with pytest.raises(ValueError):
            pari_backend.jordan_totient(n, k)


def test_radical():
    # factorback(factorint(n)[, 1]) in GP, for n = 1..20 (OEIS A007947)
    values = [1, 2, 3, 2, 5, 6, 7, 2, 3, 10, 11, 6, 13, 14, 15, 2, 17, 6, 19]
    values.append(10)
    assert [pari_backend.radical(n) for n in range(1, 21)] == values
    assert pari_backend.radical(360) == 30
    assert pari_backend.radical(2**100 * 3**50 * 7) == 42
    assert isinstance(pari_backend.radical(12), Integer)
    for bad in (0, -12, Rational(1, 2), x):
        with pytest.raises(ValueError):
            pari_backend.radical(bad)


def test_predicates_return_bool_or_exponent():
    prelude = pari_backend.PRELUDE
    assert prelude["isprime"](Integer(2) ** 521 - 1) is True
    assert prelude["isprime"](91) is False
    assert prelude["issquare"](9) is True
    assert prelude["ispower"](8) == 3 and prelude["ispower"](10) == 0
    assert prelude["isprimepower"](9) == 2


def test_every_exposed_row_resolves_to_a_callable():
    rows = pari_backend._ROWS
    assert {r["status"] for r in rows} == {"prelude", "namespace"}
    for row in rows:
        function = getattr(pari, row["er2_name"])
        assert callable(function)
        assert function.__name__ == row["er2_name"]
        assert row["pari_name"] in function.__doc__


def test_namespace():
    assert pari.phi is pari_backend.PRELUDE["phi"]
    assert pari.factor is pari_backend.factor
    gamma = sympy.EulerGamma.evalf(40)
    assert abs(pari.digamma(1) + gamma) < sympy.Float("1e-37")
    assert abs(pari.factorial(5) - 120) < 1e-30  # a real, not exact
    assert isinstance(pari.factorial(5), sympy.Float)
    assert pari.Mod(2, 5) == Mod(2, 5)
    assert pari.raw is PARI
    assert "zeta" in dir(pari) and "raw" in dir(pari)
    with pytest.raises(AttributeError):
        pari.eulerphi  # PARI names are not ER2 names (use pari.phi)
    with pytest.raises(AttributeError):
        pari.no_such_function
