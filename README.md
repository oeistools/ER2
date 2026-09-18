# ER2 — Mathematical Python

[![CI](https://github.com/oeistools/ER2/actions/workflows/ci.yml/badge.svg)](https://github.com/oeistools/ER2/actions/workflows/ci.yml)
[![Status: design stage](https://img.shields.io/badge/status-design%20stage-orange)](PLAN.md)
[![Python 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: PEP 8](https://img.shields.io/badge/code%20style-PEP%208-blue)](https://peps.python.org/pep-0008/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PARI/GP](https://img.shields.io/badge/powered%20by-PARI%2FGP-8a2be2)](https://pari.math.u-bordeaux.fr/)
[![SymPy](https://img.shields.io/badge/powered%20by-SymPy-3b5526)](https://www.sympy.org/)
[![Jupyter](https://img.shields.io/badge/runs%20in-Jupyter-F37626?logo=jupyter&logoColor=white)](ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![Quarto](https://img.shields.io/badge/runs%20in-Quarto-39729E?logo=quarto&logoColor=white)](ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![Cite](https://img.shields.io/badge/cite-CITATION.cff-lightgrey)](CITATION.cff)

**ER2** is Python with mathematics built in: symbolic syntax, exact arithmetic by default, and
computational number theory powered by [PARI/GP](https://pari.math.u-bordeaux.fr/).

It is named after the Hungarian mathematician **Paul Erdős**. In Spanish, "Erdős" sounds like
"ER-dos", which is where *ER2* comes from.

> **Status: design stage.** There is no working code yet. This README describes what ER2 is meant to
> be. See [ARCHITECTURE.md](ARCHITECTURE.md) for the technical design and the open decisions.

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

for k in range(1, 20):        # ordinary Python
    if isprime(k):
        print(k)

np.zeros(2^3)                 # ER2 numbers pass straight into libraries
```

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

## Jupyter and Quarto

ER2 runs in notebooks and in Quarto documents:

- **ER2 kernel**: run `er2 kernel install`, then pick "ER2" in Jupyter. In Quarto, set `jupyter: er2` in the front matter.
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

## Roadmap

| Version | Focus |
|---------|-------|
| 0.1 | Preparser: `sym`, `^`, `_x`, exact integers and rationals; Jupyter kernel, `%load_ext er2`, Quarto |
| 0.2 | CAS: `expand`, `factor`, `simplify`, `diff`, `integrate`, `solve` |
| 0.3 | Number theory on PARI: primality, factorization, `phi`, `sigma`, `mu`, … |
| 0.4 | Automatic backend selection, PARI types, benchmarks |
| 0.5 | Algebra: matrices, finite fields, resultants, Gröbner bases |
| 0.6 | Series: power, Dirichlet, Euler products |
| 1.0 | Stable language: specification, installable package |

Later: OEIS integration (`oeis.search`, `oeis.identify`). Deeper CPython integration comes only
after the syntax is stable.

## Development

Requirements: Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/). There are no system dependencies,
because the cypari2 wheel includes PARI.

```bash
git clone https://github.com/oeistools/ER2.git && cd ER2
uv sync          # creates .venv with sympy, cypari2, pytest and ruff
uv run pytest
```

We keep dependencies deliberately minimal: `sympy` and `cypari2` at runtime, plus `ipykernel` as
the optional `er2[jupyter]` extra. Development uses `pytest` and `ruff`. The code follows
[PEP 8](https://peps.python.org/pep-0008/), enforced with `uv run ruff format` and `uv run ruff check`.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md): technical design, the compatibility contract, and open design decisions
- [PLAN.md](PLAN.md): project plan, with phases and acceptance criteria
- [docs/PARI_FUNCTIONS.md](docs/PARI_FUNCTIONS.md): all PARI functions and their ER2 names
- [draft/ER2_idea_summary.md](draft/ER2_idea_summary.md): the original idea
- [CLAUDE.md](CLAUDE.md): guidelines for AI-assisted development

## Citation

If you use ER2 in your work, please cite it. The metadata is in [CITATION.cff](CITATION.cff), and
GitHub shows it through **"Cite this repository"**. Please also cite
[PARI/GP](https://pari.math.u-bordeaux.fr/) and [SymPy](https://doi.org/10.7717/peerj-cs.103),
which ER2 builds on.

## License

[MIT](LICENSE)
