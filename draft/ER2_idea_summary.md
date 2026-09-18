# ER2 — Python + Symbolic Mathematics + PARI/GP

## 1. Idea

**ER2** is a Python extension aimed at mathematical computation.

The idea is not to create an entirely new language, but to **extend Python** by adding, as first-class citizens:

- symbolic computation;
- exact arithmetic;
- number theory;
- computer algebra;
- transparent access to the algorithms of **PARI/GP**.

In one sentence:

> **ER2 = Python + symbolic language + PARI/GP number-theory computation.**

Python remains the base language, and ER2 preserves its ecosystem and philosophy as far as possible.

---

## 2. Goal

Allow writing code that combines conventional programming and mathematics naturally.

### Conventional Python

```python
x = 10

for n in range(1, 20):
    print(n)
```

### Symbolic mathematics

```er2
sym x, y

f = x^2 + 2*x + 1

expand(f)
factor(f)
diff(f, x)
```

### Number theory

```er2
factor(10^100 - 1)
isprime(2^127 - 1)
phi(123456)
sigma(123456)
```

The essential difference from Python + libraries is that mathematical syntax and semantics are part of ER2 itself.

---

## 3. Design philosophy

### 3.1 Python as the base

Do not replace Python.

ER2 should leverage:

- Python syntax;
- CPython;
- modules and packages;
- NumPy;
- SciPy;
- Matplotlib;
- Jupyter;
- the entire Python ecosystem.

### 3.2 Mathematics as a native extension

Add:

- symbols;
- expressions;
- polynomials;
- matrices;
- algebraic numbers;
- symbolic functions;
- equations;
- series;
- arithmetic functions.

### 3.3 Exact computation by default

Whenever possible:

```er2
1/3
```

represents exactly:

\[
\frac{1}{3}
\]

and not a `float`.

---

# 4. Symbolic syntax

## 4.1 Symbol declaration

Main form:

```er2
sym x
sym x, y, z
```

This replaces the more verbose form:

```python
x = Symbol("x")
y = Symbol("y")
z = Symbol("z")
```

## 4.2 Predefined symbols

The proposal is to use identifiers prefixed with `_`:

```er2
_x
_y
_z
_n
_k
_p
```

as predefined mathematical symbols.

This allows writing directly:

```er2
factor(_x^4 - 1)
```

Also:

```er2
x = _x
```

binds the mathematical symbol `x` to a conventional Python identifier.

Example:

```er2
x = _x

f = x^2 + 2*x + 1
factor(f)
```

produces:

```text
(x + 1)^2
```

## 4.3 Multiple variables

```er2
sym x, y, z

f = x^2 + y^2 + z^2
```

## 4.4 Powers

The proposal is to allow:

```er2
x^2
```

instead of requiring:

```python
x**2
```

The mathematical syntax would be translated internally into the corresponding AST/runtime representation.

---

# 5. Symbolic system

ER2 should initially support:

```text
Symbol
Expression
Integer
Rational
Real
Complex
Polynomial
Matrix
Vector
Set
Function
Equation
```

Fundamental operations:

```er2
expand(f)
factor(f)
simplify(f)
collect(f, x)
cancel(f)

diff(f, x)
integrate(f, x)
limit(f, x, a)

solve(equation, x)
series(f, x, 0, 10)
```

---

# 6. Number theory

Number theory must be one of the pillars of ER2.

Initial functions:

```er2
gcd(a, b)
lcm(a, b)

isprime(n)
nextprime(n)
factor(n)
divisors(n)

phi(n)
sigma(n)
mu(n)
psi(n)

omega(n)
Omega(n)
valuation(n, p)
```

Also:

```er2
znorder(a, n)
znprimroot(n)
```

and other specialized PARI/GP functions.

---

# 7. PARI/GP as the engine

ER2 should not try to reinvent PARI.

The initial architecture would be:

```text
                 ER2
                  |
        +---------+---------+
        |                   |
   Symbolic engine       PARI backend
        |                   |
      SymPy              cypari2
                            |
                         libpari
                            |
                           PARI
```

PARI would provide the specialized algorithms for number theory and exact computation.

The intent is that the user can write:

```er2
factor(10^1000 - 1)
```

without having to call PARI explicitly:

```python
pari("factor(...)")
```

ER2 decides which backend to use.

---

# 8. SymPy

SymPy can be used initially as the symbolic engine or as a reference.

There is no need to fork SymPy in the first stage.

Initial architecture:

