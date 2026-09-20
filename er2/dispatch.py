"""Public mathematical functions and their backends (ARCHITECTURE.md §3.4).

This is the only place that knows which backend computes what.  Each
entry of ``TABLE`` is a list of ``(predicate, implementation)`` pairs; a
public function calls the first implementation whose predicate accepts
its positional arguments.

``FUNCTIONS`` maps every public name to its function; the prelude
exposes them all.
"""

import sys
from fractions import Fraction

from er2 import _lazy
from er2.backends import pari_backend
from er2.runtime.finite_field import FiniteField, FiniteFieldElement
from er2.runtime.modular import Mod

__all__ = ["FUNCTIONS", "TABLE", "implementation"]


class _SympyBackend:
    """A SymPy backend function, imported on first use (``er2._lazy``)."""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def resolve(self):
        from er2.backends import sympy_backend

        return getattr(sympy_backend, self.name)


def symbolic(args, kwargs):
    """Whether an argument is a symbolic (non-numeric) SymPy object."""
    return any(_lazy.is_symbolic(arg) for arg in args)


def number(args, kwargs):
    """Whether the first argument is an exact number."""
    if not args:
        return False
    if isinstance(args[0], (int, Fraction)):
        return True
    return _lazy.sympy_loaded() and isinstance(
        args[0], sys.modules["sympy"].Rational
    )


def anything(args, kwargs):
    """Accept any arguments."""
    return True


def rational_univariate(args, kwargs):
    """Whether ``args`` is one univariate polynomial over Q, no options.

    PARI factors these 2-25x faster than SymPy (docs/BENCHMARKS.md);
    options such as ``extension=`` or ``modulus=`` stay with SymPy.
    """
    return (
        len(args) == 1
        and not kwargs
        and _lazy.sympy_loaded()
        and pari_backend.is_rational_univariate(args[0])
    )


def matrix_domain(matrix, names):
    """Whether SymPy already knows the entries lie in one of ``names``.

    A SymPy ``Matrix`` keeps its entries in a ``DomainMatrix`` tagged
    with a domain, so ``is_ZZ`` or ``is_QQ`` answers "every entry is
    rational" in constant time instead of scanning n^2 entries — which
    is most of what dispatch costs on a matrix call (ARCHITECTURE §2.1).

    The converse does not hold: setting an entry of an ``EXRAW`` matrix
    back to an integer leaves the domain ``EXRAW``.  A domain that is
    not in ``names`` therefore proves nothing, and the caller scans.
    That is also why reading the private ``_rep`` is safe here: should
    SymPy rename it, this returns False and the scan still gives the
    right answer, only slower.
    """
    domain = getattr(getattr(matrix, "_rep", None), "domain", None)
    return domain is not None and any(getattr(domain, n) for n in names)


def series_product(args, kwargs):
    """Whether ``expand`` was given arithmetic on truncated series.

    Only ``Mul`` and ``Pow`` are worth intercepting: SymPy evaluates
    ``Add`` eagerly, so ``s + t`` is already a series by the time it
    arrives, while ``s * t`` is still an unevaluated product (M6, §2.1).
    The series must be univariate and around 0, which is what PARI's
    ``t_SER`` can represent.
    """
    if len(args) != 1 or kwargs or not _lazy.sympy_loaded():
        return False
    sympy = sys.modules["sympy"]
    expr = args[0]
    if not isinstance(expr, sympy.Expr) or not (expr.is_Mul or expr.is_Pow):
        return False
    orders = expr.atoms(sympy.Order)
    if not orders or len(expr.free_symbols) != 1:
        return False
    variables = {v for order in orders for v in order.variables}
    points = {p for order in orders for p in order.point}
    return len(variables) == 1 and points == {sympy.S.Zero}


def truncated_series(args, kwargs):
    """Whether every argument is a univariate series around 0.

    These operations exist only in PARI (M6 task 1), so the predicate
    guards the conversion rather than choosing between backends.
    """
    if not args or kwargs or not _lazy.sympy_loaded():
        return False
    sympy = sys.modules["sympy"]
    for expr in args:
        if not isinstance(expr, sympy.Expr):
            return False
        order = expr.getO()
        if order is None or len(order.variables) != 1:
            return False
        if any(point != 0 for point in order.point):
            return False
        if len(expr.free_symbols) != 1:
            return False
    return True


