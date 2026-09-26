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
| **1.0** | The language is stable (PLAN.md, M8): the syntax and the public API freeze, and change afterwards only through the deprecation policy. The normative specification is [docs/LANGUAGE.md](docs/LANGUAGE.md), shipped in 0.7. |

What is stable already, and what is not:

- **Stable:** the ER2 syntax in the §3 table of [docs/LANGUAGE.md](docs/LANGUAGE.md) (`^`, `^^`,
  exact integer literals, `sym`, `5r`). Any change to it requires updating that table and a
  changelog entry.
  Python compatibility (all Python syntax, any library through `import`) is a hard requirement.
- **Stable in intent, may still change before 1.0:** the curated prelude (`factor`, `phi`,
  `isprime`, `Mod`, …), `latex()` and `show()`, and the `er2` command.
- **Experimental:** `pari.<name>` (it follows PARI's own API and the PARI table), the `oeis`
  module, and the printed form of results (`repr`, LaTeX), which may improve between releases.

## [Unreleased]

### Added
- **macOS is supported**, on Apple Silicon: CI now runs the whole test suite on macOS as well as
  Linux, for Python 3.12–3.14, and the package declares `Operating System :: MacOS`. Intel Macs
  are experimental until CI's first run on them passes.
- **Releases through a trusted publisher (M8).** Pushing a tag `vX.Y.Z` starts
  `.github/workflows/release.yml`. It checks the tag against the version and that the commit
  is on `main`, runs the suite, builds, and runs the built wheel in a clean environment. It then
  waits for a maintainer to approve the upload to PyPI. No token is stored anywhere: PyPI trusts
  that workflow in that environment and nothing else. The manual route in
  [docs/RELEASING.md](docs/RELEASING.md) remains as the fallback, and `tests/test_release.py`
  checks that only the approved job can publish.

### Fixed
- The README's logo and five of its badges used relative paths, which are dead on the PyPI
  project page, since the README is the PyPI description. They are now absolute, and
  `tests/test_release.py` fails if a relative link comes back.
- `examples/er2.xml` was not well-formed XML: its header comment contained `--`, which XML
  forbids. Pandoc accepted it, so highlighting worked, but a strict XML parser rejected it,
  and so did any tool that read the file other than Pandoc. `tests/test_site.py` now parses it.
- The package declared `Operating System :: OS Independent`, but cypari2 has no Windows build,
  so ER2 cannot be installed on Windows (WSL works). The classifiers now declare Linux and
  macOS, the two platforms CI tests, and the README's Quick start has a platform table.

## [0.7.0] — 2026-09-21

The first release prepared for PyPI, and the one that makes ER2 a *specified* language rather
than an implemented one. It carries the whole of M5 (algebra), M6 (series) and M7 (the language
specification), which had accumulated unreleased since 0.4.2.

### Added
- **Packaging for PyPI (M8).** `pip install er2`, with `er2[jupyter]` and `er2[oeis]`. Keywords,
  classifiers and `Documentation`/`Changelog` URLs; the README's links are absolute, because the
  README is the PyPI description and PyPI does not resolve relative paths. The upload itself is
  run by the maintainer, following [docs/RELEASING.md](docs/RELEASING.md) — nothing in the
  repository publishes anything.
- **A stability and deprecation policy, [docs/STABILITY.md](docs/STABILITY.md) (M8).** What is
  stable — the language, the number model, the prelude names, the predefined symbols, the `er2`
  command, `.er2` imports — and what is deliberately not: `pari.<name>`, `er2.oeis`, printed
  forms, backend routing, everything private, performance. Deprecation is concrete: announce,
  warn, wait two minor releases and six months, remove only in a major. A mathematically wrong
  answer is the one exception: that is a bug, not an API. `tests/test_stability.py` pins the
  public surface, so a name cannot appear or vanish unnoticed.
- **A documentation site, [`site/`](site/) (M8)**, Quarto to GitHub Pages. Its prose pages
  *include* `docs/*.md` instead of copying them, so the site cannot drift from the repository,
  and its home page **executes ER2 on the er2 kernel while it renders** — the site that documents
  ER2 is built by ER2. `site/doc-links.lua` rewrites the included documents' relative links so
  they work both on GitHub and on the site, and `tests/test_site.py` fails if a new link is left
  unmapped. Published by `.github/workflows/pages.yml`.
- **The language specification, [docs/LANGUAGE.md](docs/LANGUAGE.md) (M7, 0.7).** One normative
  document defines ER2: what is preparsed, the two-pass translation and its error and
  line-number rules, the exhaustive table of differences from Python, precedence and
  associativity, the `Integer`/`Rational` model and where conversion stops, symbols and the
  prelude, dispatch, the three conversion boundaries, printing and LaTeX, notebooks, and what is
  stable before 1.0. Every rule carries an identifier, and Appendix B maps each one to the test
  that would fail if it changed. `tests/test_language_spec.py` pins the rules that had no test
  of their own — precedence, symbol semantics, the conversion boundary — and fails if the table
  of differences grows or if a cited test disappears.
- **Scientific interoperability, tested across the stack (M7, 0.7).**
  `tests/compat/test_scientific.py` now covers all four libraries the README names — NumPy,
  Matplotlib, pandas and SciPy — in 16 tests. `Integer` subclasses `int`, so every library gives
  it a real integer dtype. `Rational` is not a machine number, and the stack splits on it: NumPy
  and pandas keep it in an object array, pandas keeping the arithmetic exact (`1/2 + 1/3` sums to
  `5/6`), while SciPy's ufuncs reject it with `TypeError`, having no object fallback. The escape
  hatch stays explicit, `float(...)`. pandas and SciPy joined the dev group for this; neither is
  a runtime dependency.
- **Quarto documents show their cells as ER2 (0.6.1)**, with real ER2 syntax highlighting:
  `examples/er2.xml` is a KDE syntax definition that states the LANGUAGE.md §3 table — `sym`, `5r`
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
  §1.4, *learnable in an afternoon by a Python programmer*, makes the LANGUAGE.md §3 table the whole of
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
- The Matplotlib guard in `tests/compat/test_scientific.py` was a module-level `importorskip` in
  the *middle* of the file, which aborts the import and takes every test with it: with Matplotlib
  absent the file collected **zero** tests, including the six that only need NumPy. Each library
  now has its own fixture, verified by blocking each of the three in turn.
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
