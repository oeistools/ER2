# ER2 — Arquitectura

> Documento de diseño técnico. Fuente de la idea: [draft/ER2_idea_resumen.md](draft/ER2_idea_resumen.md).
> Estado: **pre-implementación** (no hay código todavía).

## 1. Qué es ER2

ER2 es **Python matemático**: un superconjunto de Python que añade sintaxis simbólica
(`sym x`, `x^2`, `_x`), aritmética exacta por defecto y acceso transparente a PARI/GP.

No es un lenguaje nuevo ni un intérprete nuevo. En las etapas 0.x, ER2 es:

1. un **preprocesador fuente→fuente** (`.er2` → Python válido),
2. un **runtime** (paquete `er2`) que define tipos y funciones matemáticas,
3. unos **backends** (SymPy para lo simbólico, PARI vía cypari2 para teoría de números).

El código generado se ejecuta en CPython sin modificar. El fork de CPython sólo se
considera en 2.0 (ver §9).

Precedente directo: el *preparser* de SageMath hace exactamente esto
(`^`→`**`, literales enteros envueltos en `Integer`). Conviene estudiarlo antes de reinventar.

## 2. Vista general

```text
 fuente .er2 / celda Jupyter / REPL
              │
              ▼
 ┌─────────────────────────────┐
 │ er2.preparser               │  tokenize → transformar tokens → untokenize
 │  - sym x, y   → asignaciones│  (NO regex sobre texto crudo: respeta strings,
 │  - ^          → **          │   comentarios, f-strings)
 │  - literales  → Integer(…)  │
 └──────────────┬──────────────┘
                ▼
        Python válido (str)  ──►  ast.parse / compile  ──►  CPython
                                                               │
                         namespace inicial = er2.prelude  ◄────┘
                                        │
 ┌──────────────────────────────────────┴────────────────────────┐
 │ er2.runtime                                                    │
 │  tipos: Integer, Rational, Symbol, Expr, …                     │
 │  funciones públicas: factor, expand, diff, isprime, phi, …     │
 │  er2.dispatch: elige backend según tipo de argumento           │
 │  er2.printing: salida estilo matemático (x^2, no x**2)         │
 └───────────────┬────────────────────────────┬───────────────────┘
                 ▼                            ▼
     er2.backends.sympy            er2.backends.pari
          SymPy                  cypari2 → libpari
```

## 3. Componentes

### 3.1 Preparser (`er2/preparser.py`)

Entrada: texto ER2. Salida: texto Python equivalente. Función pura, sin estado, fácil de testear
con pares entrada/salida.

Transformaciones (0.1):

| ER2                | Python generado                                   | Notas |
|--------------------|---------------------------------------------------|-------|
| `sym x, y`         | `x, y = __er2_symbols__("x y")`                   | sólo al inicio de sentencia (soft keyword, como `match`) |
| `x^2`              | `x**2`                                            | ver D1 |
| `a ^^ b`           | `a ^ b`                                           | XOR explícito (convención Sage) |
| `1/3`              | `Integer(1)/Integer(3)` → `Rational(1, 3)`        | ver D2 |
| `_x`               | sin cambio; `_x` está en el prelude               | ver D3 |

Requisitos:
- Basado en el módulo `tokenize`; nunca tocar el contenido de strings ni comentarios.
- Debe preservar números de línea (los errores deben apuntar a la línea del `.er2`).
- Idempotente sobre Python puro que no use `^` ni `sym`.
- `er2 --show-python archivo.er2` debe imprimir el Python generado (depuración).

### 3.2 Puntos de entrada

- **CLI**: `er2 archivo.er2` y REPL `er2` (basado en `code.InteractiveConsole` con el preparser).
- **Import hook**: `import modulo` encuentra `modulo.er2` (meta path finder + loader).
- **Jupyter**: extensión IPython que registra el preparser en `input_transformers_post`
  (`%load_ext er2`).

Los tres comparten `er2.preparser` y `er2.prelude`; ninguno tiene lógica propia de traducción.