def _matrix_of(args, entry_test=None, domains=()):
    """Whether ``args[0]`` is a SymPy matrix whose entries pass the test.

    ``matrix.flat()`` rather than ``for e in matrix``: SymPy's
    ``__iter__`` costs about twice as much per entry.
    """
    if not args or not _lazy.sympy_loaded():
        return False
    matrix = args[0]
    if not isinstance(matrix, sys.modules["sympy"].MatrixBase):
        return False
    if entry_test is None or matrix_domain(matrix, domains):
        return True
    return all(map(entry_test, matrix.flat()))


def matrix(args, kwargs):
    """Whether the first argument is a matrix."""
    return _matrix_of(args)


def rational_matrix(args, kwargs):
    """Whether the first argument is a matrix over Q (PARI's domain)."""
    return _matrix_of(args, lambda e: e.is_Rational, ("is_ZZ", "is_QQ"))


def square_rational_matrix(args, kwargs):
    """Whether the first argument is a square matrix over Q.

    Shape first: it is O(1), while the entry scan is O(n^2).
    """
    if not args or not _lazy.sympy_loaded():
        return False
    return getattr(args[0], "is_square", False) and rational_matrix(
        args, kwargs
    )


def integer_matrix(args, kwargs):
    """Whether the first argument is a matrix over Z."""
    return _matrix_of(args, lambda e: e.is_Integer, ("is_ZZ",))


def linear_system(args, kwargs):
    """Whether ``args`` is ``(A, b)``, two matrices: ``solve(A, b)``.

    ``b`` must be a ``Matrix``: with a list, ``solve`` keeps SymPy's
    meaning (``solve([x + y - 1, x - y], [x, y])``).
    """
    return len(args) == 2 and not kwargs and _matrix_of(args[1:])


def rational_linear_system(args, kwargs):
    """Whether ``args`` is a square regular-sized linear system over Q."""
    return (
        linear_system(args, kwargs)
        and square_rational_matrix(args, kwargs)
        and _matrix_of(args[1:], lambda e: e.is_Rational)
    )


def modular_polynomials(args, kwargs):
    """Whether ``args`` are polynomials over Z and ``kwargs`` is ``modulus=p``.

    That is the case PARI's ``factormod`` handles, ×40 faster than SymPy
    at degree 49.
    """
    modulus = kwargs.get("modulus")
    if list(kwargs) != ["modulus"] or not args:
        return False
    if isinstance(modulus, bool) or not isinstance(modulus, int):
        return False
    if modulus < 2 or not _lazy.sympy_loaded():
        return False
    return pari_backend.is_prime_number(modulus) and all(
        pari_backend.is_modular_polynomial(arg, modulus) for arg in args
    )


def rational_polynomials(args, kwargs):
    """Whether every argument but the last is a polynomial over Q.

    ``resultant`` and ``discriminant`` pass ``(f, g, x)`` and ``(f, x)``,
    with the variable resolved; PARI takes the polynomials in ``x``
    alone, and symbolic coefficients stay with SymPy.
    """
    if not _lazy.sympy_loaded():
        return False
    *polynomials, var = args
    return all(
        pari_backend.is_rational_polynomial(p, var) for p in polynomials
    )


def finite_field_element(args, kwargs):
    """Whether the first argument is an element of a finite field."""
    return bool(args) and isinstance(args[0], FiniteFieldElement)


def polynomial_mod(args, kwargs):
    """Whether the first argument is a ``Mod`` with a polynomial modulus."""
    return bool(args) and isinstance(args[0], Mod) and args[0].is_polynomial


sympy_backend = _SympyBackend  # TABLE entries: sympy_backend("factor")

