# ER2 — Python + Symbolic Mathematics + PARI/GP

## 1. Idea

**ER2** es una extensión de Python orientada al cálculo matemático.

La idea no es crear un lenguaje completamente nuevo, sino **ampliar Python** incorporando como ciudadanos de primera clase:

- cálculo simbólico;
- aritmética exacta;
- teoría de números;
- álgebra computacional;
- acceso transparente a los algoritmos de **PARI/GP**.

En una frase:

> **ER2 = Python + lenguaje simbólico + cálculo de teoría de números de PARI/GP.**

Python sigue siendo el lenguaje base y ER2 conserva, en lo posible, su ecosistema y filosofía.

---

## 2. Objetivo

Permitir escribir código que combine programación convencional y matemática de forma natural.

### Python convencional

```python
x = 10

for n in range(1, 20):
    print(n)
```

### Matemática simbólica

```er2
sym x, y

f = x^2 + 2*x + 1

expand(f)
factor(f)
diff(f, x)
```

### Teoría de números

```er2
factor(10^100 - 1)
isprime(2^127 - 1)
phi(123456)
sigma(123456)
```

La diferencia esencial respecto a Python + bibliotecas es que la sintaxis y la semántica matemática forman parte de ER2.

---

## 3. Filosofía de diseño

### 3.1 Python como base

No sustituir Python.

ER2 debe aprovechar:

- sintaxis Python;
- CPython;
- módulos y paquetes;
- NumPy;
- SciPy;
- Matplotlib;
- Jupyter;
- todo el ecosistema Python.

### 3.2 Matemática como extensión nativa

Añadir:

- símbolos;
- expresiones;
- polinomios;
- matrices;
- números algebraicos;
- funciones simbólicas;
- ecuaciones;
- series;
- funciones aritméticas.

### 3.3 Cálculo exacto por defecto

Cuando sea posible:

```er2
1/3
```

representa exactamente:

\[
\frac{1}{3}
\]

y no un `float`.

---

# 4. Sintaxis simbólica

## 4.1 Declaración de símbolos

Forma principal:

```er2
sym x
sym x, y, z
```

Esto sustituye a la forma más verbosa:

```python
x = Symbol("x")
y = Symbol("y")
z = Symbol("z")
```

## 4.2 Símbolos predefinidos

Se propone utilizar identificadores con `_`:

```er2
_x
_y
_z
_n
_k
_p
```

como símbolos matemáticos predefinidos.

Así puede escribirse directamente:

```er2
factor(_x^4 - 1)
```

También:

```er2
x = _x
```

permite asignar el símbolo matemático `x` a un identificador Python convencional.

Ejemplo:

```er2
x = _x

f = x^2 + 2*x + 1
factor(f)
```

produce:

```text
(x + 1)^2
```

## 4.3 Varias variables

```er2
sym x, y, z

f = x^2 + y^2 + z^2
```

## 4.4 Potencias

Se propone permitir:

```er2
x^2
```

en lugar de exigir:

```python
x**2
```

La sintaxis matemática se traduciría internamente a la representación correspondiente del AST/runtime.

---

# 5. Sistema simbólico

ER2 debería soportar inicialmente:

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

Operaciones fundamentales:

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

# 6. Teoría de números

La teoría de números debe ser uno de los pilares de ER2.

Funciones iniciales:

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

También:

```er2
znorder(a, n)
znprimroot(n)
```

y otras funciones especializadas de PARI/GP.

---

# 7. PARI/GP como motor

ER2 no debería intentar reinventar PARI.

La arquitectura inicial sería:

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

PARI proporcionaría los algoritmos especializados de teoría de números y cálculo exacto.

La intención es que el usuario pueda escribir:

```er2
factor(10^1000 - 1)
```

sin tener que llamar explícitamente a PARI:

```python
pari("factor(...)")
```

ER2 decide qué backend utilizar.

---

# 8. SymPy

SymPy puede utilizarse inicialmente como motor simbólico o como referencia.

No es necesario forkear SymPy en la primera etapa.

Arquitectura inicial:

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

A largo plazo, ER2 puede desarrollar componentes simbólicos propios cuando sea necesario.

---