```text
ER2
 |
 +-- Python / CPython
 |
 +-- Symbolic layer
 |      |
 |     SymPy
 |
 +-- Number theory
        |
       cypari2
          |
        PARI
```

In the long run, ER2 may develop its own symbolic components when needed.

---

# 9. Repositories and fork strategy

## CPython

Base repository:

```text
python/cpython
```

It is the candidate for a **future fork** if ER2 needs to modify the parser, AST, or runtime.

Modifying CPython is not recommended at the start.

## SymPy

Repository:

```text
sympy/sympy
```

Forking is not recommended initially.

Use it as a dependency and/or reference.

## PARI/GP

Official PARI/GP repository.

Forking is not recommended.

It should be kept as upstream.

## cypari2

Repository:

```text
sagemath/cypari2
```

It is the natural bridge between Python and PARI.

It would initially be used as a dependency.

A dedicated fork could appear later if ER2 needs a specific integration.

---

# 10. Development architecture

First stage:

```text
.er2
 |
 v
ER2 parser
 |
 v
Python AST / intermediate representation
 |
 v
CPython
 |
 +---- SymPy
 |
 +---- cypari2 --> PARI
```

This allows experimenting with ER2 without building a new compiler.

---

# 11. First MVP

The first goal should be small.

The following code should work:

```er2
sym x

f = x^2 + 2*x + 1

print(f)
print(expand(f))
print(factor(f))
```

Output:

```text
x^2 + 2*x + 1
x^2 + 2*x + 1
(x + 1)^2
```

And at the same time:

```er2
factor(2^127 - 1)
phi(123456789)
sigma(123456789)
isprime(2^521 - 1)
```

---

# 12. Roadmap

## ER2 0.1 — Symbolic core

- parser;
- `sym x, y, z`;
- `_x`, `_y`, `_z`;
- symbols;
- expressions;
- exact integers;
- rationals;
- `^` operator.

## ER2 0.2 — CAS

- `simplify`;
- `expand`;
- `factor`;
- `diff`;
- `integrate`;
- `solve`;
- polynomials.

## ER2 0.3 — Number Theory

- primality;
- factorization;
- divisors;
- `phi`;
- `sigma`;
- `mu`;
- arithmetic functions.

## ER2 0.4 — PARI

- `cypari2` integration;
- PARI types;
- automatic backend selection;
- ER2 vs PARI/GP benchmarks.

## ER2 0.5 — Algebra

- matrices;
- finite fields;
- polynomials;
- resultants;
- Gröbner bases;
- algebraic numbers.

## ER2 0.6 — Series

- power series;
- generating functions;
- Dirichlet series;
- Euler products.

## ER2 1.0 — Stable language

- formal specification;
- modules;
- documentation;
- Jupyter;
- installable package;
- test suite;
- benchmarks.

## ER2 2.0 — Deep CPython integration

Only once the syntax has settled:

- parser modifications;
- dedicated AST;
- mathematical runtime;
- optimizations;
- possible C/Rust extensions.

---

# 13. Relationship with OEIS

ER2 can integrate previous work on OEIS through a module:

```er2
import oeis

a = [phi(n) for n in range(1, 100)]

oeis.search(a)
```

Also:

```er2
def a(n):
    return phi(n) + sigma(n)

sequence(a, 100)
```

and later:

```er2
oeis.identify(a)
```

The goal would not only be to identify sequences, but to provide mathematical properties:

```text
sequence
multiplicative?
recurrence
generating function
Dirichlet series
Euler product
OEIS references
```

---

# 14. Distinguishing feature

ER2 does not aim to be simply:

```text
Python + SymPy + PARI
```

The difference must lie in the **linguistic integration**.

The user should be able to write, in the same program:

```er2
sym x, n

f = x^n + 1

g = factor(f)

for k in range(1, 100):
    if isprime(k):
        print(k)
```

That is:

> **Python programming and symbolic mathematics within the same language.**

---

# 15. Name and tagline

Name:

> **ER2**

In honor of the Hungarian mathematician **Paul Erdős**: in Spanish, "Erdős" sounds like "ER-dos" — *ER2*.

Provisional tagline:

> **ER2 — Programming Mathematics**

or:

> **ER2 — Python for Symbolic Mathematics**

Conceptually:

```text
Python
   +
Symbolic Mathematics
   +
Computational Number Theory
   +
PARI/GP
   =
ER2
```

---

# 16. Fundamental principle

The most important architectural decision is:

> **Do not create a new language unnecessarily. Extend Python where Python is unnatural for mathematics.**

ER2 must be, above all, **mathematical Python**.
