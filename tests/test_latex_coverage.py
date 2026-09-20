r"""Every ER2 type and every prelude result has real LaTeX (§3.6).

``latex()`` falls back to ``\texttt{repr}`` for unknown objects.  These
tests fail when a public runtime type, a prelude value or the result of
a public function would print that way, so a new type or function
cannot be added without LaTeX support.
"""

import importlib
import inspect
import pkgutil

import pytest
import sympy

import er2.runtime
from er2 import prelude
from er2.printing import latex
from er2.runtime.factorization import Factorization
from er2.runtime.finite_field import GF, FiniteField, FiniteFieldElement
from er2.runtime.modular import Mod
from er2.runtime.numbers import Integer, Rational
from er2.runtime.qfb import Qfb

x, y = sympy.symbols("x y")
f = x**2 + 2 * x + 1

# One instance of every public class in ``er2.runtime``.
TYPE_SAMPLES = {
    Integer: Integer(5),
    Rational: Rational(1, 3),
    Mod: Mod(3, 7),
    Factorization: Factorization([(2, 3), (3, 2)]),
    Qfb: Qfb(1, 1, 6),
    FiniteField: GF(9),
    # a^2 + 1 in GF(9) = a^2 + a + 2: prints reduced, as 2*a + 2.
    FiniteFieldElement: GF(9).gen() ** 2 + 1,
}

# Prelude values that are not mathematical objects.
NOT_MATHEMATICAL = {"pari", "oeis"}

n = Integer


def _m(ns):
    return ns["Matrix"]([[2, 1], [1, 3]])


def _c(ns):
    return ns["Matrix"]([[1, 2], [2, 4]])


# A call of every public function in the prelude, with its golden LaTeX.
FUNCTION_SAMPLES = {
    "expand": (lambda ns: ns["expand"]((x + 1) ** 2), "x^{2} + 2 x + 1"),
    "factor": (lambda ns: ns["factor"](f), r"\left(x + 1\right)^{2}"),
    "simplify": (
        lambda ns: ns["simplify"](ns["sin"](x) ** 2 + ns["cos"](x) ** 2),
        "1",
    ),
    "collect": (
        lambda ns: ns["collect"](x * y + x + x**2, x),
        r"x^{2} + x \left(y + 1\right)",
    ),
    "cancel": (lambda ns: ns["cancel"]((x**2 - 1) / (x - 1)), "x + 1"),
    "diff": (lambda ns: ns["diff"](x**3, x), "3 x^{2}"),
    "integrate": (
        lambda ns: ns["integrate"](f, (x, Integer(0), Integer(1))),
        r"\frac{7}{3}",
    ),
    "limit": (lambda ns: ns["limit"](1 / x, x, 0, dir="-"), r"-\infty"),
    "solve": (
        lambda ns: ns["solve"](x**2 - 2, x),
        r"\left[ - \sqrt{2},\ \sqrt{2}\right]",
    ),
    "series": (
        lambda ns: ns["series"](ns["sin"](x), x, 0, 4),
        r"x - \frac{x^{3}}{6} + O\left(x^{4}\right)",
    ),
    # Linear algebra (M5): M = [2, 1; 1, 3] (regular), C = [1, 2; 2, 4].
    "charpoly": (lambda ns: ns["charpoly"](_m(ns)), "x^{2} - 5 x + 5"),
    "det": (lambda ns: ns["det"](_m(ns)), "5"),
    "echelon_form": (
        lambda ns: ns["echelon_form"](_c(ns)),
        r"\left[\begin{matrix}1 & 2\\0 & 0\end{matrix}\right]",
    ),
    "hermite_form": (
        lambda ns: ns["hermite_form"](_m(ns)),
        r"\left[\begin{matrix}5 & 2\\0 & 1\end{matrix}\right]",
    ),
    "inverse": (
        lambda ns: ns["inverse"](_m(ns)),
        r"\left[\begin{matrix}\frac{3}{5} & - \frac{1}{5}\\"
        r"- \frac{1}{5} & \frac{2}{5}\end{matrix}\right]",
    ),
    "kernel": (
        lambda ns: ns["kernel"](_c(ns)),
        r"\left[ \left[\begin{matrix}1\\- \frac{1}{2}\end{matrix}\right]"
        r"\right]",
    ),
    "minpoly": (lambda ns: ns["minpoly"](_m(ns)), "x^{2} - 5 x + 5"),
    # Gröbner bases (M5): SymPy's own LaTeX for its ``GroebnerBasis``.
    "groebner": (
        lambda ns: ns["groebner"]([x**2 + y**2 - 1, x - y], x, y),
        r"\operatorname{GroebnerBasis}\left(\left( x - y, \  2 y^{2} - "
        r"1\right), \left( x, \  y\right)\right)",
    ),
    "reduce": (
        lambda ns: ns["reduce"](
            x**2 + y**2, ns["groebner"]([x**2 + y**2 - 1, x - y], x, y)
        ),
        "1",
    ),
    # Resultants (M5); values checked against cypari2.
    "resultant": (
        lambda ns: ns["resultant"](x**2 + 1, x**3 - 2, x),
        "5",
    ),
    "discriminant": (
        lambda ns: ns["discriminant"](x**3 + x + 1, x),
        "-31",
    ),
    "rank": (lambda ns: ns["rank"](_c(ns)), "1"),
    "smith_form": (
        lambda ns: ns["smith_form"](_m(ns)),
        r"\left[\begin{matrix}1 & 0\\0 & 5\end{matrix}\right]",
    ),
    # Number theory (PARI); values checked against cypari2.
    "bigomega": (lambda ns: ns["bigomega"](n(360)), "6"),
    "binomial": (lambda ns: ns["binomial"](n(10), n(3)), "120"),
    "chinese": (
        lambda ns: ns["chinese"](Mod(1, 3), Mod(2, 5)),
        r"7 \pmod{15}",
    ),
    "core": (lambda ns: ns["core"](n(360)), "10"),
    "dedekind_psi": (lambda ns: ns["dedekind_psi"](n(12)), "24"),
    "divisors": (
        lambda ns: ns["divisors"](n(12)),
        r"\left[ 1,\ 2,\ 3,\ 4,\ 6,\ 12\right]",
    ),
    "factorial": (
        lambda ns: ns["factorial"](n(20)),
        "2432902008176640000",
    ),
    "fibonacci": (lambda ns: ns["fibonacci"](n(50)), "12586269025"),
    "gcd": (lambda ns: ns["gcd"](n(12), n(18)), "6"),
    "ispower": (lambda ns: ns["ispower"](n(8)), "3"),
    "isirreducible": (
        lambda ns: ns["isirreducible"](x**2 + x + 1, modulus=n(2)),
        r"\text{True}",
    ),
    "isprime": (
        lambda ns: ns["isprime"](n(2) ** 127 - 1),
        r"\text{True}",
    ),
    "isprimepower": (lambda ns: ns["isprimepower"](n(9)), "2"),
    "ispseudoprime": (
        lambda ns: ns["ispseudoprime"](n(91)),
        r"\text{False}",
    ),
    "issquare": (lambda ns: ns["issquare"](n(10)), r"\text{False}"),
    "issquarefree": (
        lambda ns: ns["issquarefree"](n(30)),
        r"\text{True}",
    ),
    "jordan_totient": (lambda ns: ns["jordan_totient"](n(12), n(2)), "96"),
    "kronecker": (lambda ns: ns["kronecker"](n(2), n(7)), "1"),
    "lcm": (lambda ns: ns["lcm"](n(4), n(6)), "12"),
    "radical": (lambda ns: ns["radical"](n(360)), "30"),
    "mu": (lambda ns: ns["mu"](n(30)), "-1"),
    "nextprime": (lambda ns: ns["nextprime"](n(100)), "101"),
    "numdiv": (lambda ns: ns["numdiv"](n(360)), "24"),
    "omega": (lambda ns: ns["omega"](n(360)), "3"),
    "phi": (lambda ns: ns["phi"](n(123456789)), "82260072"),
    "precprime": (lambda ns: ns["precprime"](n(100)), "97"),
    "prime": (lambda ns: ns["prime"](n(100)), "541"),
    "primepi": (lambda ns: ns["primepi"](n(1000)), "168"),
    "primes": (
        lambda ns: ns["primes"](n(5)),
        r"\left[ 2,\ 3,\ 5,\ 7,\ 11\right]",
    ),
    "sigma": (lambda ns: ns["sigma"](n(123456789)), "178422816"),
    "sqrtint": (lambda ns: ns["sqrtint"](n(99)), "9"),
    "valuation": (lambda ns: ns["valuation"](n(48), n(2)), "4"),
    "znlog": (lambda ns: ns["znlog"](n(3), Mod(5, 7)), "5"),
    "znorder": (lambda ns: ns["znorder"](Mod(2, 7)), "3"),
    "znprimroot": (lambda ns: ns["znprimroot"](n(7)), r"3 \pmod{7}"),
}
# ``factor`` of a number is a Factorization; of an expression, SymPy's.
FACTOR_OF_NUMBERS = [
    (n(-360), r"-1 \cdot 2^{3} \cdot 3^{2} \cdot 5"),
    (Rational(1, 12), r"2^{-2} \cdot 3^{-1}"),
    (n(1), "1"),
]


