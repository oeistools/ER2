# ER2 — Project plan

This plan orders the work into milestones. Each milestone has concrete tasks and acceptance
criteria. The design lives in [ARCHITECTURE.md](ARCHITECTURE.md); the decisions it references
(D1–D15) are in ARCHITECTURE.md §6.

There are no calendar dates. A milestone is done when its acceptance criteria pass, and not
before.

## Rules that apply to every milestone

These come from the hard requirements in ARCHITECTURE.md §1.1, §1.2 and §6.1.

- **Python compatibility.** `tests/compat/` stays green. The semantic differences are only those
  in the §1.1 table.
- **Notebooks.** Every user-facing feature works in `er2 file.er2`, in Jupyter (the `er2` kernel
  and `%load_ext er2`), and in Quarto.
- **PEP 8.** `uv run ruff format` and `uv run ruff check` are clean.
- **Minimal dependencies.** A new dependency needs a written reason in ARCHITECTURE.md §8.
- **Tests with the code.** No feature is merged without tests. Expected mathematical values come
  from cypari2's PARI or from SymPy, and are hard-coded in the tests.
- **English only** in code, docs and commits.

## Status overview

| Milestone | Focus                                         | Status      |
| --------- | --------------------------------------------- | ----------- |
| M0        | Foundations                                   | ✅ done (CI result not yet checked) |
| M1 (0.1)  | Preparser, number types, CLI, Jupyter, Quarto | ✅ done     |
| M2 (0.2)  | CAS on SymPy                                  | ✅ done     |
| M3 (0.3)  | Number theory on PARI →**MVP**         | ✅ done     |
| M4 (0.4)  | Backend selection, PARI types, benchmarks     | ✅ done     |
| M5 (0.5)  | Algebra                                       | ✅ done     |
| 0.5.1     | Scientific articles (§1.3)                     | ✅ done     |
| 0.5.2     | Learnability and speed (§1.4, §1.5)            | ✅ done     |
| M6 (0.6)  | Series                                        | ✅ done     |
| 0.6.1     | ER2 cells and highlighting in Quarto (D9)     | ✅ done     |
| M7 (0.7)  | Language specification                        | not started |
| M8 (1.0)  | Stable language and release                   | not started |
| — (2.0)  | Deep CPython integration                      | long term   |

---

## M0 — Foundations

**Done:**

- [X] Idea draft translated to English (`draft/ER2_idea_summary.md`, kept locally, not in the repository)
- [X] ARCHITECTURE.md, CLAUDE.md, README.md, MIT LICENSE, .gitignore, CITATION.cff
- [X] Local git repository
- [X] `uv` environment: sympy, cypari2 (bundled PARI 2.17.2), pytest, ruff
- [X] Python compatibility model chosen: SageMath model (D1 resolved, D2 resolved for integers)
- [X] Prototype showing that an IPython input transformer works in Jupyter and Quarto (§1.2)
- [X] PARI → ER2 function table: [er2/data/pari_functions.csv](er2/data/pari_functions.csv),
  with its generator and [docs/PARI_FUNCTIONS.md](docs/PARI_FUNCTIONS.md)

**Remaining:**

- [X] GitHub repository: [oeistools/ER2](https://github.com/oeistools/ER2)
- [X] CI with GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)): ruff,
  pytest on Python 3.12–3.14, and a check that the PARI table is in sync. Quarto tests will be
  skipped when Quarto is not installed.
- [X] First tests: integrity of the PARI → ER2 table ([tests/test_pari_functions.py](tests/test_pari_functions.py))
- [X] README badges
- [X] Decisions for M1 settled: D2b, D3, D4, D6 (after the spike), D9

**Acceptance:** CI is green (⚠️ not checked yet: the repository is private and `gh` is not
logged in, so look at the Actions tab), and D3, D4, D6, D9 and
D2b are recorded in ARCHITECTURE.md §6.

---

## M1 — 0.1: Preparser, number types, entry points

Goal: ER2 syntax runs everywhere, even before the mathematics is complete.

**Tasks:**

1. ✅ **D6 spike** (done in M0; result: `Integer(int)`). Prototype `class Integer(int)` against the §1.1 contract: `range`, indexing,
   `hash`, `json`, `math`, and NumPy (`np.zeros(n)`, `np.array([n])` dtype). NumPy is used only in
   the spike environment. Then decide D6.
2. `er2/preparser.py`, built on `tokenize`:
   - `sym x, y` → symbol assignment (soft keyword, D4)
   - `^` → `**`, `^^` → `^`, `^=` → `**=`, `^^=` → `^=`
   - integer literals → `Integer(...)`
   - strings, comments and f-strings left untouched; line numbers preserved
   - XOR heuristic warning (§1.1, point 7)
3. `er2/runtime/`: `Integer` and `Rational` (exact `/`), meeting the §1.1 contract.
4. `er2/prelude.py`: the initial namespace, including `_x, _y, _z, _n, _k, _p` (D3).
5. `er2/printing.py`: `x^2` notation and `__repr__`; `latex()`, `Tex` and `show()`
   (ARCHITECTURE §3.6), with `_repr_latex_` on every ER2 type.
6. CLI (`er2/__main__.py`): `er2 file.er2`, `er2 --show-python file.er2`, and the `er2` REPL.
7. `er2/importer.py`: `.er2` imports through a `FileFinder` path hook, so `.py` still wins and
   `__init__.er2` packages work.
8. Notebooks: `er2/session.py` (`%load_ext er2`), and `er2/kernel.py` with
   `er2 kernel install`. The kernel also preparses `user_expressions`, which is how Quarto evaluates inline code. Add the optional extra `er2[jupyter] = ipykernel`.
9. Tests:
   - `tests/preparser/`: input/output pairs, including `^` and `sym` inside strings and comments
   - `tests/compat/`: plain Python snippets behave identically; stdlib imports work from `.er2`
   - notebook tests: execute a notebook through both routes (`nbclient` in the dev group, justified
     in §8); render a `.qmd` when Quarto is available

