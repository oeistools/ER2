"""Benchmarks: ER2 against raw cypari2, SymPy and plain Python (M4).

Run ``uv run python benchmarks/run.py`` to print a Markdown report, or
``--write`` to save it as ``docs/BENCHMARKS.md``.  ``--quick`` runs every
benchmark once with small inputs (the test suite uses it).

Each row reports the median time per call and ER2's overhead, which is
``ER2 time / reference time``.
"""

import argparse
import importlib.metadata
import itertools
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cypari2
import sympy

from er2 import prelude
from er2.preparser import preparse
from er2.runtime.numbers import Integer

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "BENCHMARKS.md"


def measure(function, quick):
    """Return the median seconds per call of ``function``."""
    function()  # warm up (caches, lazy imports)
    if quick:
        return _timed(function, 1)
    # Calibrate the number of calls so each sample takes ~0.2 s.
    calls = 1
    while _timed(function, calls) * calls < 0.2 and calls < 10**6:
        calls *= 4
    return statistics.median(_timed(function, calls) for _ in range(5))


def _timed(function, calls):
    start = time.perf_counter()
    for _ in range(calls):
        function()
    return (time.perf_counter() - start) / calls


def er2_function(source, name):
    """Compile ER2 ``source`` and return the function ``name`` from it."""
    namespace = prelude.inject({"__name__": "bench"})
    exec(compile(preparse(source), "<bench>", "exec"), namespace)
    return namespace[name]


LOOP = """
def loop(n):
    s = 0
    i = 0
    while i < n:
        s = s + i * i % 7
        i = i + 1
    return s
"""


def python_loop(n):
    """Run the same loop as ``LOOP`` with plain ints."""
    s = 0
    i = 0
    while i < n:
        s = s + i * i % 7
        i = i + 1
    return s


def integer_rows(quick):
    """Rows for ``Integer`` arithmetic (the D2 risk)."""
    n = 1000 if quick else 20000
    loop = er2_function(LOOP, "loop")
    a, b = Integer(12345), Integer(678)
    return [
        (
            f"numeric loop, {n} iterations (ER2 literals)",
            measure(lambda: loop(n), quick),
            "Python `int`",
            measure(lambda: python_loop(n), quick),
        ),
        (
            "`a + b`",
            measure(lambda: a + b, quick),
            "`int` `a + b`",
            measure(lambda: 12345 + 678, quick),
        ),
    ]


def number_theory_rows(quick):
    """Rows for number theory: ER2 prelude against cypari2 and SymPy.

    Each call gets a different argument, because SymPy caches results
    (``@cacheit``) and a repeated argument would measure the cache.
    """
    pari = cypari2.Pari()
    ns = prelude.namespace()
    count = 10 if quick else 5000
    near = [Integer(123456789 + i) for i in range(count)]
    mersenne = [Integer(2) ** 127 - 1] * count  # PARI and SymPy do not cache
    primes = [Integer(2) ** 89 - 1, Integer(2) ** 107 - 1, *mersenne[:1]]
    semiprimes = [
        Integer(1000000007 + 2 * i) * Integer(998244353) for i in range(count)
    ]
    cases = [
        ("phi(n), n ≈ 1.2e8", ns["phi"], near, pari.eulerphi, sympy.totient),
        (
            "sigma(n), n ≈ 1.2e8",
            ns["sigma"],
            near,
            pari.sigma,
            sympy.divisor_sigma,
        ),
        (
            "isprime(2^127 - 1), proven",
            ns["isprime"],
            mersenne,
            pari.isprime,
            None,
        ),
        (
            "ispseudoprime (BPSW), Mersenne primes",
            ns["ispseudoprime"],
            primes,
            pari.ispseudoprime,
            sympy.isprime,
        ),
        (
            "factor(n), n ≈ 1e18 semiprime",
            ns["factor"],
            semiprimes,
            pari.factor,
            sympy.factorint,
        ),
    ]
    rows = []
    for label, er2_call, args, pari_call, sympy_call in cases:
        er2_time = measure(_cycling(er2_call, args), quick)
        plain = [int(a) for a in args]
        references = [("cypari2", pari_call), ("SymPy", sympy_call)]
        for name, call in references:
            if call is not None:
                reference = measure(_cycling(call, plain), quick)
                rows.append((label, er2_time, name, reference))
    return rows


