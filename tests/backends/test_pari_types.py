"""PARI types with ER2 semantics (M4): SymPy <-> PARI conversions.

Expected values were computed with cypari2 (PARI 2.17.2).
"""

import pytest
import sympy

from er2.backends.pari_backend import PARI, from_pari, pari, to_pari
from er2.runtime.modular import Mod
from er2.runtime.qfb import Qfb

x, y, sigma = sympy.symbols("x y sigma")


@pytest.mark.parametrize(
    ("value", "gp", "kind"),
    [
        (x**2 - 1, "x^2 - 1", "t_POL"),
        (x * y + y / 3, "y*x + 1/3*y", "t_POL"),
        (sympy.Rational(3, 4) + x, "x + 3/4", "t_POL"),
        (1 / (x**2 + 1), "1/(x^2 + 1)", "t_RFRAC"),
        (
            sympy.series(sympy.sin(x), x, 0, 6),
            "x - 1/6*x^3 + 1/120*x^5 + O(x^6)",
            "t_SER",
        ),
        (1 + 2 * sympy.I, "1 + 2*I", "t_COMPLEX"),
        (sympy.oo, "+oo", "t_INFINITY"),
        (-sympy.oo, "-oo", "t_INFINITY"),
        (sympy.Matrix([[1, x], [2, 3]]), "[1, x; 2, 3]", "t_MAT"),
        (Mod(x, x**2 + 1), "Mod(x, x^2 + 1)", "t_POLMOD"),
        (Qfb(1, 1, 6), "Qfb(1, 1, 6)", "t_QFB"),
    ],
)
def test_round_trip(value, gp, kind):
    converted = to_pari(value)
    assert converted.type() == kind
    assert str(converted) == gp
    assert from_pari(converted) == value


def test_reserved_gp_names_become_new_variables():
    """``sigma`` is a GP function, so it gets its own variable."""
    p = to_pari(sigma**2 + 1)
    assert p.type() == "t_POL" and str(p) == "sigma^2 + 1"
    assert to_pari(sigma) == to_pari(sigma)  # the same variable each time
    assert from_pari(p) == sigma**2 + 1


def test_reals_convert_exactly_both_ways():
    zeta2 = pari.zeta(2)
    assert to_pari(zeta2) == PARI.zeta(2, precision=128)
    assert from_pari(to_pari(zeta2)) == zeta2
    assert abs(from_pari(to_pari(sympy.pi)) - sympy.pi.evalf(40)) < 1e-37


def test_series_with_negative_valuation():
    assert from_pari(PARI("1/x + 1 + O(x^2)")) == 1 / x + 1 + sympy.O(x**2)


@pytest.mark.parametrize(
    "text",
    [
        "1 + x + x^2 + O(x^3)",  # the ordinary case: no expand needed
        "1/x + 1 + O(x^2)",  # negative valuation: truncate gives a t_RFRAC
        "1/x^3 + O(x)",
        "(y + 1)*x^2 + y*x + 1 + O(x^3)",  # coefficients in another variable
        "O(x^4)",  # no terms at all
        "1 + O(x^2)",  # truncate gives a t_INT, not a t_POL
        "1/2 + x/3 + O(x^2)",
    ],
)
def test_a_series_comes_back_expanded(text):
    """``_series`` skips ``expand`` when it would do nothing (§2.1).

    Skipping it in a case that needed it is invisible in the value but
    wrong in the form, so every shape that reaches ``truncate`` is
    checked against expanding unconditionally, which is what it did
    before.
    """
    result = from_pari(PARI(text))
    body, order = result.removeO(), result.getO()
    assert body == sympy.expand(body)
    assert from_pari(PARI(text)) == sympy.expand(body) + (order or 0)


def test_series_away_from_zero_is_not_converted():
    s = sympy.series(sympy.exp(x), x, 1, 3)
    with pytest.raises(TypeError, match="around 0"):
        to_pari(s)


def test_pari_functions_accept_sympy_objects():
    assert pari.polresultant(x**2 + 1, x**3 - 2) == 5
    assert pari.polcyclo(6) == x**2 - x + 1
    assert pari.polisirreducible(x**4 + 1) == 1
    assert pari.polgalois(x**3 - 2)[3] == "S3"
    assert pari.matdet(sympy.Matrix([[1, 2], [3, 4]])) == -2
    assert pari.exp(pari.zeta(2)) > 5


def test_polynomial_mod():
    i = Mod(x, x**2 + 1)
    assert i.is_polynomial and i.modulus == x**2 + 1
    assert i**2 == Mod(-1, x**2 + 1)
    assert i**-1 == Mod(-x, x**2 + 1)
    assert i * x == Mod(-1, x**2 + 1)
    assert i + 1 == 1 + i == Mod(x + 1, x**2 + 1)
    assert 2 - i == Mod(2 - x, x**2 + 1)
    assert i / 2 == Mod(x / 2, x**2 + 1)
    assert Mod(x**3, x**2 + 1) == Mod(-x, x**2 + 1)
    # Like PARI: different moduli combine modulo their gcd.
    assert Mod(x**2, x**3 - 2) * Mod(x, x**2 - 2) == Mod(0, 1)
    with pytest.raises(TypeError):
        int(i)


def test_qfb():
    q = Qfb(1, 1, 6)
    assert (q.a, q.b, q.c) == (1, 1, 6)
    assert q.discriminant() == -23
    assert q(1, 1) == 8
    assert q * Qfb(2, 1, 3) == Qfb(2, 1, 3)
    assert Qfb(2, 1, 3) ** 3 == q
    assert Qfb(12, 11, 3).reduce() == Qfb(2, -1, 3)
    assert pari.qfbprimeform(-23, 2) == Qfb(2, 1, 3)
    assert len({Qfb(1, 1, 6), Qfb(1, 1, 6), Qfb(2, 1, 3)}) == 2
    with pytest.raises(TypeError):
        Qfb(1, 2, 3.0)
