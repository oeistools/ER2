# ER2 — Project plan

This plan orders the work into milestones. Each milestone has concrete tasks and acceptance
criteria. The design lives in [ARCHITECTURE.md](ARCHITECTURE.md); the decisions it references
(D1–D10) are in ARCHITECTURE.md §6.

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
| M0        | Foundations                                   | in progress |
| M1 (0.1)  | Preparser, number types, CLI, Jupyter, Quarto | not started |
| M2 (0.2)  | CAS on SymPy                                  | not started |
| M3 (0.3)  | Number theory on PARI →**MVP**         | not started |
| M4 (0.4)  | Backend selection, PARI types, benchmarks     | not started |
| M5 (0.5)  | Algebra                                       | not started |
| M6 (0.6)  | Series                                        | not started |
| M7 (1.0)  | Stable language and release                   | not started |
| — (2.0)  | Deep CPython integration                      | long term   |

---

## M0 — Foundations

**Done:**

- [X] Idea draft translated to English: [draft/ER2_idea_summary.md](draft/ER2_idea_summary.md)
- [X] ARCHITECTURE.md, CLAUDE.md, README.md, MIT LICENSE, .gitignore, CITATION.cff
- [X] Local git repository
- [X] `uv` environment: sympy, cypari2 (bundled PARI 2.17.2), pytest, ruff
- [X] Python compatibility model chosen: SageMath model (D1 resolved, D2 resolved for integers)
- [X] Prototype showing that an IPython input transformer works in Jupyter and Quarto (§1.2)
- [X] PARI → ER2 function table: [er2/data/pari_functions.csv](er2/data/pari_functions.csv),
  with its generator and [docs/PARI_FUNCTIONS.md](docs/PARI_FUNCTIONS.md)

**Remaining:**

- [ ] Create the GitHub repository and push it (waiting for `gh auth login` and a choice of public or private)
- [ ] CI with GitHub Actions: `uv sync`, `ruff format --check`, `ruff check`, `pytest`
  (Quarto render tests are skipped when Quarto is not installed)
- [ ] Settle the decisions M1 needs: **D3** (`_x` symbols), **D4** (`sym` soft keyword),
  **D6** (integer type), **D9** (kernelspec language), **D2b** (decimal literals)

**Acceptance:** the repo is on GitHub, CI is green on an empty test suite, and D3, D4, D6, D9 and
D2b are recorded in ARCHITECTURE.md §6.

---

## M1 — 0.1: Preparser, number types, entry points

Goal: ER2 syntax runs everywhere, even before the mathematics is complete.

**Tasks:**

1. **D6 spike.** Prototype `class Integer(int)` against the §1.1 contract: `range`, indexing,
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
7. `er2/importer.py`: an import hook for `.er2` modules, added to the finders and never
   replacing them.
8. Notebooks: `er2/ipython_ext.py` (`%load_ext er2`), and `er2/kernel.py` with
   `er2 kernel install`. The kernel also preparses `user_expressions`, which is how Quarto evaluates inline code. Add the optional extra `er2[jupyter] = ipykernel`.
9. Tests:
   - `tests/preparser/`: input/output pairs, including `^` and `sym` inside strings and comments
   - `tests/compat/`: plain Python snippets behave identically; stdlib imports work from `.er2`
   - notebook tests: execute a notebook through both routes (`nbclient` in the dev group, justified
     in §8); render a `.qmd` when Quarto is available

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

**Acceptance: MVP.** The full program in ARCHITECTURE.md §5 gives the expected output in the CLI,
Jupyter (both routes) and Quarto. Values are checked against cypari2:
`phi(123456789) = 82260072`, `sigma(123456789) = 178422816`, `isprime(2^521 - 1) = True`.

---

## M4 — 0.4: Backend selection, PARI types, benchmarks

- Automatic backend selection beyond `factor`, for example integer polynomials going to PARI when
  that is faster.
- PARI types exposed with ER2 semantics: `Mod`, `Pol`, `Ser`, `Qfb`, and vectors and matrices.
- Benchmarks comparing ER2, raw cypari2 and SymPy, with the ER2 overhead reported.
- Performance of `Integer` literals in numeric loops (D2 risk).

## M5 — 0.5: Algebra

Matrices, finite fields, resultants, Gröbner bases and algebraic numbers. Choose the backend per
feature: PARI for number fields and finite fields, SymPy for Gröbner bases.

## M6 — 0.6: Series

Power series, generating functions, Dirichlet series and Euler products. The OEIS module
(`er2.oeis`) starts here, reusing the author's previous OEIS work.

## M7 — 1.0: Stable language

- A formal specification of the preparser (the §1.1 table becomes normative).
- A documentation site. Quarto is a natural choice, since ER2 already runs in it.
- PyPI release: `pip install er2` and `pip install er2[jupyter]`.
- A stability policy for the public API and deprecations.

## 2.0 — Deep CPython integration (long term)

Only once the syntax is stable: a fork of CPython with native `sym` and `^` in the PEG grammar.
Revisit this only if the preparser shows real limits.

---

## Decision schedule

| ID  | Topic                                  | Needed by | Status                                              |
| --- | -------------------------------------- | --------- | --------------------------------------------------- |
| D1  | `^` as power                         | —        | ✅ resolved (Sage model)                            |
| D2  | exact integer literals                 | —        | ✅ resolved (Sage model)                            |
| D2b | decimal literals:`float` or `Real` | M1        | open                                                |
| D3  | predefined`_x` symbols               | M1        | open (proposal: keep, and allow shadowing)          |
| D4  | `sym` as a soft keyword              | M1        | open (proposal: only at the start of a statement)   |
| D6  | canonical integer type                 | M1        | open (proposal:`Integer(int)`, pending the spike) |
| D9  | kernelspec language                    | M1        | open (proposal:`python`)                          |
| D5  | `psi`: Dedekind or digamma           | M3        | open                                                |
| D7  | expensive factorizations               | M3        | open                                                |
| D8  | `Omega` → `bigomega`              | M3        | open (proposal:`bigomega`)                        |
| D10 | exposure of PARI functions             | M3        | open (proposal: curated prelude plus`pari.`)      |

## Risks

| Risk                                                           | Impact                  | Mitigation                                                                              |
| -------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------- |
| `Integer` literals slow down numeric loops                   | Performance             | M4 benchmarks; an`int` subclass keeps the fast paths; raw literals as an escape hatch |
| Libraries reject ER2 numbers (`isinstance(n, int)`)          | Ecosystem compatibility | D6 spike before writing code; compat tests                                              |
| A cypari2 wheel is missing for a new Python version            | Installation            | Pin the supported Python versions in CI; cypari2 can build from source                  |
| The`functions_basic` struct layout changes in a PARI upgrade | Table generator breaks  | The script checks the layout and fails loudly; re-check after each cypari2 bump         |
| Pasted Python code that uses`^` as XOR                       | Silent wrong results    | Preparser warning; document the difference; keep such code in`.py` modules            |
| Changes in the ipykernel or Quarto APIs                        | Notebook support breaks | Notebook tests in CI                                                                    |
