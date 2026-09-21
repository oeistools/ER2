# The ER2 Language

**Normative specification.** Version 0.7 (draft for 1.0).

This document defines the ER2 language: what an ER2 source file is, how it differs from Python,
and what a conforming implementation must do. It is the single source of truth for the language.
Where [ARCHITECTURE.md](../ARCHITECTURE.md) explains *why* a rule exists, this document states
*what* the rule is; where the two disagree, this document wins.

`docs/LANGUAGE.md` describes the language. It does not document the library: the mathematical
functions are listed in [PARI_FUNCTIONS.md](PARI_FUNCTIONS.md) and in their docstrings.

## Conventions

**MUST**, **MUST NOT** and **MAY** have their usual force: a translator that breaks a MUST is not
an ER2 implementation.

Every normative rule has an identifier, `§2.3 R1`. Appendix B maps each one to the test that
would fail if the rule changed; a rule with no test is a defect in this specification.

Throughout, **Python** means CPython 3.12 or later, and *the translation* of an ER2 source is the
Python source an implementation produces from it.

---

## 1. Scope

### 1.1 What ER2 is

ER2 is a **superset of Python**. Its implementation is a source-to-source translator (the
*preparser*) followed by unmodified CPython, plus a runtime library.

**R1.** Every syntactically valid Python program is a syntactically valid ER2 program.

**R2.** A Python program that contains none of the constructs in §3 has the same meaning in ER2
as in Python.

R2 is the whole compatibility contract, and §3 is exhaustive: the constructs listed there are the
*only* places where ER2 and Python differ. A construct that is not in §3's table behaves as
Python defines it, including constructs added to Python after this document was written.

### 1.2 What is preparsed

**R3.** An implementation MUST preparse exactly these sources:

- files with the `.er2` suffix, run directly or imported;
- input typed at the ER2 REPL;
- notebook cells in a session where ER2 is active (§10).

**R4.** An implementation MUST NOT preparse anything else. In particular `.py` files, installed
libraries and the standard library are executed as plain Python, whether they are imported from
ER2 code or not.

R3 and R4 are what make the ecosystem usable: `import numpy` from an ER2 file gets the real
NumPy, translated by nobody.

### 1.3 Conformance

A conforming implementation:

1. implements the translation of §2 and §3 exactly;
2. provides the number model of §5;
3. provides the prelude names of §6 with the meanings given there;
4. produces the representations of §9.

Backends are not part of conformance: §7 constrains *which answer* a function gives, not which
library computes it.

---

## 2. The translation

### 2.1 Token-based

**§2.1 R1.** The translation MUST operate on Python's token stream (`tokenize`), never on the raw
text. A construct of §3 is recognised only when it appears as a token or a sequence of adjacent
tokens.

The consequence, and the reason for the rule:

**§2.1 R2.** Text inside a string literal, a byte literal, a comment, or the literal part of an
f-string MUST NOT be translated.

```er2
s = "2^3"          # the string is unchanged; it prints 2^3
n = 2^3            # the code is translated; n is 8
# sym x            # a comment; declares nothing
```

The one exception is the self-documenting f-string of §3.6, where Python itself echoes source
text and ER2 must echo the *ER2* text.

### 2.2 Two passes

**§2.2 R1.** The translation MUST be performed in two passes:

1. **Pass 1** rewrites, on the ER2 token stream: power and XOR operators (§3.1, §3.2), `sym`
   statements (§3.5), self-documenting f-strings (§3.6), and removes the `r` suffix of raw
   literals (§3.4), recording their positions.
2. **Pass 2** re-tokenises the result of pass 1 — which is valid Python — and wraps integer
   literals (§3.3), skipping the positions recorded in pass 1 and the literals inside `case`
   patterns.

The order matters and is normative. Pass 2 needs a parseable source, because `case` patterns can
only be located by parsing (§3.3 R3); and pass 1 produces one, because none of its rewrites
depends on integer literals being wrapped.

### 2.3 Line numbers and columns