# 9. Repositorios y estrategia de forks

## CPython

Repositorio base:

```text
python/cpython
```

Es el candidato a **fork futuro** si ER2 necesita modificar el parser, AST o runtime.

No se recomienda modificar CPython al principio.

## SymPy

Repositorio:

```text
sympy/sympy
```

No se recomienda forkear inicialmente.

Utilizarlo como dependencia y/o referencia.

## PARI/GP

Repositorio oficial de PARI/GP.

No se recomienda forkearlo.

Debe mantenerse como upstream.

## cypari2

Repositorio:

```text
sagemath/cypari2
```

Es el puente natural entre Python y PARI.

Inicialmente se utilizaría como dependencia.

Un fork propio podría aparecer posteriormente si ER2 necesita una integración específica.

---

# 10. Arquitectura de desarrollo

Primera etapa:

```text
.er2
 |
 v
ER2 parser
 |
 v
Python AST / representación intermedia
 |
 v
CPython
 |
 +---- SymPy
 |
 +---- cypari2 --> PARI
```

Esto permite experimentar con ER2 sin crear un nuevo compilador.

---

# 11. Primer MVP

El primer objetivo debe ser pequeño.

El siguiente código debería funcionar:

```er2
sym x

f = x^2 + 2*x + 1

print(f)
print(expand(f))
print(factor(f))
```

Resultado:

```text
x^2 + 2*x + 1
x^2 + 2*x + 1
(x + 1)^2
```

Y simultáneamente:

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
- símbolos;
- expresiones;
- enteros exactos;
- racionales;
- operador `^`.

## ER2 0.2 — CAS

- `simplify`;
- `expand`;
- `factor`;
- `diff`;
- `integrate`;
- `solve`;
- polinomios.

## ER2 0.3 — Number Theory

- primalidad;
- factorización;
- divisores;
- `phi`;
- `sigma`;
- `mu`;
- funciones aritméticas.

## ER2 0.4 — PARI

- integración con `cypari2`;
- tipos PARI;
- selección automática de backend;
- benchmarks ER2 vs PARI/GP.

## ER2 0.5 — Algebra

- matrices;
- cuerpos finitos;
- polinomios;
- resultantes;
- bases de Gröbner;
- números algebraicos.

## ER2 0.6 — Series

- series de potencias;
- funciones generatrices;
- series de Dirichlet;
- productos de Euler.

## ER2 1.0 — Lenguaje estable

- especificación formal;
- módulos;
- documentación;
- Jupyter;
- paquete instalable;
- suite de tests;
- benchmarks.

## ER2 2.0 — Integración profunda con CPython

Sólo cuando la sintaxis esté consolidada:

- modificaciones al parser;
- AST específico;
- runtime matemático;
- optimizaciones;
- posibles extensiones C/Rust.

---

# 13. Relación con OEIS

ER2 puede integrar el trabajo previo sobre OEIS mediante un módulo:

```er2
import oeis

a = [phi(n) for n in range(1, 100)]

oeis.search(a)
```

También:

```er2
def a(n):
    return phi(n) + sigma(n)

sequence(a, 100)
```

y posteriormente:

```er2
oeis.identify(a)
```

El objetivo no sería sólo identificar secuencias, sino proporcionar propiedades matemáticas:

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

# 14. Característica diferencial

ER2 no pretende ser simplemente:

```text
Python + SymPy + PARI
```

La diferencia debe estar en la **integración lingüística**.

El usuario debería poder escribir en un mismo programa:

```er2
sym x, n

f = x^n + 1

g = factor(f)

for k in range(1, 100):
    if isprime(k):
        print(k)
```

Es decir:

> **programación Python y matemáticas simbólicas dentro del mismo lenguaje.**

---

# 15. Nombre y lema

Nombre:

> **ER2**

Lema provisional:

> **ER2 — Programming Mathematics**

o:

> **ER2 — Python for Symbolic Mathematics**

Conceptualmente:

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

# 16. Principio fundamental

La decisión arquitectónica más importante es:

> **No crear un lenguaje nuevo innecesariamente. Extender Python allí donde Python resulta poco natural para las matemáticas.**

ER2 debe ser, ante todo, **Python matemático**.