**Status: ✅ done (2026-09-18).** There are 115 tests. They cover the preparser, the numbers, printing
and LaTeX, the CLI, the REPL, imports, the compat suite, both notebook routes, and a real Quarto
render (with `gfm` output; the HTML rendering was checked in the prototype).

Found and fixed while building M1:
- Quarto runs `%reset` before rendering, which wiped the prelude. The prelude is now restored
  before every cell.
- A meta-path finder cannot see `.er2` packages. The importer now uses a path hook.
- Tracebacks showed ER2's internal frames and the preparsed code. They now show the user's ER2
  source.

Known limitations, carried forward:
- IPython's column highlighting in notebook tracebacks may be misaligned (M4).
- `f"{2^3=}"` echoes the preparsed text `2**__er2_int__(3)=`.
- The integer literal escape hatch (`5r`, §1.1 point 6) is not implemented; add it when needed.
- Literals are wrapped at every evaluation; hoisting constants is an M4 optimization.

**Acceptance:**

- `print(2^10)`, `print(1/3)`, `print(5 ^^ 3)` and `sym x; print(x^2 + 1)` give `1024`, `1/3`,
  `6` and `x^2 + 1` in the CLI, the REPL, Jupyter (both routes) and Quarto.
- `latex(1/3)` gives `\frac{1}{3}`, and `` `{python} latex(x^2)` `` renders as inline math in
  Quarto HTML with the `er2` kernel.
- An error on line N of a `.er2` file or cell is reported at line N.
- `tests/compat/` passes.

---

## M2 — 0.2: CAS on SymPy

**Tasks:**

1. `er2/backends/sympy_backend.py`: `expand`, `factor` (on `Expr`), `simplify`, `collect`,
   `cancel`, `diff`, `integrate`, `limit`, `solve`, `series`.
2. `er2/dispatch.py`: a single dispatch table, with only the SymPy backend at this point.
3. Conversion boundary: `to_sympy` and `from_sympy`. ER2 `Integer` and `Rational` interoperate with
   SymPy expressions.
4. Polynomials: `factor(x^4 - 1)`, and multivariate polynomials.
5. `latex()` for every symbolic type, with golden LaTeX tests. A test walks the runtime's
   public types and fails if any of them falls back to `\texttt`. Check rendering in Jupyter and
   in Quarto HTML and PDF.

**Status: ✅ done (2026-09-19).** There are 177 tests. New ones cover the conversion boundary, every CAS
function (values checked against SymPy 1.14), the dispatch table, golden LaTeX for the symbolic
types, the first half of the MVP in the CLI and in both notebook routes, and Quarto renders to
HTML and PDF (the PDF test is skipped without a TeX installation).

Done while building M2:
- The public functions return exact numbers as ER2 `Integer`/`Rational`
  (`integrate(f, (x, 0, 1))` is the ER2 `7/3`). Symbolic results stay SymPy objects (D11).
- The prelude also exposes SymPy's `pi, E, I, oo, sqrt, exp, log, sin, cos, tan, Eq`, because
  `integrate`, `limit` and `series` are hardly usable without them (ARCHITECTURE §3.3).
- `Integer` and `Rational` now define `_repr_latex_` (M1 gap), so a cell ending in `1/3`
  renders as math.
- `Poly` prints with `^` (SymPy's `_print_Poly` hard-codes `**`).
- `factor` of a number raises `TypeError` until the PARI backend exists (M3).

**Acceptance:** the first half of the MVP (ARCHITECTURE.md §5) prints the expected output in all
environments: `x^2 + 2*x + 1`, `x^2 + 2*x + 1`, `(x + 1)^2`.

---

## M3 — 0.3: Number theory on PARI → MVP

**Tasks:**

1. Settle **D5** (`psi`), **D7** (policy for expensive factorizations), **D8** (`bigomega`) and
   **D10** (prelude vs `pari.` namespace).
2. `er2/backends/pari_backend.py`: a single `cypari2.Pari()` instance, a configurable stack, and
   `to_pari` / `from_pari`.
3. Load `er2/data/pari_functions.csv`: build the prelude from the `prelude` rows and the `pari`
   namespace from the `namespace` rows. Add a test that every `prelude` and `namespace` row
   resolves to a callable.
4. Dispatch `factor` by type: integers go to PARI and expressions go to SymPy. Add a
   `Factorization` type that prints `2^3 * 3^2` (LaTeX `2^{3} \cdot 3^{2}`).
5. Exact `factorial`, since PARI's version returns a real.
6. Add `examples/mvp.er2`, `examples/mvp.ipynb` and `examples/mvp.qmd`, plus golden tests.

**Status: ✅ done (2026-09-19).** There are 268 tests. They cover the PARI conversion boundary, factorizations
(full, negative, rational, partial), the predicates, `Mod` (checked against PARI), `Factorization`,
every `prelude`/`namespace` row as a callable, golden LaTeX for every public function, the golden
programs `examples/mvp.er2` and `tests/examples/number_theory.er2`, `examples/mvp.ipynb` through
both routes, and `examples/mvp.qmd` in Quarto.

Done while building M3:
- D5, D7, D8 and D10 are resolved (ARCHITECTURE §6).
- **`Mod` was moved up from M4.** Four curated prelude functions (`znprimroot`, `znorder`,
  `znlog`, `chinese`) take or return residues. `Mod` is a pure-Python type with PARI's semantics
  (mixed moduli reduce to the gcd).
- `factorial` is exact through SymPy, so `factorial(x)` stays symbolic. `pari.factorial` is still
  PARI's real-valued function.
- **PARI setup.** The maximum stack was raised from ~8 MB to 1 GiB (reserved, not allocated), and
  real precision was set to GP's 38 digits (cypari2 uses 15). `pari.set_stack` and
  `pari.set_precision` change them.
- `dispatch` entries are now predicates over all the arguments, so `gcd(4, x)` goes to SymPy.
- Ruff excludes `examples/*.ipynb`, because it cannot parse ER2 syntax (§6.1).

Known limitations, carried forward:
- `from_pari` raises `TypeError` for `t_POLMOD`, `t_SER`, `t_QFB`, `t_PADIC` and other types
  (M4). `pari.raw` gives raw PARI objects.
- `to_pari` does not convert SymPy polynomials yet (M4, `Pol`).
- The 30 `wrapper` rows (`sum`, `intnum`, `prodeuler`, …) are not exposed yet.

**Acceptance: MVP.** The full program in ARCHITECTURE.md §5 gives the expected output in the CLI,
Jupyter (both routes) and Quarto. Values are checked against cypari2:
`phi(123456789) = 82260072`, `sigma(123456789) = 178422816`, `isprime(2^521 - 1) = True`.

---

## M4 — 0.4: Backend selection, PARI types, benchmarks

**Tasks:**

1. Automatic backend selection beyond `factor` of integers: univariate polynomials over Q go to
   PARI when that is faster.
2. PARI types exposed with ER2 semantics: `Pol` (including SymPy → PARI), `Ser`, `Qfb`, `POLMOD`,
   and vectors and matrices. (`Mod` came in M3.)
3. The `wrapper` functions that take GP closures (`sum`, `intnum`, `prodeuler`, `direuler`, …),
   accepting Python callables.
4. Benchmarks comparing ER2, raw cypari2 and SymPy, with the ER2 overhead reported.
5. Performance of `Integer` literals in numeric loops (D2 risk).
6. Notebook tracebacks (carried from M1).

Decisions taken with the user (2026-09-19): PARI types map to native ER2/SymPy objects, not a
generic wrapper; `Integer` stays pure Python for now; every univariate polynomial over Q is
factored by PARI.

**Status: ✅ done (2026-09-19).** There are 309 tests.

Done:
- **`factor` backend choice.** A univariate polynomial over Q with no options goes to PARI and
  comes back in SymPy's exact form. It gives the same expression as `sympy.factor` (checked on
  248 random polynomials) and is ×1.2–14 faster from degree 9 upward.