**§2.3 R1.** Every rewrite MUST stay on the line of the token it replaces. A translation MUST
NOT add, remove or reorder lines.

**§2.3 R2.** Line *n* of an ER2 source therefore corresponds to line *n* of its translation, so
tracebacks, `linecache`, debuggers and notebook cell offsets point at the right ER2 line.

Columns are not preserved: a wrapped literal is longer than the literal. An implementation MAY
report a column that is shifted within the correct line.

### 2.4 Errors

**§2.4 R1.** Source that cannot be tokenised MUST raise `SyntaxError`, carrying the file name and
the line where tokenising failed.

**§2.4 R2.** Source that ends inside an open bracket or an unterminated multi-line string MUST
raise a distinguishable subclass of `SyntaxError` (`er2.preparser.IncompleteSourceError`), so
that the REPL can ask for another line instead of reporting an error.

**§2.4 R3.** Source that is valid ER2 but whose translation is invalid Python MUST be reported by
CPython at compile time, at the correct line (§2.3 R2). The translator does not check syntax it
does not create.

**§2.4 R4.** A `^` that shares a line with an obvious bit-manipulation operand — a hexadecimal or
binary literal, `&`, `|`, `<<`, `>>` or `~`, outside comments — SHOULD raise `er2.preparser.ER2Warning`
at that line. This is a diagnostic for Python code pasted into an `.er2` file (§11.2); it does
not change the meaning of the program, which is always power.

---

## 3. The differences from Python

**§3 R1.** This table is exhaustive. An implementation MUST NOT introduce another difference, and
a change to this table is a change to the language.

| Construct     | Python                 | ER2                                                    |
|---------------|------------------------|--------------------------------------------------------|
| `a ^ b`       | XOR                    | power, `a ** b`                                        |
| `a ^^ b`      | syntax error           | XOR, Python's `a ^ b`                                  |
| `a ^= b`      | XOR-assign             | power-assign, `a **= b`                                |
| `a ^^= b`     | syntax error           | XOR-assign, Python's `a ^= b`                          |
| integer literal | `int`                | `Integer` (§5.1), so `1/3` is the rational 1/3          |
| `5r`          | syntax error           | raw literal: the plain Python `int` 5                  |
| `sym x, y`    | syntax error           | symbol declaration                                     |
| `f"{a^2=}"`   | echoes the source text | echoes the **ER2** source text                         |

Four of the eight rows are syntax errors in Python, so they cannot change the meaning of any
Python program. The other four are the real cost of ER2, and §11 states what it buys.

### 3.1 Power: `^` and `^=`

**R1.** A `^` operator token MUST be translated to `**`, and `^=` to `**=`, unless it is part of
a `^^` or `^^=` sequence (§3.2).

**R2.** The translated operator keeps Python's `**` precedence and associativity (§4).

```er2
2^10        # 1024
2^3^2       # 512, right-associative: 2^(3^2)
-2^2        # -4, the power binds tighter than the unary minus
2^-1        # 1/2, a Rational (§5.1)
x^2 + 1     # symbolic, if x is a symbol
```

### 3.2 XOR: `^^` and `^^=`

**R1.** Two `^` tokens that are **adjacent** — the second starts at the column where the first
ends — MUST be translated to a single `^`, Python's XOR. `^` immediately followed by `^=` MUST
be translated to `^=`.

**R2.** Adjacency is required: `a ^ ^b` is not `^^`, and is a syntax error after translation.

**R3.** `^^` has the precedence of Python's `^`, **not** the precedence of ER2's `^`.

R3 is the one place where an ER2 operator's precedence is not what its spelling suggests, and it
follows from R1: the translation *is* Python's XOR, with Python's precedence.

```er2
6 ^^ 3          # 5
6 ^^ 3 + 1      # 2, i.e. 6 ^^ (3 + 1) — Python's XOR precedence
2 ^ 3 + 1       # 9, i.e. (2^3) + 1 — power binds tighter than +
```

### 3.3 Integer literals

**R1.** Every integer literal token MUST be translated to a call `__er2_int__(literal)`, where
the literal's text is reproduced unchanged, except as R2 and R3 provide.