### 3.3 Runtime y prelude (`er2/runtime/`, `er2/prelude.py`)

`prelude` define el namespace inicial: tipos, funciones públicas y símbolos `_x, _y, _z, _n, _k, _p`.

Tipo canónico de enteros: **uno solo** en el lado ER2 (propuesta: `sympy.Integer`, que usa gmpy2
si está instalado). Requisitos: `__index__` (para que `range`, indexado y slicing sigan
funcionando), conversión sin pérdida a/desde `cypari2.gen` y a/desde `int`.

### 3.4 Dispatch (`er2/dispatch.py`)

Las funciones públicas son genéricas y deciden backend por tipo:

```text
factor(n: entero)        → PARI  factor / factorint
factor(p: polinomio/Expr) → SymPy factor
isprime(n)               → PARI  isprime (prueba) / ispseudoprime (opción)
```

- La tabla de dispatch vive en un único sitio, no dispersa por funciones.
- Toda conversión de tipos ocurre en la frontera del backend (`to_pari`, `from_pari`,
  `to_sympy`, `from_sympy`). El usuario nunca ve un `cypari2.gen` ni un objeto SymPy "desnudo"
  salvo que lo pida.
- `factor(n)` entero devuelve un objeto `Factorization` propio (imprime `2^3 * 3^2`), no una matriz PARI.

### 3.5 Tabla de nombres ER2 → PARI

Los nombres del borrador no coinciden con PARI; hace falta un mapeo explícito
(verificado con PARI 2.17.3):

| ER2            | PARI              | Observación |
|----------------|-------------------|-------------|
| `phi(n)`       | `eulerphi(n)`     | `phi` está obsoleto en GP |
| `mu(n)`        | `moebius(n)`      | |
| `sigma(n, k=1)`| `sigma(n, k)`     | |
| `omega(n)`     | `omega(n)`        | |
| `Omega(n)`     | `bigomega(n)`     | |
| `valuation`    | `valuation`       | |
| `znorder`, `znprimroot`, `nextprime`, `divisors`, `gcd`, `lcm` | igual | |
| `psi(n)`       | **conflicto**     | en PARI `psi` es la digamma; en el borrador se lista como aritmética (¿ψ de Dedekind?). Ver D5 |

### 3.6 Printing (`er2/printing.py`)

`print(f)`, `str`, `repr` y la salida de Jupyter usan notación ER2: `x^2 + 2*x + 1`, `(x + 1)^2`.
Implementar como subclase de `sympy.printing.str.StrPrinter` (`_print_Pow`) y `_repr_latex_`
para Jupyter.

### 3.7 Backends (`er2/backends/`)

- `sympy_backend.py` — CAS: `expand, factor, simplify, collect, cancel, diff, integrate, limit, solve, series`.
- `pari_backend.py` — teoría de números. Instancia única de `cypari2.Pari()`; tamaño de pila
  configurable (`er2.config.pari_stack`).
- Un backend no importa al otro. Sólo `dispatch` conoce ambos.

## 4. Estructura de repositorio propuesta

```text
er2/
  __init__.py
  __main__.py          # CLI: er2 file.er2 | er2 (REPL) | er2 --show-python
  preparser.py
  prelude.py
  dispatch.py
  printing.py
  importer.py          # import hook .er2
  ipython_ext.py       # %load_ext er2
  runtime/             # tipos: Integer, Rational, Symbol, Factorization, …
  backends/
    sympy_backend.py
    pari_backend.py
tests/
  preparser/           # pares .er2 → .py esperados
  runtime/
  backends/
  examples/            # programas .er2 completos con salida esperada (golden)
examples/
  mvp.er2
draft/                 # documentos de idea (no código)
pyproject.toml
```

## 5. MVP (objetivo de la primera iteración)

Debe ejecutarse con `er2 examples/mvp.er2`:

```er2
sym x
f = x^2 + 2*x + 1
print(f)            # x^2 + 2*x + 1
print(expand(f))    # x^2 + 2*x + 1
print(factor(f))    # (x + 1)^2

print(factor(2^127 - 1))
print(phi(123456789))
print(sigma(123456789))
print(isprime(2^521 - 1))

for k in range(1, 20):
    if isprime(k):
        print(k)
```