- **PARI ↔ SymPy conversions** in both directions: polynomials, rational functions, series
  (`t_SER` ↔ `p + O(x^n)`), exact reals (SymPy `Float` with its precision), complex numbers,
  matrices, `oo`. GP-reserved names such as `sigma` get their own PARI variable.
- **PARI types.** `Mod` takes polynomial moduli (`Mod(x, x^2 + 1)`, PARI's `t_POLMOD`), and there
  is a new `Qfb(a, b, c)` with composition, powers and `reduce()`, both computed by PARI.
- **26 functions take Python callables** (`er2/backends/pari_closures.py`), from `pari.sum`
  through `pari.forqfvec`. The other 4 former `wrapper` rows became `python`: `O` (use SymPy's
  `O` or `series()`), `Str`, `eval`, `intfuncinit`.
- **Benchmarks.** `benchmarks/run.py` writes [docs/BENCHMARKS.md](docs/BENCHMARKS.md), and a test
  runs it with `--quick`. ER2 adds about 2 µs per call over raw cypari2, and it is 16–50× faster
  than SymPy on number theory once SymPy's result cache is taken out of the comparison.
- **`Integer`.** The specialized operators and the literal cache make it 1.4–1.6× faster. A
  tight loop is about ×13 slower than `int` (it was ×19); the rest is the pure-Python floor
  (D6, ARCHITECTURE §6).
- **Notebook tracebacks** end at the user's line: ER2's internal frames are hidden, as in the CLI.
  The column-highlighting issue from M1 does not show up: current IPython highlights no columns,
  even for plain Python cells.

Found and fixed:
- **`match`/`case`.** The preparser wrapped the literals of `case` patterns, turning `case 0:`
  into a class pattern that never matched a plain `int`. Pattern literals are now left alone.
- **PARI objects kept between calls.** A PARI object created inside a callback lives on PARI's
  temporary stack, so no PARI object is cached between calls any more (variables, GP lambdas).
- **Quarto and the `.venv`.** Quarto started from an editor may only see the `.venv` kernels, so
  the ER2 kernel can also be installed there: `er2 kernel install --sys-prefix`.

Known limitations, carried forward:
- `t_PADIC`, `t_FFELT` and the structures of number fields and elliptic curves have no ER2 type
  yet (M5).
- `f"{2^3=}"` and the `5r` suffix: fixed in 0.4.1.
- Automatic backend choice covers `factor` only; polynomial `gcd` and resultants could follow.

## 0.4.1 — Quick wins

**Status: ✅ done (2026-09-19).** There are 325 tests.

- **Version.** 0.4.1, with `pyproject.toml` as the only source: `er2.__version__` and
  `er2 --version` read the package metadata, and a test checks that CITATION.cff matches.
- **Lazy SymPy** (user decision): a number theory program starts in 0.16 s instead of 0.40 s
  (ARCHITECTURE §3.3).
- **`5r` raw literals** (user decision; a new row in the §1.1 table): `5r` is a plain Python `int`.
- **`f"{2^3=}"`** now prints `2^3=8`; before, it echoed the preparsed Python text. Checked against
  Python's own output on 13 cases.
- **`factorial(n)`** of an integer uses PARI's exact `n!`, so it no longer loads SymPy.
- **CI** has a Quarto job, with Quarto and TinyTeX, that runs the notebook, HTML and PDF tests.
  `ER2_REQUIRE_QUARTO` makes them fail there instead of being skipped.
- **Found and fixed:** `er2 file.er2` did not put the file's directory on `sys.path`, as
  `python file.py` does, so a program could not import an `.er2` module next to it unless it was
  run from that directory.
- **A `Makefile`** for the common tasks, and VS Code notes for Quarto previews.

Still open: the M0 check that CI is green. `gh` is not logged in on this machine, so look at the
Actions tab after the next push.

## 0.4.2 — OEIS (brought forward from M6)

**Status: ✅ done (2026-09-19).** Decisions taken with the user: reuse
[oeis-tools](https://github.com/oeistools/oeis-tools) through the optional extra `er2[oeis]`, and
put `oeis` in the prelude.

- `oeis.sequence`, `search`, `identify` (by terms or by a function), `check` against the b-file,
  and `write_bfile` (ARCHITECTURE §10).
- **Tests.** 11 offline tests on recorded OEIS responses, and one live test
  (`ER2_NETWORK_TESTS=1`), which passes against oeis.org.
- **ER2 types format their own LaTeX** (`Mod`, `Qfb`, `Factorization`, `OEISSequence`), without
  SymPy's printer, so their LaTeX does not load SymPy.
- **Requires oeis-tools ≥ 0.2.1**, the first release with `Sequence.get_bibtex`, which
  `OEISSequence.bibtex()` uses.

## M5 — 0.5: Algebra

Matrices, finite fields, polynomials over them, resultants, Gröbner bases and algebraic numbers.
The backend is chosen per feature in `er2/dispatch.py`: PARI for exact linear algebra over Z and
Q, finite fields and number fields; SymPy for symbolic entries and Gröbner bases (PARI has none).

Starting point: every PARI function M5 needs (`matdet`, `matker`, `mathnf`, `matsnf`, `charpoly`,
`ffgen`, `ffinit`, `fforder`, `factormod`, `polresultant`, `poldisc`, `nfinit`, `bnfinit`,
`idealfactor`, …) is already reachable as `pari.<name>`, and `to_pari`/`from_pari` convert
matrices. What is missing is ER2 types, backend choice, and conversions: `from_pari` does not
handle `t_FFELT`, and it turns `nf`/`bnf` structures into plain lists.

**Tasks:**

1. ✅ Settle **D12** (matrix type), **D13** (finite-field syntax), **D14** (number-field API)
   and **D15** (scope of 0.5), ARCHITECTURE §6. Done 2026-09-19: SymPy `Matrix` with PARI
   dispatch; `GF(q)` with generator `a` and `ffinit`; a `NumberField` class with a cached `bnf`;
   all of M5 in 0.5, with number fields allowed to slip to 0.5.1.
2. ✅ **Linear algebra.** `det`, `inverse`, `rank`, `kernel` (null space), `charpoly`, `minpoly`,
   `echelon_form`, `hermite_form`, `smith_form`, `solve` for linear systems. Matrices with integer
   or rational entries go to PARI; symbolic entries go to SymPy. Both give the same results.
   Done 2026-09-19 (ARCHITECTURE §3.4): `Matrix` is in the prelude; 87 tests, including PARI
   against SymPy on 40 random matrices and the normal forms against SymPy's on 40 more.
   `minpoly` also takes algebraic numbers (SymPy) and polynomial `Mod`s (PARI).
3. ✅ **Finite fields.** `GF(p)` and `GF(p^k)` (D13): elements with `+ - * / ^`, `==`,
   `order`, `minpoly`, `charpoly`, `trace`, `norm`, `sqrt`, `log`, and a primitive element.
   Computed by PARI (`t_FFELT`); `from_pari` returns the ER2 element type. `Mod` stays the type of
   `Z/nZ` residues; `GF(p)(a)` and `Mod(a, p)` interoperate.
   Done 2026-09-19: `GF` is in the prelude, with `FiniteField` (order, characteristic, degree,
   `modulus()`, `gen()`, `primitive_element()`, `elements()`) and `FiniteFieldElement`. 15 tests,
   including all of the arithmetic against PARI on every element of GF(7), GF(9) and GF(2^5).
4. ✅ **Polynomials over finite fields.** `factor(f, modulus=p)` and `factor(f, domain=GF(q))` (PARI
   `factormod`), `isirreducible`, `gcd`, and `ffinit` as a way to build extensions.
   Done 2026-09-19: `factor` and `gcd` with `modulus=p` go to PARI and give what SymPy gives
   (checked on 400 random polynomials); `isirreducible` is new, over Q and over `F_p`; `GF(p, k)`
   already builds extensions with `ffinit`. **Not done:** polynomials over `GF(p^k)`, `k > 1`,
   which need a polynomial type whose coefficients are field elements. `factor(f, domain=GF(9))`
   raises `NotImplementedError` and points to `pari.raw.factormod`. Proposed for 0.5.1 (D15).
5. ✅ **Resultants and discriminants.** `resultant(f, g, x)`, `discriminant(f, x)`: PARI for
   polynomials over Q, SymPy for symbolic coefficients.
   Done 2026-09-20: both are in the prelude, the variable may be left out when the arguments
   have a single variable between them, and 20 tests compare the two backends on 200 random
   polynomials over Q and 40 with symbolic coefficients. **D16** was needed: `sympy.resultant`
   drops the sign of reordering its arguments, so ER2 follows the standard definition (PARI's)
   and corrects the SymPy route — the first place where "the PARI route returns what SymPy
   returns" could not be kept as written (ARCHITECTURE §3.4, §6).
6. ✅ **Gröbner bases.** `groebner(F, *gens, order="lex")` through SymPy, returning SymPy's
   `GroebnerBasis` printed with ER2's printer; `reduce` of a polynomial modulo a basis.
   Done 2026-09-20: both are in the prelude, 10 tests. **D17**: `reduce(f, G)` returns the
   remainder (the normal form), not SymPy's `([quotients], remainder)`. Found while testing:
   `f in G` is Python's list membership, not membership of the ideal — SymPy's `GroebnerBasis`
   has `__iter__` and no `__contains__` — so the docstrings point at `reduce(f, G) == 0`.
7. ✅ **Number fields** (D14). Build from an irreducible polynomial over Q: degree,
   discriminant, integral basis, class number and class group, fundamental units, ideal
   factorization of a rational prime, elements as `Mod(poly, x^2 + 5)` (`t_POLMOD`, from M4).
   `bnfinit` is computed once per field and cached; heavy calls follow the D7 policy (Ctrl-C).
   Done 2026-09-20: `NumberField` and `PrimeIdeal`, 18 tests. D14 and the M4 rule "no PARI object
   outlives the call that made it" collided over the cached `bnf`; resolved by extracting
   everything to plain Python data in the one `bnfinit` call, which a test enforces by clearing
   PARI's stack and checking the field still works (ARCHITECTURE §3.4). Found while testing:
   `bnfinit` is randomised, so a fundamental unit comes back as one of several equivalent
   representatives. Non-monic polynomials are rejected: PARI would silently present the field by
   a different polynomial.
8. ✅ **Printing and LaTeX** (hard requirement, ARCHITECTURE §3.6): every new type has `latex()`,
   `_repr_latex_` and a golden LaTeX test, with no SymPy import for PARI-only types.
   Done 2026-09-20: satisfied as each type landed; `tests/test_latex_coverage.py` fails if a
   runtime class or prelude function is missing a sample, and `tests/test_lazy_sympy.py` proves
   the PARI-only types (`Mod`, `Qfb`, `Factorization`, `GF`) format LaTeX without SymPy.
9. ✅ **Tables and docs.** Update `er2/data/pari_functions.csv` for the rows that gain an ER2 name
   (`matdet` → `det`, `polresultant` → `resultant`, …) and regenerate `docs/PARI_FUNCTIONS.md`.
   Add an algebra section to the README and `examples/demo.qmd`.
   Done 2026-09-20: 16 rows now name their ER2 equivalent. **Deviation:** the equivalent went in
   the `note` column, not `er2_name`. For a `namespace` row `er2_name` is what `pari.<name>` is
   called, so renaming would have moved `pari.matdet` to `pari.det` — away from the name a PARI
   user knows — and this file only renames a namespace row for PEP 8 (`factormodDDF`). The README
   and `examples/demo.qmd` have algebra sections; the demo was rendered with Quarto and every
   output checked.
10. ✅ **Benchmarks.** Add determinant, kernel, HNF/SNF and `factor` over GF(p) to
    `benchmarks/run.py` (ER2 vs raw cypari2 vs SymPy) and regenerate `docs/BENCHMARKS.md`.
    Done 2026-09-20. The numbers corrected a documented claim: `factor(f, modulus=p)` was said to
    be ×40 faster than SymPy at degree 49, which is the *raw PARI* ratio; end to end ER2 is
    ×2–10, because converting to and from SymPy's form costs more than the factoring.
    `hermite_form` is ×3.3 **slower** than SymPy at 10×10 — a size threshold for its dispatch is
    open work (ARCHITECTURE §3.4).

**Tests.** Expected values from cypari2 and SymPy, hard-coded. The PARI and SymPy routes of task 2
agree on random integer matrices (like the 248-polynomial check for `factor` in M4). Finite-field
arithmetic is checked against PARI on all elements of small fields (GF(7), GF(9), GF(2^5)). No
class-group computation above degree 4 or discriminant 10^6 in the suite (D7).

**Acceptance: ✅ met (2026-09-20).** `tests/examples/algebra.er2` (golden output checked in the
CLI), `examples/algebra.qmd` (rendered by Quarto), and the same program through both Jupyter
routes — `test_algebra_notebook` and `test_algebra_quarto` in `tests/notebooks/`. The golden
output was checked to be reproducible across runs, which matters because `bnfinit` is randomised;
nothing in it depends on a fundamental unit's representative. It shows:

- `det`, `kernel` and `smith_form` of an integer matrix, and `det` of a symbolic matrix;
- arithmetic in GF(9) and `factor(x^8 - x, modulus=2)`;
- `resultant(x^2 + 1, x^3 - 2, x) = 5` and the discriminant of `x^3 + x + 1` (= -31);
- a Gröbner basis of `[x^2 + y^2 - 1, x - y]` in lex order;
- the class number of Q(√-5) (= 2) and the factorization of 2 and 3 in it.

`tests/compat/` stays green, and `import er2` still does not load SymPy for number-only programs
(`tests/test_lazy_sympy.py`).

## 0.5.1 — Scientific articles

Goal stated by the user on 2026-09-20 and recorded as ARCHITECTURE §1.3: **a paper should be
writable in ER2**, with its numbers, formulas and figures produced by the document that states
them. Nothing here is a new subsystem — Quarto, `latex()`, exact arithmetic and the OEIS BibTeX
already exist — but only a whole article exercises them together, and nothing does that today.

**Tasks:**

1. ✅ **Figures.** `tests/compat/test_scientific.py` now covers Matplotlib: ER2 `Integer` and
   `Rational` as coordinates, a `Tex` string as a label, and saving a figure. Matplotlib joined
   the `dev` group (user decision, 2026-09-20): the *kernel's* interpreter needs it, so
   `uv run --with matplotlib quarto render` does not help. It brings NumPy with it, so the
   scientific tests now run in the ordinary test job and the separate CI job was removed.
2. ✅ **`examples/article.qmd`**: *Mertens' third theorem, computed* — abstract, a numbered and
   cross-referenced equation, a computed table, a figure, citations and a bibliography
   (`examples/article.bib`). Six numbers in the prose come from the computation, including the
   exact rational product for `x = 50`. Renders to HTML and to PDF.
3. ✅ **A test that renders it**: `test_article_renders`, parametrised over HTML and PDF, in the
   Quarto CI job. It asserts the six computed values, exactly one figure image of real size, the
   cross-references and the bibliography — not merely that the render exited 0.
4. ✅ **Citing the tools.** The article cites ER2, PARI/GP, SymPy and Mertens' 1874 paper.

**Acceptance: ✅ met (2026-09-20).** Found while building it, and now guarded: writing the exact
rational product past `x = 10^4` is quadratic in the digits (3500 digits at `10^4`, and the render
hung at `10^6`), so the article keeps the exact value for the small case and accumulates in
floating point for the table — and says why. And `matplotlib.use("Agg")` in a Quarto cell makes
`plt.show()` draw **nothing** while the render still succeeds, which is why the test asserts the
image exists rather than trusting the exit code.

**Deliberately out of scope:** a journal template, `.docx` or `.tex` export, and any wrapper
around Matplotlib. Quarto already does templates and export, and a plotting API is a different
project.

## 0.5.2 — Learnability and speed

Three things the user asked for on 2026-09-20, all of them about ER2's stated goals rather than
its feature list: **ER2 must be easy to learn for a Python programmer**, **it must be faster than
SymPy**, **using PARI through it must cost little beyond a small dispatch charge**, and the
architecture document should show the components as a diagram.

The first and the last are writing. The middle two turned out not to be, because the
measurements did not support them.

**Tasks:**

1. ✅ **ARCHITECTURE §1.4, learnable in an afternoon.** The §1.1 table — five differences — plus
   the function names is the whole of what has to be learned, and the section names the four
   things that goal rules out. The measure is that the language's reference stays short.
2. ✅ **ARCHITECTURE §1.5, the speed goal**, stated as two separate comparisons (against SymPy,
   the user's alternative; against cypari2, the tax ER2 charges) because they are different
   promises and conflating them is how a misleading number gets published.
3. ✅ **A Mermaid diagram of the components** in §2, with the ASCII version kept below it and a
   structural test so it cannot silently break; there is no JavaScript toolchain here to render
   it, so the test checks what actually breaks: `subgraph`/`end` balance, edges to undeclared
   nodes, `class` without `classDef`. Each guard was checked against a deliberately broken copy.
4. ✅ **ARCHITECTURE §2.1, where the time goes.** Choosing a backend, converting, and computing
   measured apart. For a 10×10 `det`: 1.5 µs, 100 µs, 13 µs.
5. ✅ **Made the goal true for matrices.** Measuring first showed the promise was not met:
   choosing a backend for a 10×10 matrix cost 135 µs, ten times the PARI call it was deciding
   about, because the predicate scanned all n² entries. SymPy already stores the answer in the
   matrix's domain, so the question is now O(1), and both conversions read that representation
   directly instead of going through `sympy.Integer`. Matrix calls are 3–6× faster;
   `docs/BENCHMARKS.md` has a new "Dispatch overhead" section so the claim stays checkable.
6. ✅ **And for polynomials.** Writing §1.5 caught a claim that was simply false: `factor` at
   degree 4 was ×1.23 *slower* than SymPy, so "faster than SymPy" did not hold at the low end.
   The same bug class again — `to_pari` called `sympy.together` to split a rational function
   into numerator and denominator, which for a polynomial is three quarters of the conversion
   spent learning that the denominator is 1. A univariate polynomial over Q now goes straight to
   PARI's `Pol`, one call instead of one per term, and the predicate no longer walks the
   expression twice.

**Acceptance: ✅ met (2026-09-20).** Every linear algebra operation is now faster than SymPy at
both sizes measured, which was not true before: `hermite_form` at 10×10 was ×3.3 *slower* and is
now ×1.4 faster.

Two findings worth keeping:

- **The recorded fix was the wrong fix.** §3.4 proposed a size threshold in dispatch, to stop
  sending small matrices to PARI. That would have treated a symptom: PARI was never what was
  slow. Making the conversion cheap removed the need for the threshold entirely. Before adding a
  rule about *when* to use a backend, check whether the backend is what is slow.
- **A predicate that scans is a predicate that costs.** Dispatch runs before any work is done, so
  anything proportional to the data belongs in the backend, not in the choice of backend.

**Found while measuring, and fixed:** `hermite_form` of a matrix with no columns returned a 0×0,
losing the row count, where SymPy keeps the shape — PARI writes every empty matrix as `[;]`.

**Still open:** `PARI.matrix` is now most of the conversion cost (~80 µs of 100 µs at 10×10) and
is cypari2's, not ours. And the predicate and the converter each build a `sympy.Poly` of the same
expression, so that work is done twice; passing the `Poly` from one to the other would cross the
boundary dispatch exists to keep, so it needs a design decision rather than a patch.

## M6 — 0.6: Series

Power series, generating functions, Dirichlet series and Euler products. (The OEIS module came
early, in 0.4.2.)

**What is already there, and what this milestone is therefore about.** Every PARI capability M6
needs already works through `pari.<name>` — checked on 2026-09-20: `Ser`, `serreverse`,
`serconvol`, `serlaplace`, `dirmul`, `dirdiv`, `direuler`, `prodeuler`, `prodeulerrat`, `sumalt`,
and `t_SER` converts in both directions. `series(exp(x), x, 0, 5)` has worked since M2.
So M6 adds almost no capability. It is an **API design milestone**: turning a PARI namespace a
user must already know PARI to navigate into a curated one they do not (§1.4). Where that
distinction is not worth a name, M6 should add nothing and say so.

**Decisions taken before starting (user, 2026-09-20):** D18, D19, D20 below.

**Tasks:**

1. ✅ **Power series stay SymPy expressions (D18).** Three functions added, and each had to earn
   its name: `series_reverse`, `hadamard_product` and `series_laplace` (the EGF-to-OGF bridge).
   **`coefficient(s, n)` was dropped**: SymPy's `s.coeff(x, n)` already does it, and §1.4 rules
   out a second way to write what Python can already write. Applying that rule to our own plan
   is the point of having it.
2. ✅ **Series arithmetic goes to PARI where it pays — and it pays everywhere.** Measuring first
   found two traps of its own: SymPy leaves `s * t` *unevaluated*, so the first benchmark
   measured nothing, and SymPy caches, so the second measured a cache hit. With distinct inputs,
   `sympy.expand` of a product of series costs 11 ms at six terms and 612 ms at eighty, against
   3.4 ms and 46 ms through PARI. The hook is **`expand`**, which the user already types — no
   backend to choose (§1.4). Only `Mul` and `Pow` are intercepted, since SymPy evaluates `Add`.
   Also fixed a `sympy.expand` in the series conversion that was a no-op costing 250 µs, two
   thirds of that conversion; the first guard broke Laurent series and an existing test caught it.
3. ✅ **A `DirichletSeries` type (D19)** with `*` and `/` (PARI `dirmul`, `dirdiv`), `+` and `-`
   coefficientwise, indexing from 1, `latex()` and `_repr_latex_`. Operations truncate to the
   shorter operand. Coefficients are plain ER2 numbers, so no PARI object outlives the call (M4),
   and a test checks it.
4. ✅ **Euler products.** Formal: `DirichletSeries.euler(f, n)` over `direuler`. Numeric:
   `pari_backend.euler_product` over `prodeuler`. Ruff caught a real API bug here — the callback
   was documented as `(p, X)`, which would have made *users* write non-PEP 8 code, against §6.1.
5. ✅ **Generating functions, tied to `er2.oeis`.** `generating_function(seq, x, n)` takes
   anything iterable, and an `OEISSequence` iterates over its terms, so neither side needed code
   about the other. The test derives `x/(1 - x - x^2)` from `oeis.sequence("A000045")` by
   multiplying it out rather than asserting it.
6. ✅ **Named series as classmethods, not prelude names**: `DirichletSeries.zeta(n)` and
   `.moebius(n)`. Discoverable from the type without spending §1.4's budget on top-level names.
7. ✅ **Golden LaTeX samples** for `DirichletSeries`, `generating_function`, `series_reverse`,
   `series_laplace` and `hadamard_product`. Both coverage tests fired on schedule while adding
   them, which is what they are for.

**Acceptance: ✅ met (2026-09-20).** `examples/series.qmd` renders with the `er2` kernel and is
checked by `test_series_quarto`; `tests/examples/series.er2` is the golden program.

Two things worth keeping:

- **An acceptance test can pass vacuously.** The first version asserted that the quotient's
  series *appears* in the render — but the document prints `expand(s/t)` and
  `series(exp(x)*(1 - x))` one after the other, so the line appears even with the division
  removed. Mutating the document proved it passed when it should not. It now asserts the line
  appears **twice**, which is the actual claim: the two routes agree.
- **D21 came out of writing the tests**, not out of planning. Multiplication, powers and mixed
  precisions agree with `sympy.expand` exactly; division does not, because SymPy declines to do
  it. That needed the user's decision, not a silent choice.

**Deliberately out of scope (D20):** L-functions (PARI's `lfun` family), modular forms, and
p-adic series. `lfun` is large enough to deserve its own milestone, and nothing in M6 needs it.

## 0.6.1 — ER2 cells and highlighting in Quarto

The user asked for `` ```{er2} `` blocks instead of `` ```{python} `` (2026-09-20). The premise
turned out to be false, and chasing it produced something better, so both are recorded here.

**What was found.** `` ```{er2} `` **does not execute** on Quarto 1.9.38, whatever the kernelspec
declares — the block is copied into the output as literal text and the render still exits 0, so
the failure is silent. Converting `examples/series.qmd` to it fails outright
(`NameError: name 'latex' is not defined`), because the inline `{python}` expressions still run
while the cells never do. Quarto's own developer notes confirm why: a block's language is claimed
by an **engine**, and there is no language-to-kernelspec mapping. ARCHITECTURE §1.2 has the
measurements.

**Tasks:**

1. ✅ **Correct the record.** §1.2 claimed Quarto accepted `` ```{er2} `` cells. It does not, on
   the version the note says was tested. The claim is replaced by the retest, and D9 is
   reaffirmed with its reason.
2. ✅ **`examples/er2-cells.lua`** renames the displayed language of every executable Python
   block to `er2` and marks the cell div. No per-cell marker: in a document with `jupyter: er2`
   every executable Python block *is* ER2.
3. ✅ **`examples/er2.xml`**, a KDE syntax definition, so `er2` is really highlighted. It states
   only the §1.1 table and includes Python's rules with `IncludeRules context="##Python"`, so
   Python's half is Pandoc's own and cannot drift. Roughly 25 lines.
4. ✅ **`examples/_quarto.yml`** turns both on for every example in four lines, once, so no
   document's front matter carries them.
5. ✅ **A test that fails if any of the three stops working**
   (`test_cells_are_displayed_as_er2`), checked by mutation: removing the syntax definition, the
   filter, or `sym` from the keyword list each makes it fail.

**Acceptance: ✅ met (2026-09-20).** All five examples render with every cell shown as `er2`,
none left as `python`, `sym` highlighted as an ER2 keyword, and their computed output unchanged.

Three things worth keeping:

- **A Lua filter cannot make a block execute**, only relabel it: Quarto runs filters after the
  kernel, which a logging filter showed by 20 log lines. A filter that relabels an unexecuted
  block produces the worst outcome — a block that looks like a cell which printed nothing.
- **The first fix made the source worse.** Putting the machinery in each document's front matter
  traded five lines per file for a feature that belongs in one place; the user said so, and
  `_quarto.yml` fixed it. Optimising the output at the author's expense is a bad trade.
- **`er2.xml` is reusable.** It is the same artefact a VS Code or Kate extension needs, and it
  belongs beside `docs/LANGUAGE.md` in M7 rather than in `examples/` for ever.

**Deliberately not done:** a Quarto **engine extension**, which is the only way to make
`` ```{er2} `` execute. `quarto create extension engine` scaffolds one, but since Jupyter must do
the executing it would be a reimplementation of Quarto's Jupyter engine (the bundled
`julia-engine` is ~1,300 lines against an API at version 0.1.0), installed per project, and it
would lose the editor tooling D9 chose `python` for.

## M7 — 0.7: Language specification

The point of this milestone is the transition from *inventing* syntax to *specifying* it.
Everything ER2 does is currently described across `ARCHITECTURE.md`, the README and the tests;
`docs/LANGUAGE.md` turns that into one normative document, so that 1.0 has something to freeze.

**Tasks:**

1. `docs/LANGUAGE.md`, covering at least:
   ER2 syntax; the exact differences from Python; operator precedence and associativity; exact
   literals; `sym`; the `Integer`/`Rational` model; Python ↔ ER2 conversion; SymPy ↔ ER2;
   PARI ↔ ER2; the dispatch rules; representation and LaTeX; Jupyter and Quarto; compatibility
   with Python code; and what counts as stable syntax before 1.0.
2. The §1.1 table of `ARCHITECTURE.md` becomes **normative**: `docs/LANGUAGE.md` owns it, and
   §1.1 links to it rather than restating it.
3. ✅ **Scientific interoperability, tested.** The README promises that ER2 numbers pass into
   NumPy, SciPy, pandas and Matplotlib, and nothing in `tests/` imported any of them.
   Done 2026-09-20 for NumPy: `tests/compat/test_scientific.py`, skipped without NumPy and run by
   its own CI job. Writing it turned up an undocumented asymmetry — `Integer` gets a real dtype,
   `Rational` falls back to an object array — which ARCHITECTURE §1.1 point 5 now states.
   SciPy, pandas and Matplotlib are still uncovered.
4. Every difference in the specification has a test that would fail if it changed.

**Acceptance:** a reader can implement a compatible preparser from `docs/LANGUAGE.md` alone,
and every statement in it is backed by a test.

## M8 — 1.0: Stable language and release

- A documentation site. Quarto is a natural choice, since ER2 already runs in it.
- PyPI release: `pip install er2` and `pip install er2[jupyter]`.
- A stability policy for the public API and deprecations.
- The syntax and the public API are frozen: after 1.0 they change only through that policy.

## 2.0 — Deep CPython integration (long term)

Only once the syntax is stable: a fork of CPython with native `sym` and `^` in the PEG grammar.
Revisit this only if the preparser shows real limits.

---

## Decision schedule

| ID  | Topic                                  | Needed by | Status                                              |
| --- | -------------------------------------- | --------- | --------------------------------------------------- |
| D1  | `^` as power                         | —        | ✅ resolved (Sage model)                            |
| D2  | exact integer literals                 | —        | ✅ resolved (Sage model)                            |
| D2b | decimal literals | M1 | ✅ resolved: Python `float` |
| D3  | predefined `_x` symbols | M1 | ✅ resolved: keep, shadowable |
| D4  | `sym` as a soft keyword | M1 | ✅ resolved: start of statement only |
| D6  | canonical integer type | M1 | ✅ resolved: `Integer(int)` (spike) |
| D9  | kernelspec language | M1 | ✅ resolved: `python` |
| D11 | `x^2` in `print()` | M1 | ✅ resolved: only in ER2 sessions |
| D5  | `psi`: Dedekind or digamma           | M3        | ✅ resolved: `dedekind_psi` + `pari.digamma`, no `psi` |
| D7  | expensive factorizations               | M3        | ✅ resolved: full + Ctrl-C + `limit=`              |
| D8  | `Omega` → `bigomega`              | M3        | ✅ resolved: `bigomega`                            |
| D10 | exposure of PARI functions             | M3        | ✅ resolved: curated prelude plus `pari.`          |
| D12 | matrix type                            | M5        | ✅ resolved: SymPy `Matrix`, backend in `dispatch` |
| D13 | finite-field syntax                    | M5        | ✅ resolved: `GF(9)`, generator `a`, `ffinit`       |
| D14 | number-field API                       | M5        | ✅ resolved: `NumberField` class, cached `bnf`     |
| D15 | scope of 0.5                           | M5        | ✅ resolved: all of M5; number fields may slip to 0.5.1 |
| D16 | sign of `resultant`                  | M5        | ✅ resolved: the standard definition (PARI), not SymPy's |
| D17 | reduction modulo a basis             | M5        | ✅ resolved: `reduce(f, G)` returns the remainder |
| D18 | representation of a power series     | M6        | ✅ resolved: a SymPy expression with `O()`, no new type |
| D19 | representation of a Dirichlet series | M6        | ✅ resolved: a `DirichletSeries` type, not a bare list |
| D20 | scope of M6                          | M6        | ✅ resolved: series, generating functions, Dirichlet and Euler; no L-functions |
| D21 | `expand` of a quotient of series     | M6        | ✅ resolved: PARI divides; ER2's `expand` beats SymPy's here |

## Risks

| Risk                                                           | Impact                  | Mitigation                                                                              |
| -------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------- |
| `Integer` literals slow down numeric loops                   | Performance             | M4 benchmarks; an`int` subclass keeps the fast paths; raw literals as an escape hatch |
| Libraries reject ER2 numbers (`isinstance(n, int)`)          | Ecosystem compatibility | D6 spike before writing code; compat tests                                              |
| A cypari2 wheel is missing for a new Python version            | Installation            | Pin the supported Python versions in CI; cypari2 can build from source                  |
| The`functions_basic` struct layout changes in a PARI upgrade | Table generator breaks  | The script checks the layout and fails loudly; re-check after each cypari2 bump         |
| Pasted Python code that uses`^` as XOR                       | Silent wrong results    | Preparser warning; document the difference; keep such code in`.py` modules            |
| Changes in the ipykernel or Quarto APIs                        | Notebook support breaks | Notebook tests in CI                                                                    |