TABLE = {
    "expand": [
        (series_product, pari_backend.expand_series),
        (anything, sympy_backend("expand")),
    ],
    "factor": [
        (modular_polynomials, pari_backend.factor_polynomial_mod),
        (rational_univariate, pari_backend.factor_polynomial),
        (symbolic, sympy_backend("factor")),
        (number, pari_backend.factor),
    ],
    "simplify": [(anything, sympy_backend("simplify"))],
    "collect": [(anything, sympy_backend("collect"))],
    "cancel": [(anything, sympy_backend("cancel"))],
    "diff": [(anything, sympy_backend("diff"))],
    "integrate": [(anything, sympy_backend("integrate"))],
    "limit": [(anything, sympy_backend("limit"))],
    "solve": [
        (rational_linear_system, pari_backend.solve_linear),
        (linear_system, sympy_backend("solve_linear")),
        (anything, sympy_backend("solve")),
    ],
    "series": [(anything, sympy_backend("series"))],
    # Exact: PARI's ``n!`` for integers, SymPy for symbols (``factorial``
    # in PARI returns a real number).
    "factorial": [
        (number, pari_backend.factorial),
        (anything, sympy_backend("factorial")),
    ],
    "dedekind_psi": [(anything, pari_backend.dedekind_psi)],
    "jordan_totient": [(anything, pari_backend.jordan_totient)],
    "radical": [(anything, pari_backend.radical)],
    # Linear algebra (M5, D12): PARI over Q, SymPy for other entries.
    "det": [
        (square_rational_matrix, pari_backend.det),
        (matrix, sympy_backend("det")),
    ],
    "inverse": [
        (square_rational_matrix, pari_backend.inverse),
        (matrix, sympy_backend("inverse")),
    ],
    "rank": [
        (rational_matrix, pari_backend.rank),
        (matrix, sympy_backend("rank")),
    ],
    "kernel": [
        (rational_matrix, pari_backend.kernel),
        (matrix, sympy_backend("kernel")),
    ],
    "charpoly": [
        (finite_field_element, pari_backend.ff_charpoly),
        (square_rational_matrix, pari_backend.charpoly),
        (matrix, sympy_backend("charpoly")),
    ],
    "minpoly": [
        (finite_field_element, pari_backend.ff_minpoly),
        (square_rational_matrix, pari_backend.minpoly),
        (polynomial_mod, pari_backend.minpoly),
        (anything, sympy_backend("minimal_polynomial")),
    ],
    "isirreducible": [
        (modular_polynomials, pari_backend.isirreducible),
        (rational_univariate, pari_backend.isirreducible),
        (anything, sympy_backend("isirreducible")),
    ],
    # Resultants (M5, task 5): PARI over Q, SymPy for symbolic
    # coefficients.  Both follow the standard sign (ARCHITECTURE §3.4).
    "resultant": [
        (rational_polynomials, pari_backend.resultant),
        (anything, sympy_backend("resultant")),
    ],
    "discriminant": [
        (rational_polynomials, pari_backend.discriminant),
        (anything, sympy_backend("discriminant")),
    ],
    # Gröbner bases (M5, task 6): SymPy only, PARI has none.
    "groebner": [(anything, sympy_backend("groebner"))],
    "reduce": [(anything, sympy_backend("reduce_polynomial"))],
    "echelon_form": [(matrix, sympy_backend("echelon_form"))],
    "hadamard_product": [
        (truncated_series, pari_backend.hadamard_product),
    ],
    "generating_function": [
        (anything, sympy_backend("generating_function")),
    ],
    "series_reverse": [
        (truncated_series, pari_backend.series_reverse),
    ],
    "series_laplace": [
        (truncated_series, pari_backend.series_laplace),
    ],
    "hermite_form": [(integer_matrix, pari_backend.hermite_form)],
    "smith_form": [(integer_matrix, pari_backend.smith_form)],
}
# The other PARI prelude functions; gcd and lcm of expressions use SymPy.
for _name, _function in pari_backend.PRELUDE.items():
    if _name not in TABLE:
        TABLE[_name] = [(anything, _function)]
for _name in ("gcd", "lcm"):
    TABLE[_name].insert(0, (symbolic, sympy_backend(_name)))
TABLE["gcd"].insert(0, (modular_polynomials, pari_backend.gcd_mod))


def implementation(name, args, kwargs=None):
    """Return the implementation of ``name`` for these arguments."""
    kwargs = kwargs or {}
    for accepts, function in TABLE[name]:
        if accepts(args, kwargs):
            if isinstance(function, _SympyBackend):
                return function.resolve()
            return function
    kind = type(args[0]).__name__ if args else "no"
    raise TypeError(f"{name}() does not support {kind} arguments")


def _call(name, *args, **kwargs):
    return implementation(name, args, kwargs)(*args, **kwargs)