def runtime_classes():
    """Yield the public classes defined in the ``er2.runtime`` modules."""
    for info in pkgutil.iter_modules(er2.runtime.__path__):
        module = importlib.import_module(f"er2.runtime.{info.name}")
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and obj.__module__ == module.__name__
                and not name.startswith("_")
            ):
                yield obj


def assert_real_latex(obj):
    body = latex(obj)
    assert r"\texttt" not in body, (obj, body)
    return body


def test_every_runtime_type_has_a_sample():
    assert set(runtime_classes()) == set(TYPE_SAMPLES)


@pytest.mark.parametrize("kind", list(TYPE_SAMPLES), ids=lambda t: t.__name__)
def test_runtime_types_have_latex(kind):
    sample = TYPE_SAMPLES[kind]
    assert type(sample) is kind
    body = assert_real_latex(sample)
    assert sample._repr_latex_() == f"${body}$"


def test_every_prelude_function_has_a_sample():
    assert set(FUNCTION_SAMPLES) == set(prelude.FUNCTIONS)


@pytest.mark.parametrize("name", sorted(FUNCTION_SAMPLES))
def test_prelude_function_results_have_golden_latex(name):
    call, expected = FUNCTION_SAMPLES[name]
    assert assert_real_latex(call(prelude.namespace())) == expected


@pytest.mark.parametrize(("number", "tex"), FACTOR_OF_NUMBERS)
def test_factorizations_have_golden_latex(number, tex):
    assert assert_real_latex(prelude.namespace()["factor"](number)) == tex


def test_prelude_values_have_latex():
    for name, value in prelude.namespace().items():
        if name in NOT_MATHEMATICAL:
            continue
        is_function = callable(value) and not isinstance(value, sympy.Basic)
        if name.startswith("__") or is_function:
            continue
        assert_real_latex(value)
