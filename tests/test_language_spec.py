"""The language specification (docs/LANGUAGE.md), rule by rule.

Every test here cites the rule it pins.  The rules already covered
elsewhere are mapped in Appendix B of the specification; this file holds
the ones that had no test of their own, plus the checks that keep the
normative table itself from drifting.
"""

import re
import textwrap
from fractions import Fraction
from pathlib import Path

import pytest

from er2 import prelude
from er2.preparser import preparse
from er2.runtime.numbers import Integer, Rational

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "LANGUAGE.md"


def run(source):
    """Run ER2 ``source``; return its namespace."""
    namespace = prelude.namespace()
    exec(
        compile(preparse(textwrap.dedent(source)), "<spec>", "exec"), namespace
    )
    return namespace


def value(expression):
    """Return the value of the ER2 ``expression``."""
    return run(f"__result__ = ({expression})\n")["__result__"]


# §3.2 R3 and §4 — precedence and associativity.
#
# ``^`` is Python's ``**`` and ``^^`` is Python's ``^``, so each keeps
# the precedence of the operator it translates to.  These sit far apart
# in the table, which is the one place a Python reader's intuition about
# ER2 is wrong.
PRECEDENCE = [
    ("2^3^2", 512),  # right-associative: 2^(3^2)
    ("-2^2", -4),  # the power binds tighter than unary minus
    ("2^-1", Fraction(1, 2)),  # ... and looser on its right
    ("2^3 + 1", 9),  # level 14 beats level 11
    ("2^3 * 2", 16),
    ("6 ^^ 3", 5),
    ("6 ^^ 3 + 1", 2),  # level 8 loses to level 11: 6 ^^ (3 + 1)
    ("1 ^^ 1 == 0", True),  # ... and beats comparison, as in Python
    ("2 * 3^2", 18),
]


@pytest.mark.parametrize(("expression", "expected"), PRECEDENCE)
def test_precedence_and_associativity(expression, expected):
    """§3.2 R3, §4 R1-R3: ER2 adds no precedence level."""
    assert value(expression) == expected


def test_xor_needs_adjacent_carets():
    """§3.2 R2: ``^^`` is two adjacent tokens, ``^ ^`` is not."""
    assert value("6 ^^ 3") == 5
    with pytest.raises(SyntaxError):
        run("n = 6 ^ ^3\n")


# §5.3 — closure, and where it stops.
def test_er2_numbers_are_closed_under_arithmetic():
    """§5.3 R1: an operation on ER2 numbers yields ER2 numbers."""
    namespace = run("""
        a = 2 + 3
        b = 7 // 2
        c = 7 % 2
        d = abs(-5)
        e = sum([1, 2, 3])
        f = divmod(7, 2)[0]
        g = 1/3 + 2/3
        h = 1/2 + 1/3
    """)
    for name in "abcdefg":
        assert type(namespace[name]) is Integer, name
    assert type(namespace["h"]) is Rational


def test_library_values_stay_python_values():
    """§5.3 R2: ER2 does not change what Python or a library returns."""
    namespace = run("""
        import math

        a = len([1, 2])
        b = range(3)[1]
        c = math.factorial(5)
        d = "abc".count("a")
    """)
    for name in "abcd":
        assert type(namespace[name]) is int, name


def test_bool_is_untouched():
    """§5.3 R3: ``True`` is not an ``Integer``."""
    namespace = run("a = True\nb = 1 == True\nc = type(True)\n")
    assert namespace["a"] is True
    assert namespace["b"] is True
    assert namespace["c"] is bool


def test_integers_and_rationals_interchange_with_python():
    """§5.1 R3, §5.2 R2: hashing, equality and normalisation."""
    namespace = run("""
        a = {2: "two"}[2r]
        b = hash(2) == hash(2r)
        c = 1/3 + 2/3
        d = (1/3).denominator
    """)
    assert namespace["a"] == "two"
    assert namespace["b"] is True
    assert namespace["c"] == 1 and type(namespace["c"]) is Integer
    assert namespace["d"] == 3


# §6.2 — symbols.
def test_sym_binds_symbols_by_name():
    """§6.2 R1-R2: ``sym x`` binds the symbol named ``x``."""
    namespace = run("""
        sym x
        sym y, z
        same = (x == x)
        expression = (y + z)^2
    """)
    sympy = pytest.importorskip("sympy")
    for name in ("x", "y", "z"):
        assert isinstance(namespace[name], sympy.Symbol)
        assert namespace[name].name == name
    assert namespace["same"] is True
    assert (
        namespace["expression"] == (sympy.Symbol("y") + sympy.Symbol("z")) ** 2
    )


def test_symbols_are_equal_across_statements():
    """§6.2 R2: two symbols with the same name are interchangeable."""
    namespace = run("""
        sym x
        first = x
        sym x
        second = x
        equal = (first == second)
        combined = first + second
    """)
    assert namespace["equal"]
    assert namespace["combined"] == 2 * namespace["first"]