def expand(expr, *args, **kwargs):
    """Expand products and powers: ``(x + 1)^2`` gives ``x^2 + 2*x + 1``."""
    return _call("expand", expr, *args, **kwargs)


def factor(obj, *args, **kwargs):
    """Factor an integer, a rational number, or an expression.

    ``factor(12)`` gives ``2^2 * 3`` (PARI); ``factor(x^2 - 1)`` gives
    ``(x - 1)*(x + 1)`` (SymPy).  For numbers, ``limit=B`` gives a
    partial factorization by trial division up to ``B`` (D7).
    ``modulus=p`` (or ``domain=GF(p)``) factors over the field ``F_p``.
    """
    return _call("factor", obj, *args, **_modulus(kwargs))


def isirreducible(obj, **options):
    """Whether a polynomial is irreducible.

    Over Q by default; ``modulus=p`` (or ``domain=GF(p)``) asks over the
    field ``F_p``: ``isirreducible(x^2 + x + 1, modulus=2)`` is true.
    A constant polynomial is not irreducible (PARI's convention).
    """
    return _call("isirreducible", obj, **_modulus(options))


def _modulus(options):
    """Turn ``domain=GF(p)`` into ``modulus=p``, PARI's own option.

    Polynomials over ``GF(p^k)`` with ``k > 1`` need coefficients that are
    field elements, which no ER2 polynomial type has yet; PARI's
    ``pari.factormod`` factors them.
    """
    domain = options.get("domain")
    if not isinstance(domain, FiniteField):
        return options
    if domain.degree > 1:
        raise NotImplementedError(
            f"ER2 has no polynomials over {domain!r} yet; "
            "pari.raw.factormod gives PARI's own factorization"
        )
    options = dict(options)
    del options["domain"]
    options["modulus"] = int(domain.characteristic)
    return options


def simplify(expr, *args, **kwargs):
    """Return the simplest form of ``expr`` that SymPy finds."""
    return _call("simplify", expr, *args, **kwargs)


def collect(expr, syms, *args, **kwargs):
    """Collect the terms of ``expr`` by powers of ``syms``."""
    return _call("collect", expr, syms, *args, **kwargs)


def cancel(expr, *args, **kwargs):
    """Write a rational function as ``p/q`` in lowest terms."""
    return _call("cancel", expr, *args, **kwargs)


def diff(expr, *symbols, **kwargs):
    """Differentiate: ``diff(f, x)``, ``diff(f, x, 2)``, ``diff(f, x, y)``."""
    return _call("diff", expr, *symbols, **kwargs)


def integrate(expr, *limits, **kwargs):
    """Integrate: ``integrate(f, x)`` or ``integrate(f, (x, a, b))``."""
    return _call("integrate", expr, *limits, **kwargs)


def limit(expr, var, point, dir="+"):  # noqa: A002 (SymPy's name)
    """Return the limit of ``expr`` as ``var`` tends to ``point``."""
    return _call("limit", expr, var, point, dir=dir)


def solve(expr, *symbols, **kwargs):
    """Solve ``expr = 0`` (or an ``Eq``, or a list of them).

    ``solve(A, b)`` with two matrices solves the linear system
    ``A * v = b`` and returns ``v``.
    """
    return _call("solve", expr, *symbols, **kwargs)


def series(expr, x=None, x0=0, n=6, dir="+"):  # noqa: A002 (SymPy's name)
    """Return the power series of ``expr`` around ``x = x0``.

    The series is truncated with an ``O((x - x0)^n)`` term.
    """
    return _call("series", expr, x, x0, n, dir)


def factorial(n):
    """Return ``n!`` exactly; ``factorial(x)`` stays symbolic."""
    return _call("factorial", n)


def dedekind_psi(n):
    """Dedekind psi: ``n * prod(1 + 1/p)`` over the primes ``p | n``.

    ER2 has no ``psi``: PARI's and SciPy's ``psi`` is the digamma
    function, available as ``pari.digamma`` (D5).
    """
    return _call("dedekind_psi", n)


def jordan_totient(n, k):
    """Jordan's totient ``J_k(n)``: ``n^k * prod(1 - 1/p^k)`` over ``p | n``.

    ``jordan_totient(n, 1)`` is Euler's totient ``phi(n)`` (PARI
    ``eulerphi``).  GP has no built-in; this is
    ``sumdiv(n, d, d^k * moebius(n/d))``.
    """
    return _call("jordan_totient", n, k)


