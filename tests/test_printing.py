"""Plain-text printing (D11) and LaTeX output (§3.6)."""

from fractions import Fraction

import pytest
import sympy

from er2 import printing
from er2.printing import Tex, latex
from er2.runtime.numbers import Integer, Rational

x, y = sympy.symbols("x y")


@pytest.fixture
def installed():
    printing.install()
    yield
    printing.uninstall()


@pytest.mark.parametrize(
    ("expr", "text"),
    [
        (x**2 + 2 * x + 1, "x^2 + 2*x + 1"),
        ((x + 1) ** 2, "(x + 1)^2"),
        (x ** (y + 1), "x^(y + 1)"),
        (1 / x, "1/x"),
        (sympy.sqrt(x), "sqrt(x)"),
        (x ** sympy.Rational(1, 3), "x^(1/3)"),
        (-(x**2), "-x^2"),
    ],
)
def test_er2_notation(installed, expr, text):
    assert str(expr) == text
    assert repr(expr) == text


def test_install_is_reversible():
    printing.install()
    printing.uninstall()
    assert str(x**2) == "x**2"


def test_plain_import_does_not_change_sympy():
    import er2  # noqa: F401

    assert str(x**2) == "x**2"


@pytest.mark.parametrize(
    ("obj", "tex"),
    [
        (x**2 + 2 * x + 1, "x^{2} + 2 x + 1"),
        ((x + 1) ** 2, r"\left(x + 1\right)^{2}"),
        (Integer(5), "5"),
        (7, "7"),
        (Rational(1, 3), r"\frac{1}{3}"),
        (Fraction(-2, 5), r"- \frac{2}{5}"),
        (0.5, "0.5"),
        (True, r"\text{True}"),
        ("a_b", r"\text{a\_b}"),
        ([Rational(1, 2), x**3], r"\left[ \frac{1}{2},\ x^{3}\right]"),
        ((1, x), r"\left( 1,\ x\right)"),
        (
            sympy.Matrix([[1, x]]),
            r"\left[\begin{matrix}1 & x\end{matrix}\right]",
        ),
        (sympy.Eq(x, 1), "x = 1"),
    ],
)
def test_latex(obj, tex):
    assert latex(obj) == tex


def test_latex_fallback_never_raises():
    class Thing:
        def __repr__(self):
            return "<thing & $>"

    assert latex(Thing()) == r"\texttt{<thing \& \$>}"


def test_latex_uses_existing_repr_latex():
    class Custom:
        def _repr_latex_(self):
            return r"$\displaystyle \alpha$"

    assert latex(Custom()) == r"\alpha"


def test_tex_is_a_string_that_renders_as_math():
    tex = latex(x**2)
    assert isinstance(tex, Tex) and isinstance(tex, str)
    assert f"${tex}$" == "$x^{2}$"
    assert tex._repr_latex_() == "$x^{2}$"
    assert tex._repr_markdown_() == "$x^{2}$"
    assert latex(x**2, display=True)._repr_latex_() == "$$x^{2}$$"


def test_show_prints_outside_notebooks(capsys, installed):
    printing.show(x**2, Rational(1, 2))
    assert capsys.readouterr().out == "x^2\n1/2\n"
