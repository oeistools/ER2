"""The initial namespace of every ER2 program (ARCHITECTURE.md §3.3).

The helpers named in ``er2.preparser`` (``__er2_int__``, ``__er2_sym__``)
are what generated code calls; they use reserved dunder names so that
user code such as ``from sympy import *`` can never shadow them.
"""

import sympy

from er2 import dispatch, preparser
from er2.backends.pari_backend import pari
from er2.printing import latex, show
from er2.runtime.factorization import Factorization
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational, literal
from er2.runtime.qfb import Qfb

# Public functions (CAS and number theory); they choose their backend in
# ``er2.dispatch``.
FUNCTIONS = tuple(dispatch.FUNCTIONS)

# SymPy constants and elementary functions, exposed as they are.
SYMPY_NAMES = (
    "pi",
    "E",
    "I",
    "oo",
    "sqrt",
    "exp",
    "log",
    "sin",
    "cos",
    "tan",
    "Eq",
)

# Predefined symbols (D3): ``_x`` is the symbol ``x``, and so on.
PREDEFINED_SYMBOLS = ("x", "y", "z", "n", "k", "p")


def symbols(names):
    """Return a tuple of SymPy symbols for the comma-separated ``names``."""
    result = sympy.symbols(names, seq=True)
    return tuple(result)


def namespace():
    """Return a fresh dict with the ER2 prelude."""
    ns = {
        preparser.INTEGER: literal,
        preparser.SYMBOLS: symbols,
        "Integer": Integer,
        "Rational": Rational,
        "Mod": Mod,
        "Factorization": Factorization,
        "Qfb": Qfb,
        "pari": pari,
        "symbols": symbols,
        "latex": latex,
        "show": show,
    }
    ns.update(dispatch.FUNCTIONS)
    for name in SYMPY_NAMES:
        ns[name] = getattr(sympy, name)
    for name in PREDEFINED_SYMBOLS:
        ns[f"_{name}"] = sympy.Symbol(name)
    return ns


def inject(target):
    """Add the prelude to the ``target`` dict without overwriting names."""
    for name, value in namespace().items():
        target.setdefault(name, value)
    return target
