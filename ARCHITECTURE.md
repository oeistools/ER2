# ER2 — Architecture

> Technical design document. Source of the idea: [draft/ER2_idea_summary.md](draft/ER2_idea_summary.md).
> Status: **pre-implementation** (no code yet).

## 1. What ER2 is

The name honors the Hungarian mathematician **Paul Erdős** — in Spanish, "Erdős" is pronounced like "ER-dos", i.e. *ER2*.

ER2 is **mathematical Python**: a superset of Python that adds symbolic syntax
(`sym x`, `x^2`, `_x`), exact arithmetic by default, and transparent access to PARI/GP.

It is neither a new language nor a new interpreter. In the 0.x releases, ER2 is:

1. a **source-to-source preparser** (`.er2` → valid Python),
2. a **runtime** (the `er2` package) that defines mathematical types and functions,
3. a set of **backends** (SymPy for symbolic work, PARI via cypari2 for number theory).

The generated code runs on unmodified CPython. A CPython fork is only considered for 2.0 (see §9).

Direct precedent: the SageMath *preparser* does exactly this
(`^`→`**`, integer literals wrapped in `Integer`). Study it before reinventing it.

## 1.1 Python compatibility contract

**Hard requirement:** ER2 must accept Python syntax without problems and give full access to the
Python ecosystem through ordinary `import`. Chosen model: **the SageMath model** (decided 2026-09-18).

1. **Only ER2 sources are preparsed**: `.er2` files, the `er2` REPL, and notebook cells with the ER2
   extension loaded. Every `.py` module and every installed library (NumPy, pandas, SciPy,
   Matplotlib, …) runs as plain, untouched Python.
2. **Imports are standard.** `import numpy as np` inside a `.er2` file uses Python's normal import
   system. The ER2 import hook only *adds* a finder for `.er2` modules; it never replaces or wraps
   the existing finders.
3. **Every Python construct is valid ER2**: classes, decorators, generators, `async`, `match`,
   comprehensions, f-strings, type hints, `with`, exceptions, `if __name__ == "__main__"`, … The
   preparser rewrites tokens, never syntax structure, so anything `ast.parse` accepts after
   preparsing keeps its Python meaning.
