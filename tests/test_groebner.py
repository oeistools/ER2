"""Gröbner bases and polynomial reduction (M5, task 6).

PARI has no Gröbner bases, so these always go to SymPy.  ``groebner``
returns SymPy's ``GroebnerBasis``; ``reduce(f, G)`` returns the
remainder, which modulo a Gröbner basis is the normal form of ``f``.
"""

import pytest
import sympy

from er2 import dispatch
from er2.backends import sympy_backend
from er2.runtime.numbers import Integer

x, y, z = sympy.symbols("x y z")

# The acceptance example (PLAN.md, M5).
CIRCLE = [x**2 + y**2 - 1, x - y]


def test_backend_choice():
    impl = dispatch.implementation
    assert impl("groebner", (CIRCLE, x, y), {}) is sympy_backend.groebner
    assert impl("reduce", (x, CIRCLE), {}) is (sympy_backend.reduce_polynomial)


def test_groebner_basis():
    basis = dispatch.groebner(CIRCLE, x, y)
    assert isinstance(basis, sympy.GroebnerBasis)
    assert list(basis) == [x - y, 2 * y**2 - 1]
    assert basis.gens == (x, y)
    assert str(basis.order) == "lex"


def test_the_order_defaults_to_lex_and_can_be_changed():
    assert list(dispatch.groebner(CIRCLE, x, y)) == [x - y, 2 * y**2 - 1]
    assert list(dispatch.groebner(CIRCLE, x, y, order="grevlex")) == [
        2 * y**2 - 1,
        x - y,
    ]
    # The ideal is the same, so both bases reduce the same polynomials.
    for order in ("lex", "grlex", "grevlex"):
        basis = dispatch.groebner(CIRCLE, x, y, order=order)
        assert str(basis.order) == order
        assert dispatch.reduce(x**2 + y**2 - 1, basis) == 0


def test_a_basis_of_the_whole_ring_is_one():
    assert list(dispatch.groebner([x, x - 1], x)) == [1]
    assert dispatch.reduce(x**5 + 3, dispatch.groebner([x, x - 1], x)) == 0


def test_reduce_gives_the_normal_form():
    basis = dispatch.groebner(CIRCLE, x, y)
    remainder = dispatch.reduce(x**2 + y**2, basis)
    assert remainder == 1
    assert isinstance(remainder, Integer)
    # Zero exactly for the members of the ideal.
    assert dispatch.reduce(x**2 + y**2 - 1, basis) == 0
    assert dispatch.reduce(x - y, basis) == 0
    assert dispatch.reduce(x + y, basis) == 2 * y


def test_reduce_modulo_a_plain_list():
    """Without a basis object the generators are needed, as in SymPy."""
    assert dispatch.reduce(x**2 + y**2, CIRCLE, x, y) == 1
    quotients, remainder = sympy.reduced(x**2 + y**2, CIRCLE, x, y)
    assert dispatch.reduce(x**2 + y**2, CIRCLE, x, y) == remainder


def test_ideal_membership_is_reduce_not_in():
    """``f in G`` is Python's list membership, not the ideal (docstring)."""
    basis = dispatch.groebner(CIRCLE, x, y)
    f = x**2 + y**2 - 1
    assert dispatch.reduce(f, basis) == 0  # f is in the ideal
    assert basis.contains(f)
    assert f not in basis  # ...but it is not one of the two polynomials
    assert (x - y) in basis


def test_reduce_is_not_functools_reduce():
    """The prelude name is the polynomial one; ``functools`` still works."""
    import functools

    assert dispatch.reduce is not functools.reduce
    assert functools.reduce(lambda a, b: a + b, [1, 2, 3]) == 6


def test_a_known_basis():
    """The twisted cubic: a textbook lex basis."""
    basis = dispatch.groebner([y - x**2, z - x**3], x, y, z, order="lex")
    assert list(basis) == [x**2 - y, x * y - z, x * z - y**2, y**3 - z**2]
    assert dispatch.reduce(z**2 - y**3, basis) == 0


def test_er2_notation_in_the_repr(er2_printing):
    """The basis prints with ``^``, through ER2's printer (D11)."""
    basis = dispatch.groebner(CIRCLE, x, y)
    assert "2*y^2 - 1" in str(basis)
    assert "**" not in str(basis)


@pytest.fixture
def er2_printing():
    from er2 import printing

    printing.install()
    yield
    printing.uninstall()
