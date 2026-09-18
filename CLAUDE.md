# CLAUDE.md

Guía para Claude Code en este repositorio.

## Proyecto

**ER2 — Python matemático.** Superconjunto de Python con sintaxis simbólica (`sym x`, `x^2`, `_x`),
aritmética exacta por defecto y teoría de números vía PARI/GP.

- Idea original: [draft/ER2_idea_resumen.md](draft/ER2_idea_resumen.md)
- Diseño técnico y decisiones abiertas (D1–D7): [ARCHITECTURE.md](ARCHITECTURE.md) — **leer antes de implementar**.
- Estado: pre-implementación. Primer objetivo: el MVP de ARCHITECTURE.md §5.

## Principio rector

> No crear un lenguaje nuevo innecesariamente. Extender Python sólo donde es poco natural para las matemáticas.

Consecuencias prácticas:
- ER2 = **preparser fuente→fuente** + **runtime Python** + **backends** (SymPy, cypari2/PARI). No escribir intérprete, compilador ni gramática propia.
- **No** forkear CPython, SymPy, PARI ni cypari2 en las etapas 0.x. Se usan como dependencias.
- Toda sintaxis nueva debe poder expresarse como transformación de tokens hacia Python válido.
- No reimplementar algoritmos que PARI o SymPy ya tienen.

## Reglas de implementación

- **Preparser**: usar el módulo `tokenize`, nunca regex sobre el texto. No tocar strings, comentarios ni f-strings. Conservar números de línea.
- **Dispatch centralizado**: las funciones públicas (`factor`, `isprime`, …) eligen backend en `er2/dispatch.py`. Los backends no se importan entre sí.
- **Conversiones sólo en la frontera del backend** (`to_pari`/`from_pari`, `to_sympy`/`from_sympy`). El usuario no debe recibir `cypari2.gen` crudos.
- **Nombres ER2 ≠ nombres PARI**: `phi→eulerphi`, `mu→moebius`, `Omega→bigomega`. `psi` en PARI es la digamma (ver D5). Mantener el mapeo en una tabla única.
- **Salida**: notación matemática (`x^2`, `(x + 1)^2`), vía el printer de `er2/printing.py`.
- Cuando una tarea toque una decisión abierta D1–D7, proponer la resolución al usuario y registrarla en ARCHITECTURE.md §6 — no decidir en silencio.
- Precedente útil para dudas de diseño: el preparser de SageMath (`^`, `Integer`, `^^` para XOR).

## Entorno

- Python 3.14 (requisito mínimo propuesto: 3.12). Gestor: `uv`.
- SymPy 1.14 instalado. `cypari2` **no instalado** todavía (`uv add cypari2`; necesita libpari).
- PARI/GP 2.17.3 disponible como `gp` — útil para verificar resultados esperados:
  `printf 'eulerphi(123456)\n' | gp -q -D colors=no`
- No es todavía un repositorio git.

## Comandos (previstos — actualizar cuando existan)

```bash
uv sync                          # instalar dependencias
uv run er2 examples/mvp.er2      # ejecutar un programa ER2
uv run er2 --show-python f.er2   # ver el Python generado por el preparser
uv run er2                       # REPL
uv run pytest                    # todos los tests
uv run pytest tests/preparser    # sólo preparser
```

## Tests

- Preparser: pares entrada `.er2` → Python esperado; incluir casos de strings/comentarios con `^` y `sym`.
- Backends: comparar contra `gp` (teoría de números) y SymPy (CAS).
- Golden tests: programas en `tests/examples/` con su salida esperada.
- Evitar tests con factorizaciones que puedan tardar (ver D7).

## Idioma

Documentación y comunicación en español. Identificadores de código y API pública en inglés (convención Python/SymPy/PARI).
