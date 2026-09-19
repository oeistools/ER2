"""The initial namespace of every ER2 program (ARCHITECTURE.md §3.3).

The helpers named in ``er2.preparser`` (``__er2_int__``, ``__er2_sym__``)
are what generated code calls; they use reserved dunder names so that
user code such as ``from sympy import *`` can never shadow them.

The SymPy values (``pi``, ``sin``, ``_x``, ...) need SymPy, which takes
about 0.3 s to import.  Given a program's code, ``namespace`` includes
them only if the program uses them (``er2._lazy``).
"""

import types

from er2 import _lazy, dispatch, oeis, preparser
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


# Names through which code can reach globals it does not name.
_DYNAMIC_NAMES = {"eval", "exec", "globals", "vars", "locals", "__import__"}


def symbols(names):
    """Return a tuple of SymPy symbols for the comma-separated ``names``."""
    result = _lazy.sympy().symbols(names, seq=True)
    return tuple(result)


def sympy_names():
    """Return the prelude names whose values are SymPy objects."""
    return {*SYMPY_NAMES, *(f"_{name}" for name in PREDEFINED_SYMBOLS)}


def needs_sympy(code):
    """Whether compiled ``code`` may use a SymPy value of the prelude."""
    names = set()
    pending = [code]
    while pending:
        current = pending.pop()
        names.update(current.co_names)
        pending.extend(
            c for c in current.co_consts if isinstance(c, types.CodeType)
        )
    return bool(names & (sympy_names() | _DYNAMIC_NAMES))


def namespace(code=None):
    """Return a fresh dict with the ER2 prelude.

    With ``code`` (a compiled program), the SymPy values are included only
    if ``needs_sympy(code)``; without it, they always are.
    """
    ns = {
        preparser.INTEGER: literal,
        preparser.SYMBOLS: symbols,
        "Integer": Integer,
        "Rational": Rational,
        "Mod": Mod,
        "Factorization": Factorization,
        "Qfb": Qfb,
        "pari": pari,
        "oeis": oeis,
        "symbols": symbols,
        "latex": latex,
        "show": show,
    }
    ns.update(dispatch.FUNCTIONS)
    if code is None or needs_sympy(code):
        sympy = _lazy.sympy()
        for name in SYMPY_NAMES:
            ns[name] = getattr(sympy, name)
        for name in PREDEFINED_SYMBOLS:
            ns[f"_{name}"] = sympy.Symbol(name)
    return ns


def inject(target, code=None):
    """Add the prelude to the ``target`` dict without overwriting names.

    ``code`` is the compiled program that will run in ``target``, if
    known; see ``namespace``.
    """
    for name, value in namespace(code).items():
        target.setdefault(name, value)
    return target