**R2.** A literal that is not an integer MUST be left alone: floats (`1.5`, `1e3`), imaginary
literals (`2j`), and the numeric parts of anything else. ER2 does not change Python's
floating-point model (D2b).

**R3.** An integer literal inside a `case` pattern MUST be left alone.

R3 exists because a `match` statement compares a literal pattern with `==`, where an `Integer` is
not needed, and because `case Integer(5):` would be read as a *class pattern* and change the
meaning of the program. Guards and bodies are ordinary code and are translated normally.

```er2
match value:
    case 0 | -1: ...        # patterns: plain ints
    case n if n > 2: ...    # the guard is translated
```

**R4.** The name `__er2_int__` MUST be bound in every ER2 namespace (§6) to a callable that
returns the `Integer` (§5.1) equal to its argument. The name is reserved: user code MUST NOT be
able to shadow it by ordinary means, which is why it is spelled as a dunder.

An implementation MAY cache the `Integer` for a literal, since `Integer` is immutable.

### 3.4 Raw literals: `5r`

**R1.** An integer literal immediately followed by the name `r` — no space, no other character —
is a *raw literal*. It MUST be translated by deleting the `r`, and MUST NOT be wrapped by §3.3.
Its value is therefore a plain Python `int`.

**R2.** The suffix applies to every integer literal form: `0x1Fr`, `0b101r`, `1_000r`.

**R3.** There is no raw float: `1.5r` is not a raw literal, because §3.4 R1 requires an integer.

```er2
type(5)         # Integer
type(5r)        # int
5r / 2          # 5/2, a Rational: an operation with an ER2 number gives an ER2 result
5r / 2r         # 2.5, a float: Python's semantics all the way
```

The last two lines are the point of the feature and follow Sage's convention: `r` opts one
*literal* out, not the expression around it. It is an escape hatch for hot numeric loops and for
code that needs Python's `int` exactly (D2).

### 3.5 `sym`

`sym` is a **soft keyword**: it is a keyword only at the start of a statement, and an ordinary
name everywhere else (D4).

**R1.** A `sym` statement is recognised when all of the following hold:

1. a `NAME` token whose text is `sym`;
2. it is the **first token of a statement** — the previous significant token is a `NEWLINE`,
   `NL`, `INDENT`, `DEDENT` or the start of the file, or it is `;` or `:`;
3. it is followed by one or more `NAME` tokens that are not Python keywords, separated by commas;
4. the last of those names is followed by end of statement — `NEWLINE`, `;` or end of file.

Comments are not significant for (2) and (4).

**R2.** A recognised `sym NAME₁, …, NAMEₙ` MUST be translated to

```python
NAME₁, …, NAMEₙ, = __er2_sym__("NAME₁, …, NAMEₙ")
```

with the trailing comma present when *n* = 1, so that a single name is unpacked rather than
assigned the tuple.

**R3.** A `sym` that fails any condition of R1 MUST be left alone, and is then an ordinary Python
name.

```er2
sym x                # x, = __er2_sym__("x")
sym x, y             # x, y = __er2_sym__("x, y")
if c: sym t          # after ':' — a sym statement
sym x; y = x^2       # after ';' — a sym statement
sym = 3              # ordinary name: assignment
sym(x)               # ordinary name: a call
d = {"sym": 1}       # a string
sym x y              # not recognised (no comma); a SyntaxError from CPython
```

**R4.** A `sym` statement MUST fit on one line. A `sym` whose names span a line continuation MUST
raise `SyntaxError` at the line of the `sym`.

R4 is a consequence of §2.3 R1: the rewrite cannot span lines, so the language forbids the case
rather than silently mistranslating it.

**R5.** `__er2_sym__` MUST be bound in every ER2 namespace (§6) to a callable that takes one
comma-separated string of names and returns a tuple of symbols (§6.2), one per name, in order.

### 3.6 Self-documenting f-strings

Python's `f"{expr=}"` echoes the *source text* of the expression. Translated naively, an ER2
program would echo its translation — `f"{2^3=}"` would print `2**__er2_int__(3)=`.

