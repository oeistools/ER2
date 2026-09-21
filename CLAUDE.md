# CLAUDE.md

Guidance for Claude Code in this repository.

## Project

**ER2 — mathematical Python.** A superset of Python with symbolic syntax (`sym x`, `x^2`, `_x`),
exact arithmetic by default, and number theory via PARI/GP.

The name honors the Hungarian mathematician **Paul Erdős**: in Spanish, "Erdős" sounds like "ER-dos", i.e. *ER2*.

- Original idea: [draft/ER2_idea_summary.md](draft/ER2_idea_summary.md) (local only: `draft/` is gitignored)
- Project plan (phases, tasks, acceptance criteria): [PLAN.md](PLAN.md)
- **The language, normatively: [docs/LANGUAGE.md](docs/LANGUAGE.md)** — it owns the table of
  differences from Python (§3) and every rule carries an identifier a test can cite.
- PARI → ER2 function names: [docs/PARI_FUNCTIONS.md](docs/PARI_FUNCTIONS.md)
- Technical design and decisions (D1–D15): [ARCHITECTURE.md](ARCHITECTURE.md) — **read before implementing**.
- Releases and versioning policy: [CHANGELOG.md](CHANGELOG.md). Contributor rules: [CONTRIBUTING.md](CONTRIBUTING.md).
- Status: 0.4.2 released; M1–M4 done (M3 was the MVP), plus `er2.oeis`. **M5 (0.5, algebra) is
  complete**, acceptance included: linear algebra with `Matrix`, finite fields with `GF`,
  polynomials over `F_p`, `resultant`/`discriminant`, `groebner`/`reduce` and `NumberField`.
  **0.5.1 (scientific articles, ARCHITECTURE §1.3) is done** too: `examples/article.qmd`, and
  **0.5.2 (learnability and speed, §1.4 and §1.5)**: matrix calls are 3–6× faster and §2.1
  records where a call's time actually goes.
  **M6 (0.6, series) is complete**, acceptance included: power series through PARI, the three
  operations SymPy lacks, `DirichletSeries`, Euler products and `generating_function`. **0.6.1**
  makes Quarto documents show their cells as ER2, with real ER2 highlighting.
  **M7 (0.7, the language specification) is complete**, acceptance included:
  [docs/LANGUAGE.md](docs/LANGUAGE.md) is normative and owns the table of differences,
  `ARCHITECTURE.md` §1.1 links to it, and all 85 of its rules are mapped to tests by the
  `COVERAGE` table in `tests/test_language_spec.py`, which fails if a rule is added without
  deciding how it is checked. Scientific interop is tested across NumPy, Matplotlib, pandas and
  SciPy. Next: M8 (1.0) in [PLAN.md](PLAN.md). D1–D21 are all resolved; 0.5 is unreleased, so the
  changes are under **Unreleased** in [CHANGELOG.md](CHANGELOG.md).

## Guiding principle

> Do not create a new language unnecessarily. Extend Python only where it is unnatural for mathematics.

**Python compatibility is a hard requirement** (ARCHITECTURE.md §1.1, SageMath model): all Python syntax works in ER2, and any library is usable via normal `import`. Only `.er2` sources are preparsed — `.py` modules and installed libraries are never touched. The only intended differences inside `.er2` files are listed in the **[docs/LANGUAGE.md](docs/LANGUAGE.md) §3 table**, which owns them (`^` = power, `^^` = XOR, exact integer literals, `sym`, `5r` raw literals, the ER2 text echoed by `f"{a^2=}"`); never add another without updating that table and asking the user, and `tests/test_language_spec.py` fails if it grows.

**Notebooks are a hard requirement** (ARCHITECTURE.md §1.2): ER2 code must run in Jupyter and Quarto, through the `er2` kernel and through `%load_ext er2`. Every feature must work in those environments, not only in `er2 file.er2`.