def radical(n):
    """Return ``rad(n)``, the product of the distinct primes of ``n``.

    GP has no built-in; this is ``factorback(factorint(n)[, 1])``.
    """
    return _call("radical", n)


def det(matrix):
    """Return the determinant of a square matrix.

    Rational matrices use PARI; symbolic ones use SymPy.
    """
    return _call("det", matrix)


def inverse(matrix):
    """Return the inverse of a square matrix.

    Raises ``NonInvertibleMatrixError`` (a ``ValueError``) if it is
    singular.
    """
    return _call("inverse", matrix)


def rank(matrix):
    """Return the rank of a matrix."""
    return _call("rank", matrix)


def kernel(matrix):
    """Return a basis of the right kernel ``{v : matrix * v = 0}``.

    The basis vectors are column matrices, in reduced echelon form (as
    Sage's echelonized basis): the same basis whichever backend computes
    it.  An invertible matrix has the empty list as its kernel basis.
    """
    vectors = _call("kernel", matrix)
    if not vectors:
        return []
    sympy = _lazy.sympy()
    echelon = sympy.Matrix.hstack(*vectors).T.rref()[0]
    return [echelon[i, :].T for i in range(len(vectors))]


def charpoly(matrix, x=None):
    """Return the characteristic polynomial ``det(x*I - matrix)`` in ``x``.

    ``x`` is the symbol ``x`` unless given.
    """
    return _call("charpoly", matrix, _variable(x))


def minpoly(obj, x=None):
    """Return the minimal polynomial of ``obj`` in ``x``.

    ``obj`` is a square matrix over Q, an algebraic number such as
    ``sqrt(2) + 1``, or a ``Mod`` with a polynomial modulus.  ``x`` is
    the symbol ``x`` unless given.
    """
    if matrix((obj,), {}) and not square_rational_matrix((obj,), {}):
        raise TypeError("minpoly() needs a square matrix over Q")
    return _call("minpoly", obj, _variable(x))


def resultant(f, g, x=None):
    """Return the resultant of ``f`` and ``g`` with respect to ``x``.

    It is zero exactly when ``f`` and ``g`` have a common root:
    ``resultant(x^2 + 1, x^3 - 2, x)`` is ``5``.  ``x`` may be left out
    when ``f`` and ``g`` have a single variable between them.

    ER2 follows the standard definition, ``Res(f, g) = lc(f)^deg(g) *
    prod g(a)`` over the roots ``a`` of ``f``, which is PARI's.  It is
    not symmetric: ``resultant(f, g) = (-1)^(deg f * deg g) *
    resultant(g, f)``, and it differs in sign from ``sympy.resultant``
    when ``deg f < deg g`` and both degrees are odd (ARCHITECTURE §3.4).
    """
    return _call("resultant", f, g, _polynomial_variable((f, g), x))


def discriminant(f, x=None):
    """Return the discriminant of ``f`` with respect to ``x``.

    ``discriminant(x^3 + x + 1)`` is ``-31``.  It is zero exactly when
    ``f`` has a repeated root.  ``x`` may be left out when ``f`` has a
    single variable.
    """
    return _call("discriminant", f, _polynomial_variable((f,), x))


def _polynomial_variable(polynomials, x):
    """Return ``x``, or the single variable of ``polynomials``."""
    if x is not None:
        return x
    symbols = set()
    for polynomial in polynomials:
        symbols |= getattr(polynomial, "free_symbols", set())
    if len(symbols) != 1:
        raise TypeError("the variable is needed: resultant(f, g, x)")
    return symbols.pop()


def groebner(seq, *gens, order="lex", **options):
    """Return a Gröbner basis of the ideal generated by ``seq``.

    ``groebner([x^2 + y^2 - 1, x - y], x, y)`` gives
    ``[x - y, 2*y^2 - 1]``.  The monomial order is ``"lex"`` unless
    given; ``"grlex"`` and ``"grevlex"`` are the other usual ones.

    The result is SymPy's ``GroebnerBasis``, a sequence of the basis
    polynomials.  Beware that ``f in G`` is Python's list membership,
    which asks whether ``f`` is one of those polynomials; membership of
    the *ideal* is ``reduce(f, G) == 0``, or SymPy's ``G.contains(f)``.
    """
    return _call("groebner", seq, *gens, order=order, **options)