**R1.** In a replacement field of the form `{expr=}`, an implementation MUST replace the echoed
text with the **ER2** source text of `expr`, as a literal part of the f-string, and MUST produce
the same value and conversion Python would: `!r` when the field has neither a conversion nor a
format specification, and neither otherwise.

```er2
f"{2^3=}"       # '2^3=8'
f"{n=:>4}"      # 'n=   8', the format spec is honoured, no !r
```

**R2.** A field whose echoed text cannot be written as a literal part of that string — it
contains a backslash or the string's own quote character — or which spans more than one line, MAY
be left untranslated. Such a field then echoes the translation; this is a known, documented gap
rather than a rule of the language.

R1 covers `{expr=}` only. Every other replacement field is ordinary code, translated by §3.1–§3.5
like any other expression.

---

## 4. Precedence and associativity

**R1.** ER2 adds no precedence level. Every operator has the precedence and associativity of the
Python operator it translates to.

From lowest to highest, with the ER2 rows marked:

| Level | Operators                                        |
|-------|--------------------------------------------------|
| 1     | `lambda`, `:=`                                   |
| 2     | `if … else`                                      |
| 3     | `or`                                             |
| 4     | `and`                                            |
| 5     | `not x`                                          |
| 6     | `in`, `not in`, `is`, `is not`, `<`, `<=`, `>`, `>=`, `!=`, `==` |
| 7     | `\|`                                             |
| 8     | **`^^`** (XOR)                                   |
| 9     | `&`                                              |
| 10    | `<<`, `>>`                                       |
| 11    | `+`, `-`                                         |
| 12    | `*`, `@`, `/`, `//`, `%`                         |
| 13    | `+x`, `-x`, `~x`                                 |
| 14    | **`^`** (power), right-associative               |
| 15    | `await x`                                        |
| 16    | `x[…]`, `x(…)`, `x.attr`                         |

Two consequences worth stating, because they are where a Python reader's intuition is wrong:

**R2.** `^` binds **tighter** than unary minus on its left and looser on its right, exactly as
Python's `**`: `-2^2` is `-4`, and `2^-1` is `1/2`.

**R3.** `^^` sits at level 8, far below `^` at level 14. `a ^^ b + c` is `a ^^ (b + c)`, while
`a ^ b + c` is `(a ^ b) + c`.

---

## 5. Numbers

### 5.1 `Integer`

**R1.** `Integer` MUST be a subclass of Python's `int`.

R1 is the load-bearing decision of the number model (D6). Because `Integer` *is* an `int`,
`isinstance(n, int)` is true, `__index__` works, and every library that type-checks integers
accepts ER2 numbers without knowing ER2 exists.

**R2.** Arithmetic on `Integer` MUST agree with `int` in value, and return `Integer`, with these
exceptions:

- `a / b` with `b` an integer returns the **exact** quotient: `Integer` when it divides, else
  `Rational`. It does not return a `float`.
- `a ^ b` with `b` negative returns a `Rational`.
- `a / 0` raises `ZeroDivisionError`.

```er2
type(2 + 3)     # Integer
type(7 // 2)    # Integer
1/3             # 1/3, a Rational — not 0.333…
2^-1            # 1/2
2 + 0.5         # 2.5, a float: mixing with float is Python's rule
```

**R3.** `hash(Integer(n)) == hash(n)`, and `Integer(n) == n`, so ER2 numbers and Python numbers
are interchangeable as dictionary keys and in sets.

### 5.2 `Rational`

**R1.** `Rational` MUST be a subclass of `fractions.Fraction`, always in lowest terms.

**R2.** An operation whose exact result is an integer MUST return an `Integer`, not a `Rational`
with denominator 1: `1/3 + 2/3` is the `Integer` 1.

**R3.** `repr(Rational(1, 3))` is `1/3` (§9).

### 5.3 Closure, and where it stops

**R1.** ER2 numbers are closed under arithmetic: an operation on ER2 numbers yields ER2 numbers.