def test_predefined_symbols():
    """§6.2 R3-R4: ``_x`` is the symbol ``x``, and may be shadowed."""
    namespace = run("""
        sym x
        predefined = (_x == x)
        _x = 5
        shadowed = _x + 1
    """)
    assert namespace["predefined"]
    assert namespace["shadowed"] == 6


def test_prelude_does_not_shadow_user_names():
    """§6.1 R2: a program's own binding wins over the prelude."""
    namespace = run("""
        factor = "mine"
        latex = 3
        result = (factor, latex + 1)
    """)
    assert namespace["result"] == ("mine", 4)


def test_reserved_helpers_are_bound():
    """§3.3 R4, §3.5 R5: the generated code's helpers exist."""
    namespace = prelude.namespace()
    assert namespace["__er2_int__"](5) == 5
    assert type(namespace["__er2_int__"](5)) is Integer
    assert len(namespace["__er2_sym__"]("a, b")) == 2


# §2.3 — line numbers survive the translation, at run time.
def test_line_numbers_reach_the_traceback():
    """§2.3 R2: a traceback points at the ER2 line."""
    source = "x = 1\n\n\nraise ValueError(2^3)\n"
    try:
        exec(compile(preparse(source), "<spec>", "exec"), prelude.namespace())
    except ValueError as exc:
        assert exc.args[0] == 8
        assert exc.__traceback__.tb_next.tb_lineno == 4
    else:
        pytest.fail("the snippet must raise")


# The normative table itself (§3 R1).
def test_the_table_of_differences_is_the_whole_language():
    """§3 R1: the table is exhaustive; growing it is a language change."""
    text = SPEC.read_text(encoding="utf-8")
    section = text.split("### 3.1 Power")[0].split("## 3. The differences")[1]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    constructs = [row.split("|")[1].strip() for row in rows]
    header, separator, *body = constructs
    assert header == "Construct" and set(separator) <= set("- ")
    assert body == [
        "`a ^ b`",
        "`a ^^ b`",
        "`a ^= b`",
        "`a ^^= b`",
        "integer literal",
        "`5r`",
        "`sym x, y`",
        '`f"{a^2=}"`',
    ], "adding a difference to ER2 requires a recorded decision (§12 R1)"


def test_architecture_points_at_the_specification():
    """M7 task 2: §1.1 links to the specification instead of restating it."""
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    section = architecture.split("## 1.2 ")[0].split("## 1.1 ")[1]
    assert "docs/LANGUAGE.md" in section
    # The table lived here until M7; it must not be duplicated.
    assert "| `a ^^ b`" not in section


def test_every_test_cited_by_the_specification_exists():
    """Appendix B: a rule with no test is a defect in the specification."""
    text = SPEC.read_text(encoding="utf-8")
    appendix = text.split("## Appendix B")[1]
    cited = set(re.findall(r"`(tests/[\w/]+\.py)`", appendix))
    assert cited, "Appendix B cites no test"
    missing = sorted(name for name in cited if not (ROOT / name).exists())
    assert not missing, f"cited but absent: {missing}"


def test_every_rule_identifier_is_well_formed():
    """Appendix B: rules are cited by identifier, so they must be unique."""
    text = SPEC.read_text(encoding="utf-8")
    headings = re.findall(r"^#{2,3} (\S+)", text, re.MULTILINE)
    numbered = [h for h in headings if re.fullmatch(r"\d+(\.\d+)?", h)]
    assert len(numbered) == len(set(numbered)), "duplicate section number"


# Acceptance for M7: "every statement in it is backed by a test".
#
# COVERAGE maps every rule of the specification either to the test file
# that exercises it, or to "policy" for the statements of intent that
# describe how the project will behave rather than how the language does
# (§12).  The test below fails when a rule is added to the specification
# without deciding which of the two it is, so the mapping cannot silently
# fall behind the document.
PREPARSER = "tests/preparser/test_preparser.py"
COMPAT = "tests/compat/test_compat.py"
SCIENTIFIC = "tests/compat/test_scientific.py"
NUMBERS = "tests/runtime/test_numbers.py"
HERE = "tests/test_language_spec.py"
PRINTING = "tests/test_printing.py"
NOTEBOOKS = "tests/notebooks/test_notebooks.py"

