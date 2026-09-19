"""Plain-text printing (D11) and LaTeX output (§3.6)."""

from fractions import Fraction

import pytest
import sympy

from er2 import printing
from er2.printing import Tex, latex
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational
from er2.runtime.qfb import Qfb

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
        ((x**2 - 1) / (x + 1), "(x^2 - 1)/(x + 1)"),
        (sympy.Derivative(x**2, x), "Derivative(x^2, x)"),
        (
            sympy.series(sympy.exp(x), x, 0, 3),
            "1 + x + x^2/2 + O(x^3)",
        ),
        (
            sympy.Poly(x**2 + 3 * x * y**2, x),
            "Poly(x^2 + 3*y^2*x, x, domain='ZZ[y]')",
        ),
        (Mod(x**3, x**2 + 1), "Mod(-x, x^2 + 1)"),
        (Qfb(1, 1, 6), "Qfb(1, 1, 6)"),
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
        # PARI types (M4).
        (Qfb(1, 1, 6), r"\left(1, 1, 6\right)"),
        (Mod(x, x**2 + 1), r"x \pmod{x^{2} + 1}"),
        (Mod(3, 7), r"3 \pmod{7}"),
        # Symbolic types (M2).
        (x * y, "x y"),
        ((x**2 - 1) / (x + 1), r"\frac{x^{2} - 1}{x + 1}"),
        (sympy.sqrt(2) * x, r"\sqrt{2} x"),
        (sympy.exp(x), "e^{x}"),
        (sympy.I * x, "i x"),
        (sympy.oo, r"\infty"),
        (sympy.log(x), r"\log{\left(x \right)}"),
        (sympy.Derivative(x**2, x), r"\frac{d}{d x} x^{2}"),
        (
            sympy.Integral(sympy.sin(x), (x, 0, sympy.pi)),
            r"\int\limits_{0}^{\pi} \sin{\left(x \right)}\, dx",
        ),
        (
            sympy.Limit(sympy.sin(x) / x, x, 0),
            r"\lim_{x \to 0^+}\left(\frac{\sin{\left(x \right)}}{x}\right)",
        ),
        (
            sympy.series(sympy.exp(x), x, 0, 3),
            r"1 + x + \frac{x^{2}}{2} + O\left(x^{3}\right)",
        ),
        (sympy.Lt(x, 1), "x < 1"),
        (
            sympy.Poly(x**2 + 1, x),
            r"\operatorname{Poly}{\left( x^{2} + 1, x, "
            r"domain=\mathbb{Z} \right)}",
        ),
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