Quarto cells are **`` ```{python} ``, never `` ```{er2} ``** (D9): Quarto decides what to execute
from the block's language before the kernel is consulted, so an `` ```{er2} `` block is silently
*not executed* while the render still exits 0. Documents are shown as ER2 by
`examples/er2-cells.lua` (renames the displayed language) and `examples/er2.xml` (highlights it),
switched on in `examples/_quarto.yml`. A test fails if any of those stops working. ARCHITECTURE
§1.2 records the measurements — read it before re-opening this.

**PEP 8 is a hard requirement** (ARCHITECTURE.md §6.1): it applies to the implementation, the public API names, and the ER2 code in examples and docs.

**Three goals shape design choices** (ARCHITECTURE.md §1.3, §1.4, §1.5): a paper should be
writable in ER2; a Python programmer should learn ER2 in an afternoon, so the LANGUAGE.md §3 table
stays the whole language; and ER2 should be faster than SymPy while charging little over PARI. On the
last one, **measure before you explain** — dispatch is cheap and conversion is not (§2.1), and
the end-to-end figure is the only one to quote, never the backend's.

In practice:
- ER2 = **source-to-source preparser** + **Python runtime** + **backends** (SymPy, cypari2/PARI). Do not write an interpreter, compiler, or custom grammar.
- Do **not** fork CPython, SymPy, PARI, or cypari2 during 0.x. Use them as dependencies.
- Every new piece of syntax must be expressible as a token transformation into valid Python.
- Do not reimplement algorithms that PARI or SymPy already provide.

## Implementation rules

- **Preparser**: use the `tokenize` module, never regex over the text. Do not touch strings, comments, or f-strings. Preserve line numbers.
- **Centralized dispatch**: public functions (`factor`, `isprime`, …) choose their backend in `er2/dispatch.py`. Backends never import each other.
- **Never `import sympy` at module level** in `er2/`: use `er2._lazy` (`sympy()`, `sympy_loaded()`), so number-only programs never load SymPy (`tests/test_lazy_sympy.py` guards this).
- **Conversions only at the backend boundary** (`to_pari`/`from_pari`, `to_sympy`/`from_sympy`). Users must not receive raw `cypari2.gen` objects.
- **Changelog**: every user-visible change gets a line in [CHANGELOG.md](CHANGELOG.md) under
  **Unreleased** (`CONTRIBUTING.md` has the full pull-request checklist).
- **New public functions** need a golden LaTeX sample in `tests/test_latex_coverage.py`, and new
  mathematical types need one in `TYPE_SAMPLES` there; both tests fail otherwise.
- **ER2 names ≠ PARI names**: `phi→eulerphi`, `mu→moebius`, `Omega` (draft) → `bigomega` (PEP 8, D8). In PARI `psi` is digamma: ER2 has `dedekind_psi` and `pari.digamma`, and no bare `psi` (D5). The single table is `er2/data/pari_functions.csv` (edit by hand). `docs/PARI_FUNCTIONS.md` is generated by `uv run python tools/sync_pari_functions.py`; never edit the generated file.
- **Output**: mathematical notation (`x^2`, `(x + 1)^2`), via the printer in `er2/printing.py`.
- **Same answer from both backends**: when PARI and SymPy can both do a job, the PARI route must
  return what SymPy returns (M4 `factor`, M5 linear algebra and `factor(f, modulus=p)`), and a
  test compares them on random input. Where a convention had to be chosen, ARCHITECTURE §3.4
  records it. **One deliberate exception, D21**: `expand` of a *quotient* of power series, where
  SymPy's `expand` does not answer at all and PARI's result matches `sympy.series` instead. An
  exception needs the user's decision and a test pinning the premise, never a silent divergence.
- **No PARI object outlives the call that made it** (M4): ER2 types store plain Python data, as
  `FiniteFieldElement` does with its coefficients.
