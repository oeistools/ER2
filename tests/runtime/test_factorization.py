"""``Factorization``: the result of ``factor`` on numbers."""

from er2.printing import latex
from er2.runtime.factorization import Factorization
from er2.runtime.numbers import Integer, Rational


def test_sequence_of_pairs():
    f = Factorization([(2, 3), (3, 2)])
    assert list(f) == [(2, 3), (3, 2)]
    assert len(f) == 2 and f[0] == (2, 3)
    assert all(type(p) is Integer and type(e) is Integer for p, e in f)
    assert dict(f) == {2: 3, 3: 2}


def test_value():
    assert Factorization([(2, 3), (3, 2)]).value() == 72
    assert Factorization([(2, 3)], unit=-1).value() == -8
    value = Factorization([(2, -2), (3, -1)]).value()
    assert value == Rational(1, 12) and type(value) is Rational
    assert Factorization([]).value() == 1
    assert Factorization([(0, 1)]).value() == 0


def test_text_and_latex():
    cases = [
        (Factorization([(2, 3), (3, 2)]), "2^3 * 3^2", r"2^{3} \cdot 3^{2}"),
        (Factorization([(7, 1)]), "7", "7"),
        (
            Factorization([(2, -2), (3, -1)]),
            "2^-2 * 3^-1",
            r"2^{-2} \cdot 3^{-1}",
        ),
        (Factorization([(2, 1)], unit=-1), "-1 * 2", r"-1 \cdot 2"),
        (Factorization([]), "1", "1"),
        (Factorization([], unit=-1), "-1", "-1"),
        (Factorization([(0, 1)]), "0", "0"),
    ]
    for f, text, tex in cases:
        assert str(f) == repr(f) == text
        assert latex(f) == tex
        assert f._repr_latex_() == f"${tex}$"


def test_equality_and_completeness():
    assert Factorization([(2, 1)]) == Factorization([(2, 1)])
    assert Factorization([(2, 1)]) != Factorization([(2, 1)], unit=-1)
    assert Factorization([(2, 1)]).is_complete
    partial = Factorization([(2, 1), (15, 1)], unfactored=[15])
    assert not partial.is_complete and partial.unfactored == (15,)