**R2.** ER2 does **not** change what Python or a library returns. `len(lst)`, `range(3)[1]` and
`math.factorial(5)` return plain `int`, in ER2 as in Python.

R1 and R2 together are the whole boundary rule, and they are consistent: `sum([1, 2])` is an
`Integer` because it adds `Integer`s to `0`, while `len([1, 2])` is an `int` because `len` is
Python's. Values become ER2 numbers by being written as literals, by arithmetic with ER2
numbers, or by coming out of an ER2 function (§8.1) — never by passing through a library.

**R3.** `bool` is untouched. `True` is not an `Integer`, and `1 == True` remains true.

### 5.4 Crossing into the scientific stack

**R1.** ER2 numbers MUST implement `__index__`, `__int__`, `__float__`, `__complex__` and
`__hash__`, so that indexing, slicing, `range`, `json`, `math` and array constructors work.

R2 to R4 are not requirements on ER2 — no ER2 code runs in them — but observable consequences
of R1 and §5.1 R1. They are specified because programs depend on them, and each is tested.

**R2.** `Integer` gets a real integer dtype everywhere, because it is an `int`:
`np.array([2^3, 3^2]).dtype` is an integer dtype, a pandas column of `Integer` is `int64`, and
SciPy accepts it as an argument, as a shape and as an interval bound.

**R3.** `Rational` is not a machine number, and the stack splits on it:

| Library | Result |
|---|---|
| NumPy | an **object array**; `1/3` stays `1/3` |
| pandas | an **object column**, with exact arithmetic: `Series([1/2, 1/3]).sum()` is `5/6` |
| SciPy | a **`TypeError`**: a ufunc has no object fallback |

**R4.** The conversion is never implicit. A program that wants machine floats asks for them with
`float(...)`.

R3 and R4 are one deliberate answer, not a gap. Converting to `float64` behind the user's back
would discard the exactness ER2 exists to preserve, which is why SciPy's refusal is preferable to
a silent approximation.

---

## 6. Namespaces and the prelude

### 6.1 The prelude

**R1.** Every ER2 namespace — a program's `__main__`, an imported `.er2` module, the REPL, an ER2
notebook session — MUST be initialised with the prelude: `__er2_int__`, `__er2_sym__`, the
mathematical functions (§7), the mathematical types, `pari`, `latex` and `show`.

**R2.** The prelude MUST NOT shadow a name the program defines or imports. A program's own
binding wins.

