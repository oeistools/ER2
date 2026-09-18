"""The initial namespace of every ER2 program (ARCHITECTURE.md §3.3).

The helpers named in ``er2.preparser`` (``__er2_int__``, ``__er2_sym__``)
are what generated code calls; they use reserved dunder names so that
user code such as ``from sympy import *`` can never shadow them.
"""

import sympy

from er2 import preparser
from er2.printing import latex, show
from er2.runtime.numbers import Integer, Rational

# Predefined symbols (D3): ``_x`` is the symbol ``x``, and so on.
PREDEFINED_SYMBOLS = ("x", "y", "z", "n", "k", "p")


def symbols(names):
    """Return a tuple of SymPy symbols for the comma-separated ``names``."""
    result = sympy.symbols(names, seq=True)
    return tuple(result)


def namespace():
    """Return a fresh dict with the ER2 prelude."""
    ns = {
        preparser.INTEGER: Integer,
        preparser.SYMBOLS: symbols,
        "Integer": Integer,
        "Rational": Rational,
        "symbols": symbols,
        "latex": latex,
        "show": show,
    }
    for name in PREDEFINED_SYMBOLS:
        ns[f"_{name}"] = sympy.Symbol(name)
    return ns


def inject(target):
    """Add the prelude to the ``target`` dict without overwriting names."""
    for name, value in namespace().items():
        target.setdefault(name, value)
    return target
