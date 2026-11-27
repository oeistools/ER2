# ER2 compared with Python, SymPy, SageMath and PARI/GP

A technical comparison: what each system is for, what ER2 takes from it, and where ER2 stops.
The figures come from `benchmarks/run.py` ([BENCHMARKS.md](BENCHMARKS.md)), measured on one
machine; ratios are ER2's time divided by the other system's.

## What ER2 gives over each

- **Over Python alone:** exact mathematics without asking for it (`1/3` is one third,
  `2^-1` is `1/2`), mathematical notation in and out (`x^2`, `sym x`; results print as
  `x^2 + 1` and `2^3 * 3^2 * 5`), and number theory, algebra and calculus without an import.
  Integer code keeps Python's speed (×1.0).
- **Over SymPy:** the same SymPy underneath, with `x^2` instead of `x**2` and `sym x` instead of
  `symbols("x")`, and PARI chosen automatically where it is faster, with the answer SymPy would
  give: a degree-60 polynomial factors in a twenty-fifth of SymPy's time, a 10x10 integer
  determinant in a hundredth.
- **Over PARI/GP:** Python instead of GP, so every Python library (NumPy, pandas, Matplotlib)
  and Jupyter work, and PARI and symbolic algebra in the same program. On integers the cost
  over calling PARI directly is small (`isprime` ×1.0, `factor` ×1.1).
- **Over SageMath:** `pip install er2`, with PARI inside the cypari2 wheel; a language whose
  difference from Python is one table, learnt in an afternoon; and a program without PARI or
  symbols starts in about 60 ms.
- **Only in ER2:** Python, SymPy and PARI as one language, with the engine chosen for each call;
  and documents (Quarto, Jupyter) written in ER2, where every result has a LaTeX form.

Where it does not win: GP alone is faster on matrices and polynomials (×2 to ×14 here, the price
of converting); SageMath covers far more mathematics (groups, algebraic geometry,
combinatorics); and ER2 adds no algorithms of its own.

## In one table

| | Python | SymPy | SageMath | PARI/GP | ER2 |
| --- | --- | --- | --- | --- | --- |
| What it is | a general language | a CAS, as a Python library | a distribution of many mathematical systems behind a Python language | a C library for number theory, and the GP language | Python with mathematical syntax, on SymPy and PARI |
| Language | Python | Python | Python, preparsed | GP | Python, preparsed (`.er2` files only) |
| `1/3` | `0.333…` | `Rational(1, 3)` if asked | `1/3` | `1/3` | `1/3` |
| `2^10` | `8` (XOR) | `8` (XOR) | `1024` | `1024` | `1024` |
| Symbols | — | `symbols("x")` | `var("x")` | any unbound name | `sym x` |
| Installs with | — | `pip` | its own distribution | a system package or source | `pip install er2` (PARI comes in the cypari2 wheel) |
| Own algorithms | — | all of its own | its own and those of the systems it bundles | all of its own | none: SymPy's and PARI's |

## Python

Python is the base: every Python program is an ER2 program, and an `.er2` file can import any
Python library. Inside `.er2` files only the differences in [LANGUAGE.md](LANGUAGE.md) §3 apply
(`^`, `^^`, exact `/` and `**`, `sym`, `5r`, the text echoed by `f"{a^2=}"`); `.py` files are
never changed.

Speed: integer code runs at Python's speed (the numeric loop is ×1.00, D22), because ER2 integers
are Python `int`s. Exact rationals cost about what `fractions.Fraction` costs (`a + b` ×1.2,
`a * b / (a - b)` ×1.1). An ER2 program that uses neither PARI nor SymPy starts in about 60 ms,
roughly three times `python -c pass`.

## SymPy

SymPy does all of ER2's symbolic work: algebra, calculus, simplification, Gröbner bases and
symbolic matrices. ER2 adds the syntax (`x^2`, `sym x`), prints results as mathematics
(`x^2 + 1`, not `x**2 + 1`) and sends to PARI the cases PARI does faster, with the same answer
SymPy would give (a test compares the two on random input).

Speed: where ER2 only calls SymPy it costs what SymPy costs (calculus rows ×0.8–1.0). Where it
routes to PARI it is faster: factoring a polynomial of degree 60 over Q takes about a twenty-fifth
of SymPy's time (×0.04), and a 10x10 integer determinant about a hundredth (×0.01). A program
that uses symbols pays SymPy's import, about 0.4 s; the REPL and the Jupyter kernel start it in
the background.

Where ER2 stops: anything SymPy cannot do, ER2 cannot do either, and `import sympy` gives the
rest of SymPy unchanged.

## SageMath

SageMath is ER2's model (ARCHITECTURE §1.1): its preparser introduced `^` as power, `^^` as XOR,
exact integer literals and the `5r` raw literal, and ER2 follows those conventions. SageMath is
far larger: it bundles PARI, GAP, Maxima, FLINT, Singular and many other systems, has its own
types for rings, fields, groups and much more, and covers areas ER2 does not touch (group theory,
algebraic geometry, combinatorics, coding theory, elliptic curves beyond what PARI exposes).

ER2 is the small end of that idea: two backends, a `pip` install, and a language whose whole
difference from Python is one table, so that a Python programmer can learn it in an afternoon
(ARCHITECTURE §1.4). If a problem needs what only SageMath bundles, SageMath is the tool.

## PARI/GP

PARI is ER2's number-theory engine, called through cypari2: `factor`, `isprime`, `phi`, number
fields, finite fields, power series, integer matrices and polynomials over F_p. GP, PARI's own
language, is not involved, and ER2 users never receive raw PARI objects: results come back as
ER2 numbers and SymPy objects.

Speed: every call converts its arguments to PARI and the result back, which is the price of
mixing PARI with Python and SymPy objects. On integers the price is small (`isprime` ×1.0,
`factor(n)` ×1.1, `phi` ×1.8 against cypari2 itself); on matrices and polynomials it is larger
(×2–3 at size 20 or degree 48, up to ×14 for small polynomials over F_p), because a SymPy matrix
or polynomial has to be read and rebuilt. Code written directly in GP avoids all of it; ER2 is
for programs that need PARI's algorithms and Python's ecosystem in the same file.

Where ER2 stops: about a thousand PARI functions are reachable as `pari.<name>`
([PARI_FUNCTIONS.md](PARI_FUNCTIONS.md)), and `pari.raw` gives cypari2 itself, but only the
types ER2 converts (integers, rationals, reals, complex numbers, `Mod`, polynomials and
rational functions, series, vectors and matrices, finite field elements, quadratic forms) come back as ER2 values.

## What ER2 does not do

- **New algorithms.** ER2 has none of its own: it chooses between SymPy and PARI and converts.
- **Numerical computing.** Floats behave as in Python; for arrays and numerical methods, import
  NumPy and SciPy (ER2 values work with them, LANGUAGE.md §5.4).
- **Windows**, natively: cypari2 has no Windows build yet (WSL works).
- **A frozen language.** ER2 is 0.x: the syntax and the public API are fixed only at 1.0
  ([STABILITY.md](STABILITY.md)).
