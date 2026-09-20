# Changelog

All notable changes to ER2 are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). [PLAN.md](PLAN.md) has the full detail of
each milestone, and [ARCHITECTURE.md](ARCHITECTURE.md) §6 has the design decisions (D1–D17).

## Versioning policy

ER2 follows [Semantic Versioning](https://semver.org/) with the usual rule for 0.x releases:

| Version | Meaning |
|---------|---------|
| **0.x** (now) | Early development. A minor release (0.4 → 0.5) may change the public API. Each such change is listed here under **Changed** or **Removed**. |
| **0.x.y** | Additions and fixes only: no intended breaking change. |
| **1.0** | The language is stable (PLAN.md, M7): a normative preparser specification, a PyPI release and a deprecation policy. |

What is stable already, and what is not:

- **Stable:** the ER2 syntax in the §1.1 table of ARCHITECTURE.md (`^`, `^^`, exact integer
  literals, `sym`, `5r`). Any change to it requires updating that table and a changelog entry.
  Python compatibility (all Python syntax, any library through `import`) is a hard requirement.
- **Stable in intent, may still change before 1.0:** the curated prelude (`factor`, `phi`,
  `isprime`, `Mod`, …), `latex()` and `show()`, and the `er2` command.
- **Experimental:** `pari.<name>` (it follows PARI's own API and the PARI table), the `oeis`
  module, and the printed form of results (`repr`, LaTeX), which may improve between releases.

## [Unreleased]

### Added
- **Quarto documents show their cells as ER2 (0.6.1)**, with real ER2 syntax highlighting:
  `examples/er2.xml` is a KDE syntax definition that states the §1.1 table — `sym`, `5r`
  literals, `^^` — and includes Python's rules, so Python's half stays Pandoc's own.
  `examples/er2-cells.lua` renames the displayed language, and `examples/_quarto.yml` turns both
  on for every example in one place. Cells are still written `` ```{python} ``, which is what
  Quarto executes: an `` ```{er2} `` block is **not executed at all**, silently, whatever the
  kernelspec says (D9, ARCHITECTURE §1.2).
- **Series (M6, 0.6)**, with decisions D18–D21:
  - **Power series stay ordinary expressions** with an `O()` term (D18) — no new type to learn.
    What was missing were three operations SymPy does not have at all: `series_reverse` (the
    compositional inverse), `hadamard_product` (coefficientwise) and `series_laplace` (an
    exponential generating function read as an ordinary one).
  - **`expand` of a product of power series now goes to PARI**, 3 to 13 times faster depending
    on the precision (11 ms → 3.4 ms at six terms, 612 ms → 46 ms at eighty). `expand` is the
    hook because SymPy leaves `s * t` unevaluated, so it is already what a user types; there is
    no backend to choose.
  - **`expand` of a *quotient* of series (D21)**, which `sympy.expand` cannot do at all — it
    leaves nested fractions. ER2 returns the series, the same one `sympy.series` gives for the
    equivalent expression. This is the one deliberate place ER2's answer differs from
    `sympy.expand`, and a test pins the premise so it can be revisited.
  - **`DirichletSeries` (D19)**: `*` and `/` are Dirichlet convolution and division, `+` and `-`
    are coefficientwise, indexing starts at 1 as the mathematics does, and it renders as
    mathematics. `DirichletSeries.zeta(n)` and `.moebius(n)`; `DirichletSeries.euler(f, n)`
    builds a series from its Euler product.
  - **`generating_function(sequence, x, n)`**, ordinary or exponential, for anything iterable —
    including an `OEISSequence`, which joins `er2.oeis` (0.4.2) to the series machinery.
  - `examples/series.qmd` is the M6 acceptance, rendered in CI; `tests/examples/series.er2` is
    the golden program.
- **Two more stated goals** (ARCHITECTURE §1.4 and §1.5), both asked for on 2026-09-20.
  §1.4, *learnable in an afternoon by a Python programmer*, makes the §1.1 table the whole of
  what has to be learned and names what that rules out — a second way to write what Python
  already writes, names that need translating from PARI, a backend the user has to choose.
  §1.5, *faster than SymPy and close to PARI*, is stated as two separate comparisons because
  they are two different promises, and §2.1 records which one is met where.
- **ARCHITECTURE §2 now has a Mermaid diagram** of the components, with the previous ASCII
  drawing kept below it for readers without Mermaid, and a structural test
  (`tests/test_architecture_diagram.py`) so a broken diagram fails the suite rather than
  rendering as an error box on GitHub. Its colours are the logo's.
- **ARCHITECTURE §2.1, "Where the time goes"**: the three costs of a public call — choosing a
  backend, converting the arguments, computing — measured separately, because conflating them
  hides the fact that conversion is roughly 80% of a matrix call and the backend under 15%.
- **Writing scientific articles in ER2** is now a stated goal (ARCHITECTURE §1.3):
  `examples/article.qmd` is a small real paper whose numbers, table and figure are computed by the
  document that states them, rendered to HTML and PDF and checked in CI. Matplotlib joined the
  dev dependencies for the figure.
- The M5 acceptance: `examples/algebra.qmd` and the extended golden program
  `tests/examples/algebra.er2`, run in the CLI, in Quarto and through both Jupyter routes.
- `tests/compat/test_scientific.py`: the README's promise that ER2 numbers pass into NumPy is now
  tested, in CI too. It records that `Integer` gets a real NumPy dtype while `Rational` lands in
  an object array, which keeps `1/3` exact instead of silently rounding it.
- Number fields (M5, D14): `NumberField(x^2 + 5)` in the prelude, with `degree`, `discriminant`
  (the field's, not the polynomial's), `integral_basis()`, `class_number()`, `class_group()`,
  `units()`, `roots_of_unity()` and `factor(p)` into `PrimeIdeal`s. Elements are `Mod` objects
  with a polynomial modulus, so arithmetic already works. `bnfinit` runs once per field and only
  its results are cached, never a PARI structure, so `pari.set_stack()` cannot invalidate a
  field. Class groups and units assume the GRH unless `certify=True`.
- A logo and an icon in [assets/](assets/), with the brand notes in `assets/README.md`: the
  wordmark is `ER` beside a tile reading `^2`, the line you would actually type in an `.er2`
  source. The tile is the icon, so the icon is the second half of the name. The letterforms are
  Exo 2 ExtraBold (SIL OFL) stored as outlines, so nothing depends on an installed font, and the
  README picks the light or dark version from the reader's colour scheme. The files are
  generated by `tools/make_logo.py` (`make logo`), which documents every design decision;
  `--check` reports whether the committed files still match.
- Gröbner bases (M5): `groebner(F, *gens, order="lex")` through SymPy (PARI has none), returning
  a `GroebnerBasis` that prints in ER2 notation, and `reduce(f, G)`, the remainder of `f` modulo
  `G` — its normal form when `G` is a Gröbner basis, so `reduce(f, G) == 0` tests membership of
  the ideal (D17). Note that `f in G` is Python's list membership, not the ideal.
- Resultants and discriminants (M5): `resultant(f, g, x)` and `discriminant(f, x)`, computed by
  PARI for polynomials over Q and by SymPy for symbolic coefficients. The variable may be left
  out when the arguments have a single variable between them. ER2 uses the standard sign
  convention, PARI's (D16): `resultant(x - 1, x^3 - 8, x)` is `-7`, where `sympy.resultant`
  answers `7`.
- Polynomials over a prime field (M5): `factor(f, modulus=p)` and `gcd(f, g, modulus=p)` are
  computed by PARI, ×3–6 faster than SymPy, with the same result, and
  `isirreducible(f)` is new (over Q or with `modulus=p`). `domain=GF(p)` works too; over `GF(p^k)`
  ER2 has no polynomials yet and says so.
- Finite fields (M5): `GF(9)`, `GF(3, 2)` and `GF(9, "t")`, with arithmetic, `order`, `trace`,
  `norm`, `minpoly`, `charpoly`, `sqrt`, `log`, `primitive_element()` and `elements()`. Computed
  by PARI; `pari.<name>` results of type `t_FFELT` now come back as ER2 elements.
- Linear algebra (M5): `Matrix` in the prelude, and `det`, `inverse`, `rank`, `kernel`,
  `charpoly`, `minpoly`, `echelon_form`, `hermite_form`, `smith_form` and `solve(A, b)`. Matrices
  over Q are computed by PARI and the others by SymPy, with the same results.
- `jordan_totient(n, k)`: Jordan's totient J_k (GP: `sumdiv(n, d, d^k*moebius(n/d))`).
- `radical(n)`: the product of the distinct primes of `n` (GP: `factorback(factorint(n)[, 1])`).
- Example gallery: `examples/hello.er2`, `examples/syntax.er2` and `examples/factorization.er2`,
  checked by the golden tests.
- `CONTRIBUTING.md`, this changelog, and GitHub issue templates.
- The M5 (0.5, Algebra) plan, with decisions D12–D17.

### Changed
- **ER2 is now faster than SymPy on every benchmark that reaches PARI**, which it was not
  before: `factor` at degree 4 was ×1.23 *slower*, and `hermite_form` at 10×10 ×3.3 slower.
  Matrix calls are 3–6× faster and polynomial calls 2–3× faster, with no change to any result.
  In both cases the cost was the conversion around PARI, not PARI: a `factor` call spent three
  quarters of its conversion inside `sympy.together`, splitting a polynomial into a numerator
  and a denominator in order to find that the denominator is 1. A univariate polynomial over Q
  now goes straight to PARI's `Pol`.
- **Matrix calls in particular**, with no change to any result. Choosing a backend
  for a 10×10 matrix cost 135 µs — ten times the PARI call it was deciding about — because the
  predicate scanned every entry to ask whether they were rational. SymPy already records the
  answer in the matrix's domain, so the question is now settled in constant time (1.5 µs), and
  the conversions read entries out of that same representation instead of building a
  `sympy.Integer` for each one. `det` on a 10×10 went from 728 µs to 112 µs and `smith_form`
  from 865 µs to 257 µs.
  `hermite_form` was ×3.3 slower than SymPy's at 10×10 and is now ×1.4 faster, which closes the
  size threshold that §3.4 had listed as open work.
  ARCHITECTURE §2.1 has the measurements and the two rules they produced.
- The preparser is much faster on large files (a 16,000-line file: 22.6 s → 1.1 s).
- Requires `oeis-tools` ≥ 0.2.1, so `OEISSequence.bibtex()` works.

### Fixed
- A `sympy.expand` in the power-series conversion did nothing in every univariate case and cost
  250 µs, two thirds of that conversion.
- `hermite_form` of a matrix with no columns returned a 0×0 matrix, losing the row count, where
  SymPy's `hermite_normal_form` keeps the shape: PARI writes every empty matrix as `[;]`, so the
  shape cannot survive the round trip and the function now keeps it itself.
- Ctrl-C during an ER2 program (D7) made `er2 file.er2` exit with code 1, like any other error.
  It now ends the way `python file.py` does — killed by SIGINT, which a shell reports as 130 — so
  an interrupted run can be told apart from a failed one.
- `divmod(7, 1/3)` and `divmod(2, 7.5)` raised `TypeError`.
- `math.floor`, `math.ceil`, `math.trunc`, `round`, `divmod` of a `Rational` and reflected shifts
  (`3r << n`) returned plain `int`/`Fraction` instead of `Integer`/`Rational`.
- The ER2 Jupyter kernel reported version `0.0.1`.

## [0.4.2] — 2026-09-19

### Added
- The `oeis` module in the prelude: `oeis.sequence`, `search`, `identify`, `check` and
  `write_bfile`, built on [oeis-tools](https://github.com/oeistools/oeis-tools) (optional extra
  `er2[oeis]`).
- ER2 types (`Mod`, `Qfb`, `Factorization`, `OEISSequence`) format their own LaTeX, so it does not
  load SymPy.

## [0.4.1] — 2026-09-19

### Added
- Raw literals: `5r` is a plain Python `int` (a new row in the §1.1 table).
- A `Makefile` for the common tasks, and a CI job that runs the Jupyter, HTML and PDF tests.

### Changed
- SymPy loads only when a program needs it: a number theory program starts in 0.16 s, not 0.40 s.
- `factorial(n)` of an integer uses PARI's exact `n!`.
- The version has a single source, `pyproject.toml`.

### Fixed
- `f"{2^3=}"` printed the preparsed Python text; it now prints `2^3=8`.
- `er2 file.er2` did not put the file's directory on `sys.path`.

## [0.4.0] — 2026-09-19

### Added
- Automatic backend choice for `factor`: univariate polynomials over Q go to PARI (×1.2–14 faster
  from degree 9).
- PARI ↔ SymPy conversions for polynomials, rational functions, series, reals, complex numbers and
  matrices; `Mod` with polynomial moduli; `Qfb` binary quadratic forms.
- 26 PARI functions that take Python callables (`pari.sum(lambda n: 1/n^2, 1, 10)`).
- Benchmarks in [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

### Changed
- `Integer` arithmetic is 1.4–1.6× faster.

### Fixed
- `case 0:` patterns never matched, because the preparser wrapped their literals.
- Notebook tracebacks showed ER2's internal frames.

## [0.3.0] — 2026-09-19 (MVP)

### Added
- Number theory on PARI: `factor` of integers and rationals (with `limit=` for partial
  factorizations), `isprime`, `phi`, `sigma`, `mu`, `bigomega`, `dedekind_psi`, `Mod`, and the
  rest of the curated prelude.
- Every other PARI function as `pari.<name>`, from the table `er2/data/pari_functions.csv`.

## [0.2.0] — 2026-09-19

### Added
- The CAS on SymPy: `expand`, `factor`, `simplify`, `collect`, `cancel`, `diff`, `integrate`,
  `limit`, `solve`, `series`, and the constants and functions `pi`, `E`, `I`, `oo`, `sqrt`, `exp`,
  `log`, `sin`, `cos`, `tan`, `Eq`.

## [0.1.0] — 2026-09-18

### Added
- The preparser: `^` as power, `^^` as XOR, exact integer literals, `sym`.
- `Integer` and `Rational`, `latex()` and `show()`.
- The `er2` command (programs, `--show-python`, the REPL), `.er2` imports, the ER2 Jupyter
  kernel, `%load_ext er2`, and Quarto support.
