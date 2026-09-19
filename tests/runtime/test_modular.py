"""``Mod``: integers modulo n.  Expected values computed with cypari2."""

import pytest

from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational


def test_construction_and_attributes():
    a = Mod(10, 7)
    assert a == Mod(3, 7)
    assert a.lift() == 3 and type(a.lift()) is Integer
    assert a.modulus == 7 and type(a.modulus) is Integer
    assert int(a) == 3
    assert Mod(5, -7) == Mod(5, 7)
    assert Mod(Rational(1, 3), 7) == Mod(5, 7)
    assert not Mod(7, 7) and Mod(1, 7)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (lambda: Mod(3, 7) + 5, Mod(1, 7)),
        (lambda: 5 + Mod(3, 7), Mod(1, 7)),
        (lambda: Mod(3, 7) - 5, Mod(5, 7)),
        (lambda: 5 - Mod(3, 7), Mod(2, 7)),
        (lambda: Mod(3, 7) * Mod(4, 7), Mod(5, 7)),
        (lambda: Mod(3, 7) ** -1, Mod(5, 7)),
        (lambda: Mod(3, 7) ** 100, Mod(4, 7)),
        (lambda: 2 / Mod(3, 7), Mod(3, 7)),
        (lambda: Mod(2, 7) / 3, Mod(3, 7)),
        (lambda: -Mod(3, 7), Mod(4, 7)),
        (lambda: Mod(1, 4) + Mod(1, 6), Mod(0, 2)),
        (lambda: Mod(3, 7) * Rational(1, 3), Mod(1, 7)),
    ],
)
def test_arithmetic_matches_pari(result, expected):
    assert result() == expected


def test_errors():
    with pytest.raises(ZeroDivisionError):
        Mod(2, 4) ** -1
    with pytest.raises(ZeroDivisionError):
        Mod(1, 0)
    with pytest.raises(TypeError):
        Mod(1.5, 7)
    with pytest.raises(TypeError):
        Mod(1, 7.0)


def test_equality_and_hash():
    assert Mod(3, 7) != Mod(3, 8)
    assert Mod(3, 7) != 3  # a residue is not an integer
    assert len({Mod(3, 7), Mod(10, 7), Mod(3, 8)}) == 2


def test_printing():
    from er2.printing import latex

    assert repr(Mod(3, 7)) == str(Mod(3, 7)) == "Mod(3, 7)"
    assert latex(Mod(3, 7)) == r"3 \pmod{7}"
    assert Mod(3, 7)._repr_latex_() == r"$3 \pmod{7}$"