COVERAGE = {
    "§1.1 R1": COMPAT,
    "§1.1 R2": COMPAT,
    "§1.2 R3": "tests/test_cli.py",
    "§1.2 R4": COMPAT,
    "§2.1 R1": PREPARSER,
    "§2.1 R2": PREPARSER,
    "§2.2 R1": PREPARSER,
    "§2.3 R1": PREPARSER,
    "§2.3 R2": HERE,
    "§2.4 R1": PREPARSER,
    "§2.4 R2": PREPARSER,
    "§2.4 R3": HERE,
    "§2.4 R4": PREPARSER,
    "§3 R1": HERE,
    "§3.1 R1": PREPARSER,
    "§3.1 R2": HERE,
    "§3.2 R1": PREPARSER,
    "§3.2 R2": HERE,
    "§3.2 R3": HERE,
    "§3.3 R1": PREPARSER,
    "§3.3 R2": PREPARSER,
    "§3.3 R3": PREPARSER,
    "§3.3 R4": HERE,
    "§3.4 R1": PREPARSER,
    "§3.4 R2": PREPARSER,
    "§3.4 R3": PREPARSER,
    "§3.5 R1": PREPARSER,
    "§3.5 R2": PREPARSER,
    "§3.5 R3": PREPARSER,
    "§3.5 R4": PREPARSER,
    "§3.5 R5": HERE,
    "§3.6 R1": PREPARSER,
    "§3.6 R2": COMPAT,
    "§4 R1": HERE,
    "§4 R2": HERE,
    "§4 R3": HERE,
    "§5.1 R1": NUMBERS,
    "§5.1 R2": NUMBERS,
    "§5.1 R3": HERE,
    "§5.2 R1": NUMBERS,
    "§5.2 R2": HERE,
    "§5.2 R3": NUMBERS,
    "§5.3 R1": HERE,
    "§5.3 R2": HERE,
    "§5.3 R3": HERE,
    "§5.4 R1": SCIENTIFIC,
    "§5.4 R2": SCIENTIFIC,
    "§5.4 R3": SCIENTIFIC,
    "§5.4 R4": SCIENTIFIC,
    "§6.1 R1": HERE,
    "§6.1 R2": HERE,
    "§6.1 R3": "tests/test_lazy_sympy.py",
    "§6.2 R1": HERE,
    "§6.2 R2": HERE,
    "§6.2 R3": HERE,
    "§6.2 R4": HERE,
    "§7 R1": "tests/test_dispatch.py",
    "§7 R2": "tests/test_linear_algebra.py",
    "§7 R3": "tests/test_series.py",
    "§7 R4": "tests/backends/test_pari_types.py",
    "§7 R5": "tests/backends/test_pari_closures.py",
    "§8.2 R1": "tests/backends/test_sympy_backend.py",
    "§8.2 R2": PRINTING,
    "§8.2 R3": "tests/backends/test_sympy_backend.py",
    "§8.3 R1": "tests/backends/test_pari_backend.py",
    "§8.3 R2": "tests/test_pari_functions.py",
    "§8.3 R3": "tests/test_pari_functions.py",
    "§9 R1": PRINTING,
    "§9 R2": PRINTING,
    "§9 R3": "tests/test_latex_coverage.py",
    "§9 R4": PRINTING,
    "§10 R1": NOTEBOOKS,
    "§10 R2": NOTEBOOKS,
    "§10 R3": NOTEBOOKS,
    "§10 R4": NOTEBOOKS,
    "§10 R5": NOTEBOOKS,
    "§11.1 R1": COMPAT,
    "§11.1 R2": COMPAT,
    "§11.1 R3": SCIENTIFIC,
    "§11.2 R1": PREPARSER,
    # §12 is the stability policy: promises about how the project will
    # behave, which no test can check.  The guard is that the table of
    # differences cannot grow unnoticed (test above).
    "§12 R1": "policy",
    "§12 R2": "policy",
    "§12 R3": "policy",
    "§12 R4": "policy",
    "§12 R5": "policy",
}


def spec_rules():
    """Return every rule identifier the specification defines, in order."""
    section = None
    rules = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^#{2,3} (§?[\d.]+)", line)
        if heading:
            section = heading.group(1).rstrip(".")
        rule = re.match(r"^\*\*(?:§[\d.]+ )?(R\d+)\.\*\*", line)
        if rule and section:
            rules.append(f"§{section} {rule.group(1)}")
    return rules


def test_every_rule_is_mapped_to_a_test():
    """M7 acceptance: no rule may be added without deciding its test."""
    rules = spec_rules()
    assert len(rules) > 50, "the rules stopped being recognised"
    unmapped = [rule for rule in rules if rule not in COVERAGE]
    assert not unmapped, f"rules with no entry in COVERAGE: {unmapped}"
    stale = [rule for rule in COVERAGE if rule not in rules]
    assert not stale, f"COVERAGE names rules the spec no longer has: {stale}"


def test_the_mapped_test_files_exist():
    """A rule may not point at a test file that is not there."""
    missing = sorted(
        {
            path
            for path in COVERAGE.values()
            if path != "policy" and not (ROOT / path).exists()
        }
    )
    assert not missing, f"COVERAGE points at absent files: {missing}"


def test_only_the_stability_policy_is_untestable():
    """Everything but §12 must point at a real test file."""
    policy = {r for r, path in COVERAGE.items() if path == "policy"}
    assert policy == {f"§12 R{n}" for n in range(1, 6)}