**R3.** An implementation MAY populate parts of the prelude lazily, provided the observable
namespace is the same. (ER2 omits the SymPy-valued names when a program's compiled code never
mentions them, so a number-theory program does not pay SymPy's import time.)

### 6.2 Symbols

**R1.** A symbol is a SymPy `Symbol`. `sym x` binds the name `x` to the symbol named `"x"`.

**R2.** Two symbols with the same name are equal and interchangeable, whichever statement created
them.

**R3.** The prelude MUST predefine `_x`, `_y`, `_z`, `_n`, `_k`, `_p` as the symbols `x`, `y`,
`z`, `n`, `k`, `p` (D3), so that a one-line expression needs no declaration.

**R4.** The predefined names are ordinary bindings and MAY be shadowed by assignment.

```er2
_x^2 + 1            # x^2 + 1, no declaration needed
sym x
x^2 + 1             # the same expression
```

---

## 7. Functions and dispatch

**R1.** The public mathematical functions are **generic**: one name accepts every type for which
the operation makes sense, and the implementation chooses how to compute it.

**R2.** The choice of backend MUST NOT be observable in the answer. When two backends can compute
the same call, they MUST return equal results, in the same type and the same normal form.

R2 is what makes R1 safe: `factor(f)` may go to PARI or to SymPy depending on the polynomial's
shape, and a program cannot tell which. An implementation is free to change the routing for
speed; it is not free to change an answer.

**R3.** A documented exception to R2 requires a recorded decision and a test that pins it. There
is exactly one (D21): `expand` of a *quotient* of truncated power series returns the series
expansion, where `sympy.expand` returns nested fractions and does not answer at all.

**R4.** Conversion between representations MUST happen only at the backend boundary. A user MUST
NOT receive a raw `cypari2.gen`, and MUST NOT need to know that PARI was involved.

**R5.** No backend object may outlive the call that produced it. ER2 types store plain Python
data.

R5 is what makes `pari.set_stack` — which discards PARI's stack — safe to call at any time.

---

## 8. Conversions

### 8.1 ER2 ↔ Python

| From | To | Rule |
|---|---|---|
| int literal | `Integer` | §3.3 |
| `5r` | `int` | §3.4 |
| `Integer`, `Rational` | `int`, `float`, `complex` | explicit: `int(n)`, `float(q)` |
| a library's `int` | stays `int` | §5.3 R2 |

### 8.2 ER2 ↔ SymPy

**R1.** A SymPy integer or rational returned through an ER2 function MUST be converted to
`Integer` or `Rational`, including inside lists, tuples, sets and dicts (as `solve` returns).

**R2.** A symbolic result stays a SymPy expression, printed in ER2 notation (§9).

**R3.** A method called directly on a SymPy object — `f.subs(x, 2)` — bypasses ER2 and returns
SymPy numbers. That is Python's attribute access, not an ER2 call, and §1.1 R2 requires it to
behave as it does in Python.

### 8.3 ER2 ↔ PARI

**R1.** Conversion is performed by `to_pari` and `from_pari` at the boundary, per §7 R4.

**R2.** `pari.<name>` exposes PARI's own functions for what the curated prelude does not cover
(D10). Results still cross the boundary: `pari.eulerphi(10)` returns an `Integer`.

**R3.** ER2 names are not PARI names. ER2 uses PEP 8 mathematical names — `phi`, `mu`,
`bigomega`, `dedekind_psi` — mapped to PARI's in
[er2/data/pari_functions.csv](../er2/data/pari_functions.csv). There is no bare `psi` (D5).

---

## 9. Representation and output

**R1.** Mathematical values MUST print in mathematical notation, with `^` for powers:
`x^2 + 2*x + 1`, `2^3 * 3^2`, `1/3`.

**R2.** ER2 printing MUST be installed only by an ER2 entry point — a program, the REPL, a
notebook session. A plain `import er2` from a Python program MUST NOT change SymPy's printing
globally (D11).

R2 keeps ER2 a good citizen: importing the library into someone else's Python program changes
nothing they can see.

**R3.** Every mathematical type MUST support `latex(obj)`, and MUST define `_repr_latex_` by
calling it, so that Jupyter and Quarto render it as mathematics.

**R4.** `latex()` returns a `str` subclass that renders as math in a notebook and as inline math
in a Quarto inline expression, and is otherwise an ordinary string.

---

## 10. Notebooks

**R1.** ER2 MUST run in Jupyter and in Quarto, through either route:

- the **`er2` kernel**, which installs the preparser as an input transformer at startup;
- `%load_ext er2` in a standard `python3` kernel.

**R2.** The kernel's declared language MUST be `python`, and cells MUST be written
`` ```{python} `` (D9).

R2 is not a preference. Quarto decides whether a block is executable from its language *before
the kernel is consulted*: a `` ```{er2} `` block is never executed, and the render still exits 0,
so the failure is silent. Declaring `python` also keeps every editor's Python tooling working,
which is what a superset should do.

**R3.** A document MAY be *displayed* as ER2 without changing what is executed, by relabelling
the language after execution (`examples/er2-cells.lua`) and highlighting it with a syntax
definition (`examples/er2.xml`). Both are presentation only.

**R4.** With the `er2` kernel, Quarto inline expressions `` `{python} x^2` `` are preparsed and
accept ER2 syntax. With `%load_ext er2` they are **not**, because Quarto evaluates them through
`user_expressions` rather than cell execution; inline expressions must then use Python syntax.

**R5.** Tracebacks in a notebook MUST point at the right cell line, by §2.3 R2.

---

## 11. Python compatibility

### 11.1 What is guaranteed

**R1.** Every Python construct is valid ER2: classes, decorators, generators, `async`, `match`,
comprehensions, f-strings, type hints, `with`, `try`, walrus, `if __name__ == "__main__"`. The
translation rewrites tokens, never structure.

**R2.** `import` is Python's. An `.er2` module can be imported like any other module; a `.py`
module of the same name wins, and Python's own finders stay in place behind ER2's.

**R3.** An ER2 value passed to a library behaves as the corresponding Python value (§5.4).

### 11.2 The known caveat

**R1.** Python code **pasted into** an `.er2` file changes meaning if it relies on `^` being XOR
or on `int / int` being a float. This is the deliberate cost of §3, and it is bounded: it affects
pasted code, never imported code.

Mitigations, in order of preference: keep such code in `.py` modules and import it (§1.2 R4);
write `^^` for XOR; heed the warning of §2.4 R4.

---

## 12. Stability

**R1.** Before 1.0, the constructs of §3 are **stable**: a change to that table requires a
recorded decision, and none is planned.

**R2.** The number model of §5 is stable.

**R3.** The set of public function *names* (§7) may still grow. A name's *meaning* may change
only through a recorded decision.

**R4.** Backend routing (§7 R1) is explicitly **not** stable and may change in any release,
because §7 R2 makes it unobservable.

**R5.** At 1.0 the syntax and the public API freeze, and change afterwards only through a
deprecation policy.

---

## Appendix A — Grammar of the additions

The additions, in the notation of the Python reference. Everything else is Python's grammar
unchanged.

```text
power        ::= (await_expr | primary) ["^" u_expr]        # was "**"
xor_expr     ::= and_expr | xor_expr "^^" and_expr          # was "^"

augtarget    ::= ...
augop        ::= ... | "^=" | "^^="                         # "^=" is power-assign

integer      ::= decinteger | bininteger | octinteger | hexinteger
er2_integer  ::= integer                                    # value: Integer
raw_integer  ::= integer "r"                                # value: int, no space before "r"

sym_stmt     ::= "sym" identifier ("," identifier)*
```

`sym_stmt` is a *statement*, recognised only at the start of one (§3.5 R1), and `identifier` MUST
NOT be a Python keyword.

## Appendix B — Conformance

Every rule above is mapped to a test. `tests/test_language_spec.py` holds the mapping as a
`COVERAGE` table, rule identifier by rule identifier, and three tests keep it honest: every rule
the document defines must have an entry, every entry must name a test file that exists, and the
only rules allowed to have no test are the five of §12, which are promises about how the project
will behave rather than statements about the language. Adding a rule without deciding how it is
checked therefore fails the suite.

`tests/test_language_spec.py` also pins the rules that had no test of their own — precedence,
symbol semantics, the conversion boundary — and guards the §3 table against growing. The table
below is the summary by area.

| Rules | Test |
|---|---|
| §2.1, §2.2, §2.3, §3.1–§3.6 (translation) | `tests/preparser/test_preparser.py` |
| §2.4 (errors and the warning) | `tests/preparser/test_preparser.py` |
| §1.1 R2, §11 (Python behaves as Python) | `tests/compat/test_compat.py` |
| §5.4 (NumPy and the scientific stack) | `tests/compat/test_scientific.py` |
| §5.1–§5.3 (the number model) | `tests/runtime/test_numbers.py`, `tests/test_language_spec.py` |
| §3.5, §6.2 (symbols) | `tests/test_language_spec.py` |
| §6.1 (the prelude) | `tests/test_lazy_sympy.py`, `tests/test_language_spec.py` |
| §7 R2 (both backends agree) | `tests/test_dispatch.py` and each backend's tests |
| §9 (printing and LaTeX) | `tests/test_printing.py`, `tests/test_latex_coverage.py` |
| §10 (notebooks and Quarto) | `tests/notebooks/test_notebooks.py` |
| Appendix A (precedence) | `tests/test_language_spec.py` |

A rule that acquires no test is a defect in this specification, not an optional one.
