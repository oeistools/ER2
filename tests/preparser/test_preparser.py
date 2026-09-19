"""ER2 → Python translation (ARCHITECTURE.md §3.1)."""

import warnings

import pytest

from er2.preparser import ER2Warning, IncompleteSourceError, preparse

I = "__er2_int__"  # noqa: E741 - short alias keeps the expected code readable


@pytest.mark.parametrize(
    ("er2", "python"),
    [
        # Power and XOR.
        ("a ^ b\n", "a ** b\n"),
        ("a ^^ b\n", "a ^ b\n"),
        ("a ^= b\n", "a **= b\n"),
        ("a ^^= b\n", "a ^= b\n"),
        ("-x^y^z\n", "-x**y**z\n"),
        # Integer literals.
        ("n = 5\n", f"n = {I}(5)\n"),
        (
            "n = 0x1F + 0b101 + 0o7 + 1_000\n",
            f"n = {I}(0x1F) + {I}(0b101) + {I}(0o7) + {I}(1_000)\n",
        ),
        ("r = 1.5 + 1e3 + 2j\n", "r = 1.5 + 1e3 + 2j\n"),
        # Literal patterns compare with ==, so they stay plain; guards and
        # bodies are ordinary code.
        (
            "match v:\n    case 0 | -1 | [2, *_]: pass\n",
            "match v:\n    case 0 | -1 | [2, *_]: pass\n",
        ),
        (
            "match v:\n    case P(x=1) if n > 2: y = 3^2\n",
            f"match v:\n    case P(x=1) if n > {I}(2): y = {I}(3)**{I}(2)\n",
        ),
        (
            'match v:\n    case {"é": 1}: pass\n',
            'match v:\n    case {"é": 1}: pass\n',
        ),
        ("case = 5\n", f"case = {I}(5)\n"),
        # sym statements.
        ("sym x\n", 'x, = __er2_sym__("x")\n'),
        ("sym x, y\n", 'x, y = __er2_sym__("x, y")\n'),
        ("sym x  # comment\n", 'x, = __er2_sym__("x")  # comment\n'),
        ("sym x; y = x\n", 'x, = __er2_sym__("x"); y = x\n'),
        ("if c: sym t\n", 'if c: t, = __er2_sym__("t")\n'),
        ("def f():\n    sym t\n", 'def f():\n    t, = __er2_sym__("t")\n'),
    ],
)
def test_translation(er2, python):
    assert preparse(er2) == python


@pytest.mark.parametrize(
    "source",
    [
        # ``sym`` as an ordinary name stays plain Python (D4).
        "sym = x\n",
        "sym(x)\n",
        "print(sym)\n",
        "sym.x\n",
        "sym[i]\n",
        "a = sym\n",
        "sym x y\n",
        "sym if\n",
        # Strings and comments are never touched.
        's = "2^3 and sym x"\n',
        "s = '''a ^ b\n5 ^^ 6'''\n",
        "# 2^3 sym x\n",
        # Floats and complex literals are Python's (D2b).
        "r = 0.1\n",
    ],
)
def test_untouched(source):
    assert preparse(source) == source


def test_fstring_literal_text_is_untouched():
    code = 'f"{a^2} ^ {b!r:>5}"\n'
    assert preparse(code) == f'f"{{a**{I}(2)}} ^ {{b!r:>5}}"\n'


def test_line_numbers_are_preserved():
    source = "a = 1\n\\\n    + 2\nsym x\n\n'''\nx ^ 2\n'''\nb = a ^ 2\n"
    assert preparse(source).count("\n") == source.count("\n")
    assert preparse(source).splitlines()[-1] == f"b = a ** {I}(2)"


def test_plain_python_without_literals_is_unchanged():
    source = (
        "import math\n"
        "class A:\n"
        "    def f(self, x: float) -> float:\n"
        "        return math.sqrt(x)\n"
        "match A:\n"
        "    case _:\n"
        "        pass\n"
    )
    assert preparse(source) == source


def test_sym_statement_must_fit_on_one_line():
    with pytest.raises(SyntaxError):
        preparse("sym x, \\\n  y\n")


def test_incomplete_source():
    with pytest.raises(IncompleteSourceError):
        preparse("f(1,\n")
    with pytest.raises(IncompleteSourceError):
        preparse('s = """abc\n')


def test_xor_warning():
    with pytest.warns(ER2Warning):
        preparse("mask = 0xFF ^ flags\n")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        preparse("y = x ^ 2\n")