def _cycling(function, args):
    """Return a call of ``function`` on the next argument of ``args``."""
    arguments = itertools.cycle(args)
    return lambda: function(next(arguments))


def polynomial_rows(quick):
    """Rows for ``factor`` of univariate polynomials: PARI against SymPy."""
    x = sympy.Symbol("x")
    factor = prelude.namespace()["factor"]
    rows = []
    for k in (1, 2) if quick else (1, 2, 4, 8):
        p = sympy.expand(
            sympy.prod([x**j - j for j in range(1, k + 1)])
            * (x ** (3 * k) - 1)
        )
        degree = int(sympy.degree(p, x))
        rows.append(
            (
                f"factor, degree {degree}",
                measure(lambda: factor(p), quick),
                "SymPy `factor`",
                measure(lambda: sympy.factor(p), quick),
            )
        )
    return rows


def startup_rows(quick):
    """Rows for the time to run a tiny program, against plain Python.

    SymPy is imported only by programs that use it (``er2._lazy``).
    """
    runs = 1 if quick else 7
    programs = {
        "number theory only": "print(phi(10^6), factor(360))\n",
        "with symbols (loads SymPy)": "sym x\nprint(factor(x^2 - 1))\n",
    }
    python = _process_time([sys.executable, "-c", "print(1)"], runs)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for label, source in programs.items():
            path = Path(tmp) / "program.er2"
            path.write_text(source, encoding="utf-8")
            command = [sys.executable, "-m", "er2", str(path)]
            er2_time = _process_time(command, runs)
            rows.append(
                (f"`er2` startup, {label}", er2_time, "Python", python)
            )
    return rows


def _process_time(command, runs):
    """Return the median wall time of running ``command``."""
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run(command, check=True, capture_output=True)
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def format_time(seconds):
    """Return ``seconds`` with a readable unit."""
    for unit, scale in (("s", 1), ("ms", 1e-3), ("µs", 1e-6)):
        if seconds >= scale:
            return f"{seconds / scale:.3g} {unit}"
    return f"{seconds / 1e-9:.3g} ns"


def table(title, rows):
    """Return a Markdown section with one row per comparison."""
    lines = [
        f"## {title}",
        "",
        "| Benchmark | ER2 | Reference | Reference time | ER2 / reference |",
        "|---|---|---|---|---|",
    ]
    for label, er2_time, reference, reference_time in rows:
        ratio = er2_time / reference_time
        lines.append(
            f"| {label} | {format_time(er2_time)} | {reference} "
            f"| {format_time(reference_time)} | ×{ratio:.2f} |"
        )
    return "\n".join(lines)


def report(quick=False):
    """Run every benchmark and return the Markdown report."""
    sections = [
        table("Startup", startup_rows(quick)),
        table("Integer arithmetic (D2)", integer_rows(quick)),
        table("Number theory", number_theory_rows(quick)),
        table("Polynomial factorization", polynomial_rows(quick)),
    ]
    header = [
        "# ER2 benchmarks",
        "",
        # Each entry is one long line of the generated Markdown, built
        # with an explicit ``+`` because it does not fit in the 79 columns
        # PEP 8 allows in this source (§6.1).
        "Generated by `uv run python benchmarks/run.py --write`; do not "
        + "edit by hand.",
        "",
        f"Python {platform.python_version()}, SymPy {sympy.__version__}, "
        + f"cypari2 {importlib.metadata.version('cypari2')}, "
        + f"{platform.machine()}.  Times are "
        + "medians per call; ×1.00 means ER2 is as fast as the reference.",
        "",
        "Notes: `isprime` proves primality (PARI's APRCL); `sympy.isprime` "
        + "and `ispseudoprime` run the BPSW probable-prime test, so they are "
        + "compared with each other.  Number theory calls get a different "
        + "argument each time, because SymPy caches results.",
    ]
    return "\n\n".join(["\n".join(header), *sections]) + "\n"


def main(argv=None):
    """Print the report, or write it to ``docs/BENCHMARKS.md``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    text = report(quick=args.quick)
    if args.write:
        REPORT.write_text(text, encoding="utf-8")
        print(f"wrote {REPORT.relative_to(ROOT)}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