4. **The only semantic differences inside `.er2` sources** are, deliberately and exhaustively:

   | Construct   | Python                 | ER2                                  |
   |-------------|------------------------|--------------------------------------|
   | `a ^ b`     | XOR                    | power (`a ** b`)                     |
   | `a ^^ b`    | syntax error           | XOR (Python's `a ^ b`)               |
   | `a ^= b`    | XOR-assign             | power-assign (`a **= b`)             |
   | `a ^^= b`   | syntax error           | XOR-assign                           |
   | int literal | `int`                  | ER2 `Integer` (exact), so `1/3` is the rational 1/3 |
   | `sym x, y`  | syntax error           | symbol declaration                   |

   Anything not in this table behaves exactly as in Python. Adding a row requires updating this
   contract.
5. **Values cross into the ecosystem transparently.** ER2 numbers implement `__index__`,
   `__int__`, `__float__`, `__complex__`, `__hash__` (equal to the corresponding `int` hash) and
   compare equal to Python numbers, so `range(n)`, `lst[n]`, `np.zeros(n)`, `math.sqrt(n)`,
   dict keys and `json` keep working. See D6 for `isinstance(n, int)`.
6. **Escape hatches**: `int(...)`/`float(...)` for explicit conversion; a raw-literal suffix such as
   `5r` (Sage's convention) for a plain Python `int`, if needed (to be decided when implementing).
7. **Known caveat**: Python code pasted into a `.er2` file that relies on `^` being XOR, or on
   `int / int` returning `float`, changes meaning. Mitigations: the preparser warns on `^` between
   obvious bitmask operands (hex/binary literals, `&`, `|`, `<<` in the same expression); keep such
   code in `.py` modules and import it.

A dedicated **compatibility test suite** (`tests/compat/`) enforces this contract: plain Python
snippets whose behavior must be identical under ER2, imports of stdlib/third-party modules from
`.er2` code, and ER2 values passed into library functions.

## 2. Overview

```text
 .er2 source / Jupyter cell / REPL
              │
              ▼
 ┌─────────────────────────────┐
 │ er2.preparser               │  tokenize → transform tokens → untokenize
 │  - sym x, y   → assignments │  (NO regex over raw text: respects strings,
 │  - ^          → **          │   comments, f-strings)
 │  - literals   → Integer(…)  │
 └──────────────┬──────────────┘
                ▼
        valid Python (str)  ──►  ast.parse / compile  ──►  CPython
                                                               │
                        initial namespace = er2.prelude  ◄─────┘
                                        │
 ┌──────────────────────────────────────┴────────────────────────┐
 │ er2.runtime                                                    │
 │  types: Integer, Rational, Symbol, Expr, …                     │
 │  public functions: factor, expand, diff, isprime, phi, …       │
 │  er2.dispatch: picks a backend based on argument type          │
 │  er2.printing: mathematical output (x^2, not x**2)             │
 └───────────────┬────────────────────────────┬───────────────────┘
                 ▼                            ▼
     er2.backends.sympy            er2.backends.pari
          SymPy                  cypari2 → libpari
```

## 3. Components

### 3.1 Preparser (`er2/preparser.py`)

Input: ER2 text. Output: equivalent Python text. A pure, stateless function that is easy to test
with input/output pairs.

Transformations (0.1):

| ER2                | Generated Python                                  | Notes |
|--------------------|---------------------------------------------------|-------|
| `sym x, y`         | `x, y = __er2_symbols__("x y")`                   | only at statement start (soft keyword, like `match`) |
| `x^2`              | `x**2`                                            | see D1 |
| `a ^^ b`           | `a ^ b`                                           | explicit XOR (Sage convention) |
| `1/3`              | `Integer(1)/Integer(3)` → `Rational(1, 3)`        | see D2 |
| `_x`               | unchanged; `_x` lives in the prelude              | see D3 |

Requirements:
- Built on the `tokenize` module; never touch the contents of strings or comments.
- Must preserve line numbers (errors must point at the line in the `.er2` file).
- Idempotent on plain Python that uses neither `^` nor `sym`.
- `er2 --show-python file.er2` must print the generated Python (for debugging).

### 3.2 Entry points

- **CLI**: `er2 file.er2` and the `er2` REPL (built on `code.InteractiveConsole` plus the preparser).
- **Import hook**: `import module` finds `module.er2` (meta path finder + loader).
- **Jupyter** (later; adds the `ipython` dependency): an IPython extension that registers the preparser in `input_transformers_post`
  (`%load_ext er2`).

All three share `er2.preparser` and `er2.prelude`; none of them contains its own translation logic.

### 3.3 Runtime and prelude (`er2/runtime/`, `er2/prelude.py`)

`prelude` defines the initial namespace: types, public functions, and the symbols `_x, _y, _z, _n, _k, _p`.

Canonical integer type: **exactly one** on the ER2 side (see D6; must satisfy the compatibility
contract in §1.1). Requirements: `__index__` (so that `range`, indexing, and slicing keep working),
lossless conversion to/from `cypari2.gen` and to/from `int`.

### 3.4 Dispatch (`er2/dispatch.py`)

Public functions are generic and choose a backend by type:

```text
factor(n: integer)         → PARI  factor / factorint
factor(p: polynomial/Expr) → SymPy factor
isprime(n)                 → PARI  isprime (proof) / ispseudoprime (option)
```

- The dispatch table lives in a single place, not scattered across functions.
- All type conversion happens at the backend boundary (`to_pari`, `from_pari`,
  `to_sympy`, `from_sympy`). Users never see a bare `cypari2.gen` or SymPy object unless
  they ask for one.
- `factor(n)` on an integer returns an ER2 `Factorization` object (prints `2^3 * 3^2`), not a PARI matrix.

### 3.5 ER2 → PARI name table

The names in the draft do not match PARI; an explicit mapping is required
(verified against the PARI 2.17.2 bundled with cypari2):

| ER2            | PARI              | Note |
|----------------|-------------------|------|
| `phi(n)`       | `eulerphi(n)`     | `phi` is obsolete in GP |
| `mu(n)`        | `moebius(n)`      | |
| `sigma(n, k=1)`| `sigma(n, k)`     | |
| `omega(n)`     | `omega(n)`        | |
| `Omega(n)`     | `bigomega(n)`     | |
| `valuation`    | `valuation`       | |
| `znorder`, `znprimroot`, `nextprime`, `divisors`, `gcd`, `lcm` | same | |
| `psi(n)`       | **conflict**      | in PARI `psi` is the digamma function; the draft lists it as arithmetic (Dedekind ψ?). See D5 |

### 3.6 Printing (`er2/printing.py`)

`print(f)`, `str`, `repr`, and Jupyter output use ER2 notation: `x^2 + 2*x + 1`, `(x + 1)^2`.
Implement as a subclass of `sympy.printing.str.StrPrinter` (`_print_Pow`), plus `_repr_latex_`
for Jupyter.

### 3.7 Backends (`er2/backends/`)

- `sympy_backend.py` — CAS: `expand, factor, simplify, collect, cancel, diff, integrate, limit, solve, series`.
- `pari_backend.py` — number theory. A single `cypari2.Pari()` instance; configurable stack size
  (`er2.config.pari_stack`).
- Neither backend imports the other. Only `dispatch` knows about both.

## 4. Proposed repository layout

```text
er2/
  __init__.py
  __main__.py          # CLI: er2 file.er2 | er2 (REPL) | er2 --show-python
  preparser.py
  prelude.py
  dispatch.py
  printing.py
  importer.py          # .er2 import hook
  ipython_ext.py       # %load_ext er2
  runtime/             # types: Integer, Rational, Symbol, Factorization, …
  backends/
    sympy_backend.py
    pari_backend.py
tests/
  preparser/           # .er2 → expected .py pairs
  compat/              # Python compatibility contract (§1.1)
  runtime/
  backends/
  examples/            # complete .er2 programs with expected (golden) output
examples/
  mvp.er2
draft/                 # idea documents (not code)
pyproject.toml
```

## 5. MVP (target of the first iteration)

Must run with `er2 examples/mvp.er2`:

```er2
sym x
f = x^2 + 2*x + 1
print(f)            # x^2 + 2*x + 1
print(expand(f))    # x^2 + 2*x + 1
print(factor(f))    # (x + 1)^2

print(factor(2^127 - 1))
print(phi(123456789))
print(sigma(123456789))
print(isprime(2^521 - 1))

for k in range(1, 20):
    if isprime(k):
        print(k)
```

This exercises all four pieces: preparser, printing, dispatch, and both backends.

## 6. Open design decisions

Each must be resolved (and recorded here) before or during 0.1.

- **D1 — `^` as power. ✅ Resolved (2026-09-18, Sage model, §1.1).** In `.er2` sources `^` means
  power and `^^` means XOR; `.py` modules are never affected.
  Precedence: translating to `**` inherits Python's (`-x^2` = `-(x^2)`, `2^3^2` = `2^(3^2)`),
  which is the mathematical one. Document it.
- **D2 — Exact by default. ✅ Resolved for integers (2026-09-18, Sage model, §1.1).** Every integer
  literal in `.er2` sources becomes an ER2 `Integer`, so `1/3` is rational. Still open: decimal
  literals (`0.1`) — keep Python `float` or use a controlled-precision `Real`. Watch performance in
  numeric loops.
- **D3 — Predefined `_x`.** The `_` prefix means "private" in Python, and `_` is the last result
  in the REPL. Low but real risk. If the user assigns `_n = 5`, the symbol is shadowed (normal
  Python behavior, acceptable).
- **D4 — `sym` as a soft keyword.** Only recognized as `sym <name>[, <name>…]` at the start of a
  logical line. `sym = 3` or `sym(x)` remain plain Python.
- **D5 — `psi`.** Decide between Dedekind ψ (arithmetic) and digamma. Proposal: `psi` = Dedekind
  (consistent with the list of arithmetic functions) and an explicit `digamma`.
- **D6 — Canonical integer type.** `sympy.Integer` vs `gmpy2.mpz` vs a custom class. Affects the
  cost of converting to PARI and to SymPy, and ecosystem compatibility (§1.1): with the Sage model
  every literal is an `Integer`, so libraries that check `isinstance(n, int)` would reject it.
  Proposal to evaluate: `class Integer(int)` (a real `int` subclass whose `/` returns `Rational`),
  converted to SymPy/PARI only at the backend boundary. Verify behavior with NumPy before deciding.
- **D7 — Expensive factorizations.** `factor(10^1000 - 1)` (the draft's example, §7) may not
  finish in reasonable time. Define a policy: timeout, `factor(n, partial=True)`, or leave it to
  the user.

## 7. Notes on the draft roadmap

- 0.3 (number theory) comes before 0.4 (PARI integration), but the 0.3 functions are built
  *on top of* PARI. Proposal: merge basic cypari2 integration into 0.3, and keep automatic backend
  selection, advanced PARI types, and benchmarks for 0.4.
- The MVP (draft §11) spans 0.1–0.3. Either widen 0.1, or declare the MVP a 0.3 milestone.

## 8. Dependencies

- Python ≥ 3.12 (current environment: 3.14).
- `sympy` (1.14 installed), optional `gmpy2`.
- `cypari2` — **the only source of PARI**. Its wheel bundles libpari (2.17.2), so no system
  PARI/GP or `gp` binary is required, by the code or by the tests.
- `ipython` — only when the Jupyter extension is implemented.
- Managed with `uv`.

Policy: **minimal dependencies**. Runtime = `sympy` + `cypari2`; dev = `pytest`. Anything else
needs a concrete reason.

## 9. Evolution (2.0)

Only once the syntax is stable: fork `python/cpython` to move the preparser transformations into
the real PEG grammar (`sym`, `^` tokens), with a dedicated AST and mathematical runtime.
Until then, **every** syntactic extension must be expressible as a token transformation over valid
Python; if a proposal is not, that is a sign it is drifting from the "mathematical Python" principle.

## 10. OEIS integration (future)

An `er2.oeis` module (`search`, `identify`) and `sequence(f, n)`. Out of scope until ≥ 0.6;
it will reuse the author's previous OEIS work.