def reduce(f, basis, *gens, **options):  # noqa: A001 (the mathematical name)
    """Return the remainder of ``f`` modulo ``basis``.

    ``reduce(x^2 + y^2, G)`` is ``1`` for the basis above.  Modulo a
    Gröbner basis the remainder is the normal form of ``f``: it is zero
    exactly when ``f`` belongs to the ideal, and it does not depend on
    the order of the basis.  Modulo a plain list of polynomials the
    remainder is whatever division by them in that order leaves.

    This is not ``functools.reduce``; import that one to use it.
    """
    return _call("reduce", f, basis, *gens, **options)


def echelon_form(matrix):
    """Return the reduced row echelon form of a matrix."""
    return _call("echelon_form", matrix)


def generating_function(sequence, x=None, n=None, exponential=False):
    """Return the truncated generating function of a sequence.

    ``sequence`` is anything iterable — a list, or an ``OEISSequence``
    from ``er2.oeis``, whose terms are taken in order from its offset::

        generating_function(oeis.sequence("A000045"), x, 10)

    gives ``x + x^2 + 2*x^3 + ... + O(x^10)``.  ``n`` truncates the
    sequence; without it every available term is used.  With
    ``exponential=True`` the result is the exponential generating
    function, ``sum a_k x^k / k!``.
    """
    terms = list(sequence)
    if n is not None:
        terms = terms[:n]
    if not terms:
        raise ValueError("a generating function needs at least one term")
    return _call(
        "generating_function", terms, _variable(x), exponential=exponential
    )


def series_reverse(s):
    """Return the compositional inverse of the power series ``s``.

    The series ``t`` with ``s(t(x)) = x``.  ``s`` must have no constant
    term and a non-zero linear one.  SymPy has no equivalent, so this
    is PARI's ``serreverse`` (M6).
    """
    return _call("series_reverse", s)


def hadamard_product(s, t):
    """Return the coefficientwise product of two power series.

    The series whose ``x^n`` coefficient is the product of those of
    ``s`` and ``t`` (PARI's ``serconvol``).
    """
    return _call("hadamard_product", s, t)


def series_laplace(s):
    """Turn an exponential generating function into an ordinary one.

    ``sum a_n x^n / n!`` becomes ``sum a_n x^n`` (PARI's ``serlaplace``),
    which is how an EGF is read as an OGF.
    """
    return _call("series_laplace", s)


def hermite_form(matrix):
    """Return the Hermite normal form of an integer matrix (PARI ``mathnf``).

    It is upper triangular, and its columns are a basis of the lattice
    spanned by the columns of ``matrix``.
    """
    return _call("hermite_form", matrix)


def smith_form(matrix):
    """Return the Smith normal form of an integer matrix.

    A diagonal matrix of the same shape with ``d_1 | d_2 | ...`` on the
    diagonal (PARI ``matsnf``).
    """
    return _call("smith_form", matrix)


def _variable(x):
    """Return ``x``, or the symbol ``x`` when it is ``None``."""
    return _lazy.sympy().Symbol("x") if x is None else x


def _public(name):
    """Return the dispatching public function for a PARI prelude row."""
    source = pari_backend.PRELUDE[name]

    def function(*args, **kwargs):
        return _call(name, *args, **kwargs)

    function.__name__ = function.__qualname__ = name
    function.__doc__ = source.__doc__
    return function


FUNCTIONS = {
    function.__name__: function
    for function in (
        expand,
        factor,
        simplify,
        collect,
        cancel,
        diff,
        integrate,
        limit,
        solve,
        generating_function,
        series,
        series_laplace,
        series_reverse,
        factorial,
        dedekind_psi,
        jordan_totient,
        radical,
        det,
        inverse,
        rank,
        kernel,
        charpoly,
        minpoly,
        resultant,
        discriminant,
        groebner,
        reduce,
        echelon_form,
        hadamard_product,
        hermite_form,
        smith_form,
        isirreducible,
    )
}
for _name in TABLE:
    if _name not in FUNCTIONS:
        FUNCTIONS[_name] = _public(_name)
