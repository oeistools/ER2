# Stability and deprecation policy

**What a user may rely on, and what may still move.**

This policy governs ER2's public API. It is in force for the 0.x releases as a statement of
intent, and becomes binding at **1.0**, when the syntax and the public API freeze.

The language itself is specified separately and normatively in
[LANGUAGE.md](LANGUAGE.md). This document covers the *library*: which names exist, what they
promise, and how they may change.

## 1. Versioning

ER2 follows [Semantic Versioning](https://semver.org/).

| Release | What it may contain |
|---|---|
| **major** (1.0 → 2.0) | a change to the public API, after the deprecation process of §4 |
| **minor** (1.0 → 1.1) | new names, new capabilities, new backends; nothing that breaks working code |
| **patch** (1.0 → 1.0.1) | fixes only |

Before 1.0 a minor release may still change the public API, and each such change is listed in
[CHANGELOG.md](../CHANGELOG.md) under **Changed** or **Removed**.

## 2. What is stable

**S1. The language.** Every rule of [LANGUAGE.md](LANGUAGE.md) except §12, which is this policy
restated. In particular the §3 table of differences from Python is exhaustive and frozen: `^`,
`^^`, their assignment forms, exact `/` and `**` on integers (D22), `sym`, and the ER2 text
echoed by `f"{a^2=}"`. The raw literal `5r` is **not** frozen: it is deprecated (LANGUAGE.md
§3.4 R4) and 1.0 removes it.

**S2. The number model.** Integers are Python's `int` (D22) and `Integer`, still available,
subclasses it; `Rational` subclasses `fractions.Fraction`; exact `/` and `**` (LANGUAGE.md
§3.7); the closure and boundary rules of LANGUAGE.md §5.

**S3. The prelude names**, listed in `tests/test_stability.py` and pinned there. They fall into
four groups:

- the mathematical functions (`factor`, `isprime`, `phi`, `det`, `expand`, …);
- the mathematical types (`Rational`, `Mod`, `GF`, `NumberField`, `Factorization`, `Qfb`,
  `DirichletSeries`, `Matrix`). `Integer` is deprecated in the prelude (LANGUAGE.md §5.1 R5):
  1.0 removes it from there, and it stays importable (`from er2 import Integer`);
- output (`latex`, `show`);
- the SymPy constants and elementary functions re-exported as they are (`pi`, `E`, `I`, `oo`,
  `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`, `Eq`), and `symbols`.

**S4. The predefined symbols** `_x`, `_y`, `_z`, `_n`, `_k`, `_p` (LANGUAGE.md §6.2 R3). They are
ordinary bindings and may be shadowed.

**S5. A stable function's contract**: the meaning of its result, its type, and the arguments it
accepts. A function may gain optional keyword arguments in a minor release; it may not change
what it returns for arguments that already worked.

**S6. The `er2` command**: `er2 file.er2`, `er2 --show-python`, the REPL, and
`er2 kernel install`.

**S7. `.er2` files are importable** with a plain `import`, and a `.py` module of the same name
wins (LANGUAGE.md §11.1 R2).

**S8. The Python API** (decided 2026-11-27): what Python code may import and rely on is the
top-level `er2` package (`er2.__all__`: `preparse`, `latex`, `show`, `Integer`, `Rational`, and
`%load_ext er2`) and the classes of `er2.runtime` (`Mod`, `Factorization`, `GF` and its
elements, `NumberField`, `PrimeIdeal`, `Qfb`, `DirichletSeries`). Their type hints
(`py.typed`) are part of it. Everything else that is importable is N5.

## 3. What is not stable

These may change in any release, and code that depends on them should expect to be updated.

**N1. `pari.<name>`.** It follows PARI's own API and PARI's own names, so it moves when PARI
does. The curated prelude (S3) is the stable route; `pari.` is the escape hatch.

**N2. `er2.oeis`.** It depends on an external service and on `oeis-tools`.

**N3. The printed form of results** — `repr`, `str` and LaTeX. The *notation* is stable (powers
print as `x^2`, LANGUAGE.md §9 R1); the exact spacing, ordering and parenthesisation are not.
Do not assert on them outside ER2's own tests.

**N4. Backend routing.** Which of PARI and SymPy computes a given call is deliberately
unobservable (LANGUAGE.md §7 R2), so it is free to change for speed. The one recorded exception
is D21.

**N5. Everything private.** Any module, class, function or attribute whose name begins with `_`,
plus `er2.dispatch`, `er2.preparser`, `er2.backends`, `er2.prelude`, `er2.session`,
`er2.importer` and `er2._lazy` as *modules*. Their contents are implementation. The names they
export into a program's namespace (S3) are what is stable, not the modules themselves.

**N6. Performance.** The benchmarks in [BENCHMARKS.md](BENCHMARKS.md) record what is true today,
not a promise.

## 4. Deprecation

From 1.0, a stable name is removed only like this:

1. **Announce.** The release that deprecates it says so in `CHANGELOG.md` under **Deprecated**,
   names the replacement, and explains how to migrate.
2. **Warn.** Using it raises `FutureWarning` with the replacement in the message. The name
   keeps working unchanged. Not `DeprecationWarning`: Python hides that one outside
   `__main__`, and the warning is for the person who wrote the program.
3. **Wait.** At least **two minor releases**, and at least **six months**, whichever is longer.
4. **Remove.** Only in a major release, listed under **Removed**.

A name is never repurposed: once removed, it is not reused for something else.

**Exception.** A security fix, or a result that is mathematically *wrong*, may be corrected in
any release without this process. A wrong answer is a bug, not an API. Such a change is listed
under **Fixed** and says plainly what the old behaviour was.

## 5. How this is enforced

`tests/test_stability.py` pins the public surface: the exact set of prelude names, the predefined
symbols and `er2.__all__`. Adding or removing a public name fails the suite until the list is
updated deliberately — which is the point, because the list is the policy's subject.

The language half is enforced the same way by `tests/test_language_spec.py`, whose `COVERAGE`
table maps every rule of LANGUAGE.md to the test that would fail if it changed.