Esto ejercita las cuatro piezas: preparser, printing, dispatch y ambos backends.

## 6. Decisiones de diseño abiertas

Cada una debe resolverse (y registrarse aquí) antes o durante 0.1.

- **D1 — `^` como potencia.** En Python `^` es XOR. Propuesta: en ficheros `.er2`, `^` es siempre
  potencia y `^^` es XOR (como Sage). Consecuencia: código Python pegado que use XOR cambia de
  significado; el preparser puede avisar si detecta `^` entre operandos claramente enteros-bitmask.
  Precedencia: al convertir a `**` se hereda la de Python (`-x^2` = `-(x^2)`, `2^3^2` = `2^(3^2)`),
  que es la matemática. Documentarlo.
- **D2 — Exactitud por defecto.** Envolver literales enteros en `Integer` (y decimales en un
  `Real`/`Float` de precisión controlada) hace que `1/3` sea racional. Riesgos: rendimiento en
  bucles numéricos y compatibilidad con librerías que esperan `int` (NumPy). Requiere `__index__`
  y probar `range`, `list[i]`, `numpy.zeros(n)`. Alternativa: sólo envolver cuando hay `/`.
- **D3 — `_x` predefinidos.** `_`-prefijo significa "privado" en Python y `_` es el último
  resultado en el REPL. Riesgo bajo pero existe. Si el usuario asigna `_n = 5`, se sombrea el
  símbolo (comportamiento Python normal, aceptable).
- **D4 — `sym` como soft keyword.** Sólo reconocido como `sym <nombre>[, <nombre>…]` al inicio
  de línea lógica. `sym = 3` o `sym(x)` siguen siendo Python.
- **D5 — `psi`.** Decidir si es ψ de Dedekind (aritmética) o digamma. Propuesta: `psi` = Dedekind
  (coherente con la lista de funciones aritméticas) y `digamma` explícito.
- **D6 — Tipo entero canónico.** `sympy.Integer` vs `gmpy2.mpz` vs clase propia. Afecta coste
  de conversión con PARI y con SymPy. Medir antes de decidir.
- **D7 — Factorizaciones costosas.** `factor(10^1000 - 1)` (ejemplo del borrador, §7) puede no
  terminar en tiempo razonable. Definir política: timeout, `factor(n, partial=True)`, o dejarlo al
  usuario.

## 7. Observaciones sobre el roadmap del borrador

- 0.3 (teoría de números) precede a 0.4 (integración PARI), pero las funciones de 0.3 se
  implementan *sobre* PARI. Propuesta: fusionar la integración básica con cypari2 en 0.3 y dejar
  para 0.4 la selección automática de backend, tipos PARI avanzados y benchmarks.
- El MVP (§11 del borrador) abarca 0.1–0.3. O se amplía 0.1, o el MVP se declara hito de 0.3.

## 8. Dependencias

- Python ≥ 3.12 (entorno actual: 3.14).
- `sympy` (1.14 instalado), opcional `gmpy2`.
- `cypari2` (no instalado) → requiere `libpari` (PARI 2.17 presente en el sistema como `gp`).
- `ipython` (opcional, extensión Jupyter).
- Gestión con `uv`.

## 9. Evolución (2.0)

Sólo cuando la sintaxis sea estable: fork de `python/cpython` para mover las transformaciones del
preparser a la gramática PEG real (tokens `sym`, `^`), AST específico y runtime matemático.
Mientras tanto, **toda** extensión sintáctica debe ser expresable como transformación de tokens
sobre Python válido; si una propuesta no lo es, es una señal de que se aleja del principio
"Python matemático".

## 10. Integración OEIS (futuro)

Módulo `er2.oeis` (`search`, `identify`) y `sequence(f, n)`. Fuera del alcance hasta ≥ 0.6;
reutilizará el trabajo previo sobre OEIS del autor.
