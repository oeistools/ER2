"""Plain-text and LaTeX output (ARCHITECTURE.md §3.6, D11).

* ``ER2StrPrinter`` prints SymPy expressions in ER2 notation (``x^2``).
  ``install()`` makes it SymPy's default for the current process; the ER2
  entry points call it, a plain ``import er2`` does not (D11).
* ``latex(obj)`` returns the LaTeX of any mathematical object as a
  ``Tex`` string, which renders as math in Jupyter and Quarto.
* ``show(*objs)`` renders objects as math in notebooks and prints them
  as ER2 text in a terminal.
"""

import functools
import sys
from fractions import Fraction

import sympy
import sympy.printing.str as sympy_str
from sympy.printing.precedence import precedence

__all__ = ["ER2StrPrinter", "Tex", "install", "latex", "show", "uninstall"]


class ER2StrPrinter(sympy_str.StrPrinter):
    """SymPy's ``StrPrinter`` with ``^`` for powers."""

    def _print_Pow(self, expr, rational=False):  # noqa: N802 (SymPy API)
        """Print a power as ``base^exp`` (SymPy prints ``base**exp``)."""
        prec = precedence(expr)
        if expr.exp is sympy.S.Half and not rational:
            return f"sqrt({self._print(expr.base)})"
        if expr.is_commutative:
            if -expr.exp is sympy.S.Half and not rational:
                return f"1/sqrt({self._print(expr.base)})"
            if expr.exp is -sympy.S.One:
                base = self.parenthesize(expr.base, prec, strict=False)
                return f"1/{base}"
        base = self.parenthesize(expr.base, prec, strict=False)
        exp = self.parenthesize(expr.exp, prec, strict=False)
        return f"{base}^{exp}"

    def _print_Poly(self, expr):  # noqa: N802 (SymPy API)
        """Print a polynomial with ``^`` for the powers of its generators.

        SymPy's method prints coefficients and generators through
        ``self._print`` and writes ``**`` only between a generator and its
        exponent, so replacing ``**`` changes exactly those.
        """
        return super()._print_Poly(expr).replace("**", "^")


def er2_str(expr, **settings):
    """Return ``expr`` as a string in ER2 notation."""
    return ER2StrPrinter(settings).doprint(expr)


_original_sstr = None


def install():
    """Make ER2 notation SymPy's default ``str``/``repr`` in this process."""
    global _original_sstr
    if _original_sstr is None:
        _original_sstr = sympy_str.sstr
        sympy_str.sstr = er2_str


def uninstall():
    """Restore SymPy's own printer (undo ``install``)."""
    global _original_sstr
    if _original_sstr is not None:
        sympy_str.sstr = _original_sstr
        _original_sstr = None


class Tex(str):
    """A LaTeX string (without ``$``) that renders as math in notebooks.

    It is an ordinary ``str``, so it can be written to files or used in
    f-strings and Matplotlib labels.  Jupyter and Quarto render it through
    ``_repr_latex_``; Quarto inline expressions (`` `{python} latex(f)` ``)
    render it through ``_repr_markdown_``.
    """

    def __new__(cls, body, display=False):
        """Create a ``Tex`` from the LaTeX ``body``."""
        self = super().__new__(cls, body)
        self.display = display
        return self

    def _delimited(self):
        return f"$${self}$$" if self.display else f"${self}$"

    def _repr_latex_(self):
        return self._delimited()

    def _repr_markdown_(self):
        return self._delimited()


def latex(obj, *, display=False, **options):
    """Return the LaTeX of ``obj`` as a ``Tex``.

    ``display=True`` renders it as display math (``$$...$$``) in
    notebooks.  ``options`` are passed to SymPy's LaTeX printer.
    """
    return Tex(_latex(obj, options), display=display)


@functools.singledispatch
def _latex(obj, options):
    r"""Return the LaTeX body of ``obj`` (fallback: ``\texttt{repr}``).

    ER2 types implement SymPy's printer protocol (a ``_latex(printer)``
    method), so their LaTeX is also correct inside SymPy containers.
    """
    if callable(getattr(obj, "_latex", None)):
        return sympy.latex(obj, **options)
    rich = getattr(obj, "_repr_latex_", None)
    if callable(rich):
        body = rich()
        if isinstance(body, str):
            return _strip_math(body)
    return r"\texttt{%s}" % _escape(repr(obj))


@_latex.register
def _(obj: sympy.Basic, options):
    return sympy.latex(obj, **options)


@_latex.register
def _(obj: bool, options):
    return r"\text{%s}" % obj


@_latex.register
def _(obj: int, options):
    return str(int(obj))


@_latex.register
def _(obj: Fraction, options):
    return sympy.latex(sympy.Rational(obj.numerator, obj.denominator))


@_latex.register
def _(obj: float, options):
    return sympy.latex(sympy.Float(obj))


@_latex.register
def _(obj: complex, options):
    return sympy.latex(sympy.sympify(obj))


@_latex.register
def _(obj: str, options):
    if isinstance(obj, Tex):
        return str(obj)
    return r"\text{%s}" % _escape(obj)


@_latex.register(list)
@_latex.register(tuple)
def _(obj, options):
    items = r",\ ".join(_latex(item, options) for item in obj)
    if isinstance(obj, tuple):
        return r"\left( %s\right)" % items
    return r"\left[ %s\right]" % items


@_latex.register(set)
@_latex.register(frozenset)
def _(obj, options):
    items = sorted((_latex(item, options) for item in obj))
    return r"\left\{%s\right\}" % r", ".join(items)


@_latex.register
def _(obj: dict, options):
    items = r", \ ".join(
        f"{_latex(k, options)} : {_latex(v, options)}" for k, v in obj.items()
    )
    return r"\left\{ %s\right\}" % items


def _strip_math(body):
    r"""Remove ``$``/``$$`` delimiters and ``\displaystyle``."""
    body = body.strip()
    for delim in ("$$", "$"):
        if body.startswith(delim) and body.endswith(delim):
            body = body[len(delim) : -len(delim)].strip()
            break
    return body.removeprefix(r"\displaystyle").strip()


def _escape(text):
    """Escape LaTeX special characters in ``text``."""
    table = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\^{}",
        "~": r"\~{}",
    }
    return "".join(table.get(ch, ch) for ch in text)


def show(*objs):
    """Render ``objs`` as display math in notebooks, else print them."""
    display = _notebook_display()
    for obj in objs:
        if display is None:
            print(obj)
        else:
            display(latex(obj, display=True))


def _notebook_display():
    """Return IPython's ``display`` inside a kernel, else ``None``."""
    ipython = sys.modules.get("IPython")
    if ipython is None:
        return None
    shell = ipython.get_ipython()
    if shell is None or not hasattr(shell, "kernel"):
        return None
    from IPython.display import display

    return display
