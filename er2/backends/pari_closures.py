"""PARI functions that take a GP expression, called with Python functions.

In GP, ``sum(n = 1, 10, 1/n^2)`` takes an expression in a loop variable.
ER2 takes a Python callable instead: ``pari.sum(lambda n: 1/n^2, 1, 10)``
(ARCHITECTURE.md §3.5, the ``wrapper`` rows).

Each function is a fixed GP lambda from ``SIGNATURES``, such as
``(f, a, b, prec) -> localbitprec(prec); sum(n = a, b, f(n))``.  GP only
ever parses these constant texts; user values and callables are passed
as arguments.  The callable receives ER2 values and its result is
converted back to PARI.
"""

from er2.backends.pari_backend import PARI, from_pari, to_pari

# name -> (parameters, GP call, arity of the callable ``f``).  The
# callable is always the parameter ``f``; ``prec`` is added to every
# lambda so that real results use ER2's precision.
SIGNATURES = {
    "sum": ("f, a, b", "sum(n = a, b, f(n))", 1),
    "prod": ("f, a, b", "prod(n = a, b, f(n))", 1),
    "sumdiv": ("n, f", "sumdiv(n, d, f(d))", 1),
    "sumdivmult": ("n, f", "sumdivmult(n, d, f(d))", 1),
    "prodeuler": ("f, a, b", "prodeuler(p = a, b, f(p))", 1),
    "direuler": ("f, a, b", "direuler(p = a, b, f(p, 'X))", 2),
    "suminf": ("f, a", "suminf(n = a, f(n))", 1),
    "prodinf": ("f, a", "prodinf(n = a, f(n))", 1),
    "sumalt": ("f, a", "sumalt(n = a, f(n))", 1),
    "sumpos": ("f, a", "sumpos(n = a, f(n))", 1),
    "sumnum": ("f, a", "sumnum(n = a, f(n))", 1),
    "sumnumap": ("f, a", "sumnumap(n = a, f(n))", 1),
    "sumnumlagrange": ("f, a", "sumnumlagrange(n = a, f(n))", 1),
    "sumnummonien": ("f, a", "sumnummonien(n = a, f(n))", 1),
    "sumnumsidi": ("f, a", "sumnumsidi(n = a, f(n))", 1),
    "intnum": ("f, a, b", "intnum(t = a, b, f(t))", 1),
    "intnumgauss": ("f, a, b", "intnumgauss(t = a, b, f(t))", 1),
    "intnumromb": ("f, a, b", "intnumromb(t = a, b, f(t))", 1),
    "intnumosc": ("f, a, h", "intnumosc(t = a, f(t), h)", 1),
    "intcirc": ("f, a, r", "intcirc(z = a, r, f(z))", 1),
    "derivnum": ("f, a", "derivnum(t = a, f(t))", 1),
    "solve": ("f, a, b", "solve(t = a, b, f(t))", 1),
    "solvestep": ("f, a, b, step", "solvestep(t = a, b, step, f(t))", 1),
    "vectorv": ("n, f", "vectorv(n, k, f(k))", 1),
    "vectorsmall": ("n, f", "vectorsmall(n, k, f(k))", 1),
    "forqfvec": ("f, q, b", "forqfvec(v, q, b, f(v))", 1),
}


# Loops whose expression value is ignored: the callable may return None.
LOOPS = {"forqfvec"}


def _adapter(f, arity, loop=False):
    """Wrap ``f`` so PARI can call it: ER2 values in, PARI value out.

    cypari2 turns a Python function into a GP closure of the same arity,
    so the adapter has a fixed arity (not ``*args``).
    """

    def result(value):
        return PARI(0) if loop and value is None else to_pari(value)

    if arity == 1:

        def adapter(a):
            return result(f(from_pari(a)))

    else:

        def adapter(a, b):
            return result(f(from_pari(a), from_pari(b)))

    return PARI(adapter)


def _closure(name):
    """Return the GP lambda for ``name``.

    It is parsed on every call and never cached: a PARI object created
    inside a callback (a wrapper used inside another wrapper's function)
    lives on PARI's temporary stack and must not outlive it.
    """
    parameters, call, _ = SIGNATURES[name]
    return PARI(f"({parameters}, prec) -> localbitprec(prec); {call}")


def function(name, summary=""):
    """Return the ER2 function for the wrapper ``name``."""
    parameters, _, arity = SIGNATURES[name]
    names = [p.strip() for p in parameters.split(",")]

    def wrapper(*args):
        if len(args) != len(names):
            raise TypeError(
                f"{name}() takes {len(names)} arguments "
                f"({parameters}), {len(args)} given"
            )
        converted = [
            _adapter(arg, arity, name in LOOPS) if key == "f" else to_pari(arg)
            for key, arg in zip(names, args)
        ]
        precision = PARI.get_real_precision_bits()
        return from_pari(_closure(name)(*converted, precision))

    wrapper.__name__ = wrapper.__qualname__ = name
    wrapper.__doc__ = (
        f"{summary}\n\n``pari.{name}({parameters})``: ``f`` is a Python "
        f"function of {arity} argument{'s' if arity > 1 else ''}.  "
        f"GP: ``{SIGNATURES[name][1]}``."
    ).strip()
    return wrapper
