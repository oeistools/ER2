# ER2 performance roadmap

What "fast enough" means for ER2, how it is measured, and what is left. The figures come from
`benchmarks/run.py`; their history, run after run, is in [PERFORMANCE.md](PERFORMANCE.md).

## Goals, by subsystem

ER2 should be **faster than Python where it can be, and charge little over PARI/GP and SymPy
where it calls them**. Exactness and choosing the engine for the user have a price; the goal is
to keep that price small and measured, not to pretend it is zero.

| Subsystem | Target (ER2 / reference) | Reference | Benchmark section |
| --- | --- | --- | --- |
| Integer arithmetic | about 1.0 | the same code in Python | Integer arithmetic |
| Exact rationals | under 1.5 | `fractions.Fraction` | Exact rationals and large integers |
| Number theory on integers | under 2 | cypari2 on the same input | Number theory |
| Polynomials and matrices through PARI | under 3 at degree 20 / size 20 | cypari2 on PARI objects | Polynomials over F_p, Linear algebra |
| Symbolic calculus | about 1.0 | SymPy | Calculus and series |
| Startup without symbols | under 3 | `python -c pass` | Startup |

The reference for PARI rows is handed objects already in PARI, so it times the backend alone;
ER2's time includes converting a SymPy object both ways. The *Conversions* section times those
conversions on their own, against the computation they serve.

## How a change is accepted

1. `make bench-baseline` before, if there is no baseline for the machine yet.
2. The change, with tests showing the results are unchanged (the same answer as before, or as
   the reference library, on random input where possible).
3. `make bench-compare`: the rows the change aims at improve, and no other row gets more than
   about 10 % worse (smaller differences are usually noise).
4. `make bench-record NOTE="what changed"`, so the history shows the step.

Measure before explaining (ARCHITECTURE §1.5): profile the call, find where the time goes, and
change that. The end-to-end figure is the one to quote, never the backend's.

## Done (2026-11-25 and 26)

| Change | Effect |
| --- | --- |
| Rational `+ - * /` built directly | `a + b` from 2.8 to about 1.5 times `Fraction` |
| D22: integers are `int`, `/` and `**` exact | numeric loop from 13.9 to 1.0 times Python |
| `factor(f, modulus=p)`: one conversion per call, terms read directly | degree 12 mod 7 from 49 to 14 times cypari2 |
| Faster start (smaller prime table, lazy version and REPL modules) | 145 to 93 ms without symbols |
| D23: integer matrices to PARI as GP text; matrices back from text | `det` 10x10 from 8.4 to 6.4 times cypari2 |
| Polynomials to PARI read from their terms | degree-12 conversion from 221 to 84 us |

## Open, in order

1. **Matrix conversion, SymPy to PARI.** At size 10 it still costs about five times the
   determinant itself; most of it is SymPy's `Matrix` and reading its entries.
2. **Loading PARI only when used.** About 24 ms of the start (cypari2 and its initialisation),
   saved only by programs that call no PARI function; it needs a layer in `dispatch` and the
   prelude, so it waits until a measured program shows it matters.
3. **Startup with symbols.** About 400 ms is importing SymPy itself; ER2 already loads it only
   when a program uses symbols.
4. **Benchmarks in CI** (PLAN backlog 14), allowing for the noise of shared runners: report,
   never block a pull request on a timing.