- **LaTeX is a hard requirement** (ARCHITECTURE §3.6): every new mathematical type must support `latex()` and define `_repr_latex_` by calling it, and must have a golden LaTeX test. Never use PARI's `Strtex`.
- When a task touches an open decision (D1–D15, all resolved so far) or needs a new convention, propose a resolution to the user and record it in ARCHITECTURE.md §6 — do not decide silently.
- Useful precedent for design questions: the SageMath preparser (`^`, `Integer`, `^^` for XOR).

## Environment

- Python 3.14 (minimum: 3.12, as `pyproject.toml` requires). Package manager: `uv`.
- `draft/` is gitignored: private notes, never committed.
- Virtual env: `.venv/` managed by `uv sync`. Dependencies in `pyproject.toml`.
- **Minimal dependencies**: runtime = `sympy` + `cypari2`; dev = `pytest` + `ruff`. Do not add a dependency unless a task truly needs it (e.g. `ipykernel` as the optional extra `er2[jupyter]`, `oeis-tools` as `er2[oeis]`).
- **OEIS tests never use the network**: they read `tests/oeis/data/` (recorded responses). `ER2_NETWORK_TESTS=1 uv run pytest tests/oeis` also runs the live test.
- Quarto 1.9 is installed on this machine (`quarto render`), used for the Quarto tests.
- **PARI comes from cypari2** (its wheel bundles libpari 2.17.2). Do not depend on a system PARI/GP install or the `gp` binary — not for the code, not for tests. To check an expected value:
  `uv run python -c "import cypari2; print(cypari2.Pari().eulerphi(123456))"`

## Code style

- PEP 8 + PEP 257 docstrings, line length 79. Before finishing any code change, run `uv run ruff format` and `uv run ruff check`, and make sure they are clean.
- Public functions are `lower_case`, classes `CapWords`. Do not introduce names like `Omega`.
- ER2 code in examples and docs is also PEP 8 style (`x^2 + 2*x + 1`, `sym x, y`).

## Commands

The [Makefile](Makefile) wraps these (`make` lists the targets; `make check` = lint + tests,
`make render FILE=x.qmd` sets `QUARTO_PYTHON` and restarts the Quarto daemon).

```bash
uv sync                          # install dependencies (dev group included)
uv run ruff format && uv run ruff check   # PEP 8
uv run pytest                    # all tests (the Quarto test is skipped without quarto)
uv run pytest tests/preparser    # preparser only
uv run er2 file.er2              # run an ER2 program
uv run er2 --show-python f.er2   # show the Python generated by the preparser
uv run er2                       # REPL
uv run er2 kernel install        # register the ER2 Jupyter kernel (--user default, --sys-prefix)
uv run python benchmarks/run.py --write   # regenerate docs/BENCHMARKS.md
uv run python tools/sync_pari_functions.py   # regenerate the PARI table docs
uv run --with fonttools python tools/make_logo.py   # regenerate assets/ (logo, icon)
```

Quarto started from an editor may only see the kernels inside `.venv`; `er2 kernel install
--sys-prefix` puts the ER2 kernel there. Quarto keeps a kernel daemon running. After changing the kernel code, run
`quarto render --execute-daemon-restart`, or set `execute: daemon: false` (the tests do this).

## Tests

- Compatibility (`tests/compat/`): plain Python must behave identically; imports and ER2 values passed to libraries must work. Any change to the preparser or number types must keep this suite green.
- Preparser: `.er2` input → expected Python pairs; include cases with `^` and `sym` inside strings/comments.
- Backends: expected values computed with cypari2's PARI (number theory) and SymPy (CAS), hard-coded in the tests.
- Golden tests: programs in `tests/examples/` with their expected output.
- Avoid tests with factorizations that may take long (see D7).

## Language

**Everything in this project is in English**: code, identifiers, comments, docstrings, documentation, commit messages, and file names. (Conversation with the user may be in Spanish.)
