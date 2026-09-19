# ER2 — Mathematical Python

[![CI](https://github.com/oeistools/ER2/actions/workflows/ci.yml/badge.svg)](https://github.com/oeistools/ER2/actions/workflows/ci.yml)
[![Status: early development](https://img.shields.io/badge/status-0.4.2%20early%20development-orange)](PLAN.md)
[![Python 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: PEP 8](https://img.shields.io/badge/code%20style-PEP%208-blue)](https://peps.python.org/pep-0008/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PARI/GP](https://img.shields.io/badge/powered%20by-PARI%2FGP-8a2be2)](https://pari.math.u-bordeaux.fr/)
[![SymPy](https://img.shields.io/badge/powered%20by-SymPy-3b5526)](https://www.sympy.org/)
[![Jupyter](https://img.shields.io/badge/runs%20in-Jupyter-F37626?logo=jupyter&logoColor=white)](ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![Quarto](https://img.shields.io/badge/runs%20in-Quarto-39729E?logo=quarto&logoColor=white)](ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![Cite](https://img.shields.io/badge/cite-CITATION.cff-lightgrey)](CITATION.cff)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)

**ER2** is Python with mathematics built in: symbolic syntax, exact arithmetic by default, and
computational number theory powered by [PARI/GP](https://pari.math.u-bordeaux.fr/).

It is named after the Hungarian mathematician **Paul Erdős**. In Spanish, "Erdős" sounds like
"ER-dos", which is where *ER2* comes from.

## Why ER2?

- **Write mathematics as mathematics.** `x^2` is a power, `1/3` is exactly one third, and
  `sym x` declares a symbol. There are no imports and no `Rational(1, 3)`.
- **Two engines, one language.** ER2 sends each computation to the right backend: SymPy for
  symbolic algebra and PARI/GP, one of the fastest number theory systems, for integers, primes
  and modular arithmetic.
- **It is still Python.** All Python syntax works, every library imports as usual, and ER2 runs in
  Jupyter and Quarto with LaTeX output.

## Quick start

ER2 is not on PyPI yet. You need Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/); PARI comes
inside the cypari2 wheel, so there is nothing else to install.

```bash
git clone https://github.com/oeistools/ER2.git && cd ER2
uv sync
uv run er2 examples/hello.er2
```

```text
Hello from ER2
1024 1/2
x^3 + 3*x^2 + 3*x + 1
True
```

Then try the REPL (`uv run er2`), write your own `program.er2`, or open a notebook: see
[Jupyter and Quarto](#jupyter-and-quarto). `uv run er2 --show-python program.er2` shows the Python
that ER2 generates.

## A taste of ER2

```python
import numpy as np            # any Python library, imported as usual

sym x                         # declare a symbol
f = x^2 + 2*x + 1             # ^ means power

print(factor(f))              # (x + 1)^2
print(diff(f, x))             # 2*x + 2
print(latex(f))               # x^{2} + 2 x + 1  (any expression → LaTeX)

print(1/3)                    # 1/3, exact and not 0.333...
print(isprime(2^521 - 1))     # True  (PARI)
print(phi(123456789))         # 82260072
print(factor(2^127 - 1))      # 2^127 - 1 is prime
print(factor(360))            # 2^3 * 3^2 * 5

for k in range(1, 20):        # ordinary Python
    if isprime(k):
        print(k)

np.zeros(2^3)                 # ER2 numbers pass straight into libraries
```

## Examples

Each program runs with `uv run er2 examples/<name>.er2`, and its expected output is checked by the
test suite.

| Example | What it shows |
|---------|---------------|
| [hello.er2](examples/hello.er2) | The smallest tour: power, exact division, algebra, a primality test |
| [syntax.er2](examples/syntax.er2) | Every ER2 syntax difference from Python: `^`, `^^`, exact literals, `sym`, `5r` |
| [factorization.er2](examples/factorization.er2) | One `factor` for integers, rationals and polynomials; partial factorizations |
| [mvp.er2](examples/mvp.er2) | The MVP program: CAS and number theory together |
| [demo.qmd](examples/demo.qmd) | A Quarto tour with rendered math, including the OEIS (`make render`) |
| [mvp.ipynb](examples/mvp.ipynb) | The MVP as a Jupyter notebook |

## Documentation

| If you want to… | Read |
|-----------------|------|
| **Use ER2** | This README, the [examples](#examples), and [docs/PARI_FUNCTIONS.md](docs/PARI_FUNCTIONS.md) (every PARI function and its ER2 name) |
| **Understand the design** | [ARCHITECTURE.md](ARCHITECTURE.md): the compatibility contract, the components, and the design decisions D1–D15 |
| **Follow the project** | [PLAN.md](PLAN.md) (milestones and acceptance criteria), [CHANGELOG.md](CHANGELOG.md) (releases and versioning policy), [docs/BENCHMARKS.md](docs/BENCHMARKS.md) |
| **Contribute** | [CONTRIBUTING.md](CONTRIBUTING.md): setup, tests, rules for each part of the code, good first contributions |

The original idea is in [draft/ER2_idea_summary.md](draft/ER2_idea_summary.md), and the rules for
AI-assisted development are in [CLAUDE.md](CLAUDE.md).

## Python compatibility

ER2 is a superset of Python and follows the same model as SageMath:

- **All Python syntax works**: classes, decorators, generators, `async`, `match`, f-strings, type hints, and the rest.
- **The whole ecosystem is available** through normal `import`: NumPy, SciPy, pandas, Matplotlib, and so on.
- **Only `.er2` sources are translated.** Your `.py` modules and installed libraries run as ordinary Python and are never modified.
- **Inside `.er2` files there are only a few deliberate differences**:

  | Construct   | Python        | ER2                           |
  |-------------|---------------|-------------------------------|
  | `a ^ b`     | XOR           | power                         |
  | `a ^^ b`    | syntax error  | XOR                           |
  | `1/3`       | `0.333…`      | exact rational `1/3`          |
  | `sym x, y`  | syntax error  | declares symbols `x`, `y`     |
  | `5r`        | syntax error  | the plain Python `int` 5      |

## Jupyter and Quarto

ER2 runs in notebooks and in Quarto documents:

- **ER2 kernel**: run `er2 kernel install`, then pick "ER2" in Jupyter. In Quarto, set `jupyter: er2` in the front matter. If Quarto or your editor reports `Jupyter kernel 'er2' not found`, it is only looking inside the project's virtual environment: run `er2 kernel install --sys-prefix` as well. In VS Code, the Quarto **Preview** button uses the system Python unless `QUARTO_PYTHON` is set. Add `"terminal.integrated.env.linux": {"QUARTO_PYTHON": "${workspaceFolder}/.venv/bin/python"}` to `.vscode/settings.json`.
- **Any Python kernel**: add `%load_ext er2` in the first cell.
- **LaTeX everywhere**: expressions render as math. `show(f)` displays one, and
  `` `{python} latex(f)` `` puts inline math in Quarto text.

````markdown
---
title: "Mersenne primes"
jupyter: er2
---

```{python}
[p for p in range(2, 130) if isprime(2^p - 1)]
```
````

## How it works

ER2 does not introduce a new interpreter. It has three parts:

```text
.er2 source ──► preparser ──► plain Python ──► CPython
                                                  │
                                    ER2 runtime (types, printing, dispatch)
                                          │                 │
                                        SymPy          cypari2 → PARI
                                    (symbolic math)   (number theory)
```

1. **Preparser.** A token-level, source-to-source translation from `.er2` to Python.
2. **Runtime.** The `er2` package provides the mathematical types and the functions (`factor`, `diff`, `phi`, …).
3. **Backends.** [SymPy](https://www.sympy.org/) handles symbolic computation, and PARI is accessed through [cypari2](https://github.com/sagemath/cypari2). ER2 chooses the backend automatically, so `factor` works on both polynomials and integers.

## Status and roadmap

**Version 0.4.2, early development.** Milestones M1–M4 are done (M3 was the MVP), and M5 is
planned. [CHANGELOG.md](CHANGELOG.md) says what is stable and what is still experimental.

| Version | Focus | Status |
|---------|-------|--------|
| 0.1 | Preparser: `sym`, `^`, `_x`, exact integers and rationals; Jupyter kernel, `%load_ext er2`, Quarto | ✅ |
| 0.2 | CAS on SymPy: `expand`, `factor`, `simplify`, `diff`, `integrate`, `limit`, `solve`, `series` | ✅ |
| 0.3 | Number theory on PARI: primality, factorization, `phi`, `sigma`, `mu`, … (the MVP) | ✅ |
| 0.4 | Automatic backend selection, PARI types (`Mod`, `Qfb`, series), benchmarks, the OEIS | ✅ |
| 0.5 | Algebra: matrices, finite fields, resultants, Gröbner bases, number fields | planned |
| 0.6 | Series: power, Dirichlet, Euler products | |
| 1.0 | Stable language: specification, PyPI package, documentation site | |

Beyond the table, every PARI function is available as `pari.<name>`, and PARI's sums and integrals
take Python functions (`pari.sum(lambda n: 1/n^2, 1, 10)`). Deeper CPython integration comes only
after the syntax is stable.

## Development

```bash
make install                    # uv sync + the ER2 kernel inside .venv
make test-fast                  # the tests without Jupyter and Quarto
make check                      # ruff + all tests, as in CI
make install-global             # the `er2` command for your user, editable (uv tool)
make preview FILE=my_doc.qmd    # live Quarto preview with the ER2 kernel
```

`make` lists every target. `make install-global` puts `er2` in `~/.local/bin`. It is an editable
install, so it follows changes to the code, and it registers the ER2 kernel for your user.

We keep dependencies deliberately minimal: `sympy` and `cypari2` at runtime, plus `ipykernel` and
`oeis-tools` as the optional `er2[jupyter]` and `er2[oeis]` extras. Development uses `pytest` and
`ruff`. The code follows [PEP 8](https://peps.python.org/pep-0008/).

## Contributing

ER2 is maintained by **Enrique Pérez Herrero** ([energycode.org@gmail.com](mailto:energycode.org@gmail.com)).

Contributions are welcome, from a bug report with a three-line example to a new feature.
[CONTRIBUTING.md](CONTRIBUTING.md) explains how to set up, what a pull request needs, and where to
start if you are new to the project.

## Citation

If you use ER2 in your work, please cite it. The metadata is in [CITATION.cff](CITATION.cff), and
GitHub shows it through **"Cite this repository"**. Please also cite
[PARI/GP](https://pari.math.u-bordeaux.fr/) and [SymPy](https://doi.org/10.7717/peerj-cs.103),
which ER2 builds on.

## License

[MIT](LICENSE)
