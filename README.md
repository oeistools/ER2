<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/oeistools/ER2/main/assets/er2-logo-dark.svg">
    <img alt="ER2 — Mathematical Python" src="https://raw.githubusercontent.com/oeistools/ER2/main/assets/er2-logo.svg" width="400">
  </picture>
</h1>

[![ER2](https://img.shields.io/badge/ER2-mathematical%20Python-8a2be2)](https://oeistools.github.io/ER2/)
[![CI](https://github.com/oeistools/ER2/actions/workflows/ci.yml/badge.svg)](https://github.com/oeistools/ER2/actions/workflows/ci.yml)
[![Release](https://github.com/oeistools/ER2/actions/workflows/release.yml/badge.svg)](https://github.com/oeistools/ER2/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/er2?label=pypi)](https://pypi.org/project/er2/)
[![Pages](https://github.com/oeistools/ER2/actions/workflows/pages.yml/badge.svg)](https://oeistools.github.io/ER2/)
[![Python 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](https://github.com/oeistools/ER2/blob/main/pyproject.toml)
[![Jupyter](https://img.shields.io/badge/runs%20in-Jupyter-F37626?logo=jupyter&logoColor=white)](https://github.com/oeistools/ER2/blob/main/ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![Quarto](https://img.shields.io/badge/runs%20in-Quarto-39729E?logo=quarto&logoColor=white)](https://github.com/oeistools/ER2/blob/main/ARCHITECTURE.md#12-notebooks-jupyter-and-quarto)
[![PARI/GP](https://img.shields.io/badge/powered%20by-PARI%2FGP-8a2be2)](https://pari.math.u-bordeaux.fr/)
[![SymPy](https://img.shields.io/badge/powered%20by-SymPy-3b5526)](https://www.sympy.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/oeistools/ER2/blob/main/LICENSE)

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

ER2 is on PyPI as [`er2`](https://pypi.org/project/er2/). It needs Python ≥ 3.12. PARI comes
inside the cypari2 wheel, so there is nothing else to install.

| Platform | Status |
|----------|--------|
| Linux | ✅ Supported, and tested in CI |
| macOS | ⚠️ Experimental: cypari2 has macOS wheels, but ER2's CI does not run on macOS yet |
| Windows | ❌ Not supported: cypari2 has no Windows build (WSL works, as Linux) |

```bash
pip install er2                 # or: uv tool install er2
pip install "er2[jupyter]"      # with the Jupyter kernel
pip install "er2[oeis]"         # with access to the OEIS
```

Save this as `hello.er2` and run `er2 hello.er2`:

```python
print("Hello from ER2")
print(2^10, 1/3 + 1/6)      # ^ is power; division is exact
sym x
print(expand((x + 1)^3))    # symbolic algebra
print(isprime(2^127 - 1))   # number theory, by PARI
```

```text
Hello from ER2
1024 1/2
x^3 + 3*x^2 + 3*x + 1
True
```

Then try the REPL (`er2`) or open a notebook: see [Jupyter and Quarto](#jupyter-and-quarto).
`er2 --show-python hello.er2` shows the Python that ER2 generates. To work on ER2 itself, clone
the repository instead: see [Development](#development).

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
| [hello.er2](https://github.com/oeistools/ER2/blob/main/examples/hello.er2) | The smallest tour: power, exact division, algebra, a primality test |
| [syntax.er2](https://github.com/oeistools/ER2/blob/main/examples/syntax.er2) | Every ER2 syntax difference from Python: `^`, `^^`, exact literals, `sym`, `5r` |
| [factorization.er2](https://github.com/oeistools/ER2/blob/main/examples/factorization.er2) | One `factor` for integers, rationals and polynomials; partial factorizations |
| [mvp.er2](https://github.com/oeistools/ER2/blob/main/examples/mvp.er2) | The MVP program: CAS and number theory together |
| [demo.qmd](https://github.com/oeistools/ER2/blob/main/examples/demo.qmd) | A Quarto tour with rendered math, including the OEIS (`make render`) |
| [mvp.ipynb](https://github.com/oeistools/ER2/blob/main/examples/mvp.ipynb) | The MVP as a Jupyter notebook |

## Documentation

The documentation site is at **<https://oeistools.github.io/ER2/>**, built by Quarto and executed by ER2 itself.

| If you want to… | Read |
|-----------------|------|
| **Use ER2** | This README, the [examples](#examples), and [docs/PARI_FUNCTIONS.md](https://github.com/oeistools/ER2/blob/main/docs/PARI_FUNCTIONS.md) (every PARI function and its ER2 name) |
| **Know exactly what the language is** | [docs/LANGUAGE.md](https://github.com/oeistools/ER2/blob/main/docs/LANGUAGE.md): the normative specification — the differences from Python, precedence, the number model, and what is stable before 1.0 |
| **Understand the design** | [ARCHITECTURE.md](https://github.com/oeistools/ER2/blob/main/ARCHITECTURE.md): the compatibility contract, the components, and the design decisions D1–D17 |
| **Follow the project** | [PLAN.md](https://github.com/oeistools/ER2/blob/main/PLAN.md) (milestones and acceptance criteria), [CHANGELOG.md](https://github.com/oeistools/ER2/blob/main/CHANGELOG.md) (releases and versioning policy), [docs/BENCHMARKS.md](https://github.com/oeistools/ER2/blob/main/docs/BENCHMARKS.md) |
| **Contribute** | [CONTRIBUTING.md](https://github.com/oeistools/ER2/blob/main/CONTRIBUTING.md): setup, tests, rules for each part of the code, good first contributions |

The rules for AI-assisted development are in [CLAUDE.md](https://github.com/oeistools/ER2/blob/main/CLAUDE.md).

## Algebra (0.5)

```python
sym x, y

det(Matrix([[2, 1], [1, 3]]))        # 5, computed by PARI
kernel(Matrix([[1, 2], [2, 4]]))     # [Matrix([[1], [-1/2]])]
smith_form(Matrix([[2, 4], [6, 8]])) # Matrix([[2, 0], [0, 4]]), as SymPy's

factor(x^8 - x, modulus=2)           # x*(x + 1)*(x^3 + x + 1)*(x^3 + x^2 + 1)
isirreducible(x^2 + x + 1, modulus=2)   # True

a = GF(9).gen()                      # the finite field with 9 elements
a^4, a.order(), minpoly(a)           # 2, 8, x^2 + x + 2

resultant(x^2 + 1, x^3 - 2, x)       # 5
discriminant(x^3 + x + 1)            # -31

G = groebner([x^2 + y^2 - 1, x - y], x, y)
list(G)                              # [x - y, 2*y^2 - 1]
reduce(x^2 + y^2, G)                 # 1, the normal form

K = NumberField(x^2 + 5)             # Q(sqrt(-5))
K.discriminant, K.class_number()     # -20, 2
K.factor(2)                          # [((2, x + 1), 2)]: 2 ramifies
K.factor(3)                          # 3 splits into two primes
```

`resultant` follows the standard sign convention, which is PARI's, so
`resultant(f, g)` and `resultant(g, f)` differ in sign when both degrees are odd
(ARCHITECTURE.md §6, D16). A class number is only as good as the GRH unless you ask for
`certify=True`.

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

**Version 0.7.0, early development.** Milestones M1–M7 are done (M3 was the MVP). Algebra
(matrices, finite fields, `F_p`, resultants, Gröbner bases, `NumberField`), series (power,
Dirichlet, Euler products) and the language specification are all in.
[docs/LANGUAGE.md](https://github.com/oeistools/ER2/blob/main/docs/LANGUAGE.md) now defines the language normatively, and
[CHANGELOG.md](https://github.com/oeistools/ER2/blob/main/CHANGELOG.md) says what is stable, what is still experimental, and what has
changed. 0.7.0 is [on PyPI](https://pypi.org/project/er2/), the
[documentation site](https://oeistools.github.io/ER2/) is live, and
[docs/STABILITY.md](https://github.com/oeistools/ER2/blob/main/docs/STABILITY.md) sets the
stability policy. What remains is 1.0 itself, which freezes the syntax and the public API.

| Version | Focus | Status |
|---------|-------|--------|
| 0.1 | Preparser: `sym`, `^`, `_x`, exact integers and rationals; Jupyter kernel, `%load_ext er2`, Quarto | ✅ |
| 0.2 | CAS on SymPy: `expand`, `factor`, `simplify`, `diff`, `integrate`, `limit`, `solve`, `series` | ✅ |
| 0.3 | Number theory on PARI: primality, factorization, `phi`, `sigma`, `mu`, … (the MVP) | ✅ |
| 0.4 | Automatic backend selection, PARI types (`Mod`, `Qfb`, series), benchmarks, the OEIS | ✅ |
| 0.5 | Algebra: matrices, finite fields, resultants, Gröbner bases, number fields | ✅ |
| 0.6 | Series: power, Dirichlet, Euler products | ✅ |
| 0.7 | The language specification, `docs/LANGUAGE.md`; first PyPI release | ✅ |
| 1.0 | Frozen syntax and public API (documentation site and stability policy done) | in progress |

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
[CONTRIBUTING.md](https://github.com/oeistools/ER2/blob/main/CONTRIBUTING.md) explains how to set up, what a pull request needs, and where to
start if you are new to the project.

## Citation

If you use ER2 in your work, please cite it. The metadata is in [CITATION.cff](https://github.com/oeistools/ER2/blob/main/CITATION.cff), and
GitHub shows it through **"Cite this repository"**. Please also cite
[PARI/GP](https://pari.math.u-bordeaux.fr/) and [SymPy](https://doi.org/10.7717/peerj-cs.103),
which ER2 builds on.

## License

[MIT](https://github.com/oeistools/ER2/blob/main/LICENSE)
