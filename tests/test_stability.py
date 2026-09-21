"""The public API surface (docs/STABILITY.md).

The policy's subject is a list of names, so the list lives here and is
pinned.  Adding or removing a public name fails this test until the list
is changed deliberately -- which is the point: from 1.0 a removal costs
a deprecation cycle (STABILITY.md §4), and a silent one must be
impossible.

This is the library half of the guarantee.  The language half is
``tests/test_language_spec.py``.
"""

from pathlib import Path

import er2
from er2 import prelude

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "docs" / "STABILITY.md"

# STABILITY.md S3: every name an ER2 program finds already defined.
PRELUDE_NAMES = frozenset(
    {
        "DirichletSeries",
        "E",
        "Eq",
        "Factorization",
        "GF",
        "I",
        "Integer",
        "Matrix",
        "Mod",
        "NumberField",
        "Qfb",
        "Rational",
        "bigomega",
        "binomial",
        "cancel",
        "charpoly",
        "chinese",
        "collect",
        "core",
        "cos",
        "dedekind_psi",
        "det",
        "diff",
        "discriminant",
        "divisors",
        "echelon_form",
        "exp",
        "expand",
        "factor",
        "factorial",
        "fibonacci",
        "gcd",
        "generating_function",
        "groebner",
        "hadamard_product",
        "hermite_form",
        "integrate",
        "inverse",
        "isirreducible",
        "ispower",
        "isprime",
        "isprimepower",
        "ispseudoprime",
        "issquare",
        "issquarefree",
        "jordan_totient",
        "kernel",
        "kronecker",
        "latex",
        "lcm",
        "limit",
        "log",
        "minpoly",
        "mu",
        "nextprime",
        "numdiv",
        "oeis",
        "omega",
        "oo",
        "pari",
        "phi",
        "pi",
        "precprime",
        "prime",
        "primepi",
        "primes",
        "radical",
        "rank",
        "reduce",
        "resultant",
        "series",
        "series_laplace",
        "series_reverse",
        "show",
        "sigma",
        "simplify",
        "sin",
        "smith_form",
        "solve",
        "sqrt",
        "sqrtint",
        "symbols",
        "tan",
        "valuation",
        "znlog",
        "znorder",
        "znprimroot",
    }
)

# STABILITY.md S4 (LANGUAGE.md §6.2 R3): the predefined symbols.
PREDEFINED_SYMBOLS = frozenset({"_x", "_y", "_z", "_n", "_k", "_p"})

# What ``import er2`` exposes to a plain Python program.
MODULE_EXPORTS = frozenset(
    {"Integer", "Rational", "latex", "preparse", "show"}
)


def test_the_prelude_surface_is_pinned():
    """S3: the set of public prelude names is exactly this."""
    namespace = prelude.namespace()
    actual = {name for name in namespace if not name.startswith("_")}
    added = sorted(actual - PRELUDE_NAMES)
    removed = sorted(PRELUDE_NAMES - actual)
    assert not added, (
        f"new public names: {added}. Add them here on purpose, and to "
        f"docs/PARI_FUNCTIONS.md and the LaTeX coverage test if they apply."
    )
    assert not removed, (
        f"public names gone: {removed}. From 1.0 this costs a deprecation "
        f"cycle (docs/STABILITY.md §4)."
    )


def test_the_predefined_symbols_are_there():
    """S4: ``_x`` and friends are part of the stable surface."""
    namespace = prelude.namespace(compile("_x + _y", "<t>", "eval"))
    assert PREDEFINED_SYMBOLS <= set(namespace)


def test_the_module_exports_are_pinned():
    """``import er2`` from plain Python exposes exactly these."""
    assert set(er2.__all__) == MODULE_EXPORTS
    for name in MODULE_EXPORTS:
        assert hasattr(er2, name), name


def test_every_stable_function_is_reachable():
    """S3: the dispatch functions are all in the prelude."""
    from er2 import dispatch

    assert set(dispatch.FUNCTIONS) <= PRELUDE_NAMES


def test_the_policy_names_its_enforcement():
    """§5: the policy must point at this file, or it is unenforced."""
    text = POLICY.read_text(encoding="utf-8")
    assert "tests/test_stability.py" in text
    assert "tests/test_language_spec.py" in text
