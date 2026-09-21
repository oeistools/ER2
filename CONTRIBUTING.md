# Contributing to ER2

Thank you for helping. ER2 is small and young, so every contribution counts: a bug report with a
three-line example is as useful as a new feature.

- [Set up](#set-up)
- [Reporting a bug](#reporting-a-bug)
- [Making a change](#making-a-change)
- [Rules for each part of the code](#rules-for-each-part-of-the-code)
- [Good first contributions](#good-first-contributions)

## Set up

You need Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/). PARI comes inside the cypari2 wheel,
so there is nothing else to install.

```bash
git clone https://github.com/oeistools/ER2.git && cd ER2
make install          # uv sync + the ER2 Jupyter kernel inside .venv
make test-fast        # the tests without Jupyter and Quarto (~15 s)
```

`make` lists every target. The ones you will use most:

| Command | What it does |
|---------|--------------|
| `make test-fast` | All tests except the notebook and Quarto ones. Run it while you work. |
| `make check` | `ruff` + the full test suite: exactly what CI runs. Run it before a pull request. |
| `make format` | Format the code (`ruff format`, then `ruff check --fix`). |
| `uv run er2 --show-python file.er2` | Show the Python the preparser generates. |
| `uv run pytest tests/preparser -x` | One area of the suite (see the layout below). |

The notebook tests need Jupyter (installed by `uv sync`); the Quarto tests are skipped when
[Quarto](https://quarto.org/) is not installed. CI always runs both.

## Reporting a bug

Open an issue with the **Bug report** template. The most helpful report is a minimal `.er2`
program:

```
# bug.er2 — run with `er2 bug.er2`
print(divmod(7, 1/3))
```

with what it printed, what you expected, and the output of `er2 --version`. If the Python that
ER2 generates looks wrong, add the output of `er2 --show-python bug.er2`. For a wrong mathematical
value, say where the expected value comes from (GP, SageMath, SymPy, the OEIS, a reference).

## Making a change

1. For anything larger than a fix, open an issue first, so we can agree on the design.
   [ARCHITECTURE.md](ARCHITECTURE.md) is the design; read the part your change touches.
2. Work on a branch and keep each pull request to one topic.
3. Before you open the pull request, check:

   - [ ] `make check` passes (ruff format, ruff check, all tests).
   - [ ] New behavior has tests. Expected mathematical values come from PARI (through cypari2) or
         SymPy and are **hard-coded** in the test, with a comment saying how they were computed.
   - [ ] Every new mathematical type has `latex()` support, a `_repr_latex_` method that calls
         it, and a golden LaTeX test (`tests/test_latex_coverage.py` fails otherwise).
   - [ ] Every new public function has a golden LaTeX sample in `tests/test_latex_coverage.py`.
   - [ ] It works in the `er2` command, in Jupyter (the ER2 kernel and `%load_ext er2`) and in
         Quarto, not only in one of them.
   - [ ] User-visible changes have a line in [CHANGELOG.md](CHANGELOG.md) under **Unreleased**.
   - [ ] Code, comments, docs and commit messages are in English.

### Style

- [PEP 8](https://peps.python.org/pep-0008/) and PEP 257 docstrings, 79-character lines,
  enforced by `ruff`. Public functions are `lower_case` and classes are `CapWords`; ER2 names follow
  PEP 8 even where PARI's do not (`bigomega`, not `Omega`).
- ER2 code in examples and docs follows PEP 8 too: `x^2 + 2*x + 1`, `sym x, y`.
- Match the surrounding code: its comment density, naming and idioms.
- No new dependency without a written reason in ARCHITECTURE.md §8. Runtime dependencies are
  `sympy` and `cypari2` only.

## Rules for each part of the code

ER2 has three layers (README, "How it works"): the **preparser** turns `.er2` source into Python,
the **runtime** provides the types and public functions, and the **backends** do the mathematics.

| Area | Files | Tests | Rules |
|------|-------|-------|-------|
| Preparser | `er2/preparser.py` | `tests/preparser/`, `tests/compat/` | Work on tokens (`tokenize`), never with regular expressions over the text. Never change strings, comments or f-string text. Keep line numbers identical. **New syntax needs a new row in the [docs/LANGUAGE.md](docs/LANGUAGE.md) §3 table and the maintainer's agreement**, because Python compatibility is a hard requirement. |
| Numbers and types | `er2/runtime/` | `tests/runtime/`, `tests/compat/` | `Integer` must keep behaving like `int` everywhere (`range`, indexing, NumPy, `json`). Results stay exact ER2 numbers. |
| Public functions | `er2/dispatch.py` | `tests/test_dispatch.py` | This is the only place that chooses a backend. |
| PARI backend | `er2/backends/pari_backend.py`, `er2/data/pari_functions.csv` | `tests/backends/`, `tests/test_pari_functions.py` | Convert only at the boundary (`to_pari`/`from_pari`): users never get a raw `cypari2` object. Do not reimplement what PARI already does. Edit the CSV by hand, then run `make sync-pari`; never edit `docs/PARI_FUNCTIONS.md`. |
| SymPy backend | `er2/backends/sympy_backend.py` | `tests/backends/` | Never `import sympy` at module level in `er2/`; use `er2._lazy` (`tests/test_lazy_sympy.py` checks it). |
| Printing | `er2/printing.py` | `tests/test_printing.py`, `tests/test_latex_coverage.py` | ER2 notation (`x^2`), and LaTeX for everything. Never use PARI's `Strtex`. |
| Notebooks | `er2/session.py`, `er2/kernel.py` | `tests/notebooks/` | After changing the kernel, restart Quarto's daemon: `quarto render --execute-daemon-restart`. |
| OEIS | `er2/oeis.py` | `tests/oeis/` | Tests never use the network: they read recorded responses in `tests/oeis/data/`. |

Backends never import each other. Tests must stay fast: avoid factorizations that can take long
(decision D7).

When a change touches an open design question, propose a resolution in the issue or pull request.
The decisions are recorded in ARCHITECTURE.md §6.

## Good first contributions

These need no deep knowledge of the internals:

- **Examples.** Add a short program to `examples/` (a classic theorem, a sequence, a puzzle), and
  its expected output in `tests/examples/<name>.out`. The golden tests run it automatically.
- **Documentation.** Fix unclear passages in the README, add a Quarto example, or improve a
  docstring.
- **Tests.** Add cases with values checked against GP or SymPy, especially edge cases (0, 1,
  negative numbers, huge numbers).
- **The PARI table.** Review rows of `er2/data/pari_functions.csv`: propose a PEP 8 ER2 name or a
  note for a PARI function, then run `make sync-pari`.
- **Benchmarks.** Add a case to `benchmarks/run.py` and regenerate `docs/BENCHMARKS.md` with
  `make bench`.
- **Arithmetic functions.** Functions like `jordan_totient` and `radical` are small, self-contained
  additions: a backend function, a `dispatch` entry, tests and a LaTeX sample.

The milestones in [PLAN.md](PLAN.md) list the larger work that comes next (M5: matrices, finite
fields, Gröbner bases, number fields).

## Contact

ER2 is maintained by **Enrique Pérez Herrero**
([energycode.org@gmail.com](mailto:energycode.org@gmail.com)). Use GitHub issues for bugs and
proposals, so that the discussion stays public; write by email for anything that should not be
public, such as a security problem.

## Working with AI assistants

[CLAUDE.md](CLAUDE.md) collects the project rules for AI-assisted development. The same rules
apply to every contribution, however it was written.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
