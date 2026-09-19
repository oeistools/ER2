"""Synchronize the PARI -> ER2 function table with the bundled libpari.

Reads PARI's own function table (``functions_basic``) from the libpari
shipped inside the cypari2 wheel, and:

* updates ``er2/data/pari_functions.csv`` -- the single source of truth
  for ER2 names.  New PARI functions are added and summaries refreshed,
  but the hand-edited columns (``er2_name``, ``status``, ``note``) of
  existing rows are never overwritten;
* renders ``docs/PARI_FUNCTIONS.md`` from the CSV.

Run with::

    uv run python tools/sync_pari_functions.py
"""

import csv
import ctypes
import keyword
import re
from pathlib import Path

import cypari2

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "er2" / "data" / "pari_functions.csv"
DOC_PATH = ROOT / "docs" / "PARI_FUNCTIONS.md"
FIELDS = ["pari_name", "section", "er2_name", "status", "note", "summary"]

# PARI help sections (``?`` menu in gp).  19-21 are operators, member
# functions and internals; they are not functions ER2 exposes.
SECTIONS = {
    1: "Programming in GP",
    2: "Standard operators",
    3: "Conversions and elementary functions",
    4: "Combinatorics",
    5: "Number theory",
    6: "Polynomials and power series",
    7: "Linear algebra",
    8: "Transcendental functions",
    9: "Sums, products, integrals",
    10: "Number fields",
    11: "Associative algebras",
    12: "Elliptic and hyperelliptic curves",
    13: "L-functions",
    14: "Hypergeometric motives",
    15: "Modular forms",
    16: "Modular symbols",
    17: "Plotting",
}

STATUSES = {
    "prelude": "top-level ER2 name (in the prelude)",
    "namespace": "available as `pari.<er2_name>`",
    "wrapper": "needs an ER2 wrapper (takes GP code; not a cypari2 method)",
    "python": "not exposed: Python or its ecosystem already covers it",
    "conflict": "not exposed yet: naming conflict to resolve",
}

# Initial curated rows: (er2_name, status, note).  Used only when a PARI
# function has no row in the CSV yet; afterwards the CSV is edited by hand.
CURATED = {
    "eulerphi": ("phi", "prelude", "draft name"),
    "moebius": ("mu", "prelude", "draft name"),
    "bigomega": (
        "bigomega",
        "prelude",
        "draft `Omega`, renamed for PEP 8 (D8)",
    ),
    "psi": (
        "digamma",
        "namespace",
        "PARI psi = digamma; Dedekind psi is dedekind_psi (D5)",
    ),
    "factor": (
        "factor",
        "prelude",
        "dispatch: integers -> PARI, Expr -> SymPy",
    ),
    "deriv": ("deriv", "namespace", "ER2 `diff` dispatches to SymPy"),
    "factorial": (
        "factorial",
        "namespace",
        "PARI returns a real; the exact `factorial` is in the prelude",
    ),
    "Pi": ("pi", "namespace", "constant; lowercase like SymPy"),
    "Euler": ("euler_gamma", "namespace", "constant; SymPy name"),
    "Catalan": ("catalan", "namespace", "constant; SymPy name"),
    "I": ("I", "namespace", "constant; SymPy name"),
}
PRELUDE_SAME_NAME = {
    "gcd",
    "lcm",
    "isprime",
    "ispseudoprime",
    "isprimepower",
    "nextprime",
    "precprime",
    "prime",
    "primes",
    "primepi",
    "divisors",
    "numdiv",
    "sigma",
    "omega",
    "valuation",
    "znorder",
    "znprimroot",
    "znlog",
    "kronecker",
    "chinese",
    "issquare",
    "issquarefree",
    "ispower",
    "sqrtint",
    "core",
    "binomial",
    "fibonacci",
}
PYTHON_EQUIVALENT = {1: "use Python", 17: "use Matplotlib"}
BUILTIN_CLASH = {"abs", "max", "min", "round", "sum", "eval"}


def read_pari_table():
    """Return ``[(name, section, summary), ...]`` from libpari."""
    cypari2.Pari()
    libs = ROOT / ".venv"
    candidates = sorted(
        libs.glob("lib/python*/site-packages/cypari2.libs/libpari-*.so*")
    )
    if not candidates:
        raise SystemExit("libpari from cypari2 not found; run `uv sync`")
    lib = ctypes.CDLL(str(candidates[0]))

    class Entree(ctypes.Structure):
        # ``entree`` from PARI's parinf.h (2.17).
        _fields_ = [
            ("name", ctypes.c_char_p),
            ("valence", ctypes.c_ulong),
            ("value", ctypes.c_void_p),
            ("menu", ctypes.c_long),
            ("code", ctypes.c_char_p),
            ("help", ctypes.c_char_p),
            ("pvalue", ctypes.c_void_p),
            ("arity", ctypes.c_long),
            ("hash", ctypes.c_ulong),
            ("next", ctypes.c_void_p),
        ]

    table = (Entree * 10000).in_dll(lib, "functions_basic")
    rows = []
    for entry in table:
        if not entry.name:
            break
        if entry.menu in SECTIONS:
            help_text = (entry.help or b"").decode(errors="replace")
            rows.append(
                (entry.name.decode(), entry.menu, summarize(help_text))
            )
    if ("eulerphi", 5) not in {(n, s) for n, s, _ in rows}:
        raise SystemExit(
            "unexpected libpari layout: eulerphi not in "
            "section 5; check the Entree struct"
        )
    return rows


def summarize(help_text):
    """Return the first sentence of a PARI help string, without signature."""
    text = " ".join(help_text.split())
    text = re.sub(r"^[^:]*?\)\s*:\s*", "", text, count=1)
    text = text.split(". ")[0].rstrip(".")
    return text[:120] + ("…" if len(text) > 120 else "")


def to_snake_case(name):
    """Convert a PARI camelCase name (``mfDelta``) to PEP 8 snake_case."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def default_row(name, section, summary):
    """Build the initial CSV row for a PARI function without one."""
    row = {
        "pari_name": name,
        "section": section,
        "summary": summary,
        "er2_name": name,
        "status": "namespace",
        "note": "",
    }
    if name in CURATED:
        row["er2_name"], row["status"], row["note"] = CURATED[name]
    elif section in PYTHON_EQUIVALENT:
        row["status"] = "python"
        row["note"] = PYTHON_EQUIVALENT[section]
    elif name in PRELUDE_SAME_NAME:
        row["status"] = "prelude"
    elif section == 3 and re.fullmatch(r"[A-Z][a-z]+", name):
        row["note"] = "type constructor (CapWords allowed by PEP 8)"
    elif name != name.lower():
        row["er2_name"] = to_snake_case(name)
        row["note"] = "renamed for PEP 8"
    if name in BUILTIN_CLASH:
        row["note"] = "Python builtin: never shadowed in the prelude"
    if keyword.iskeyword(row["er2_name"]):
        row["er2_name"] += "_"
    if row["status"] in ("prelude", "namespace") and not hasattr(
        cypari2.Pari(), name
    ):
        row["status"] = "wrapper"
        row["note"] = "GP expression argument; ER2 takes a Python callable"
    return row


def load_csv():
    """Return existing rows keyed by PARI name."""
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        return {row["pari_name"]: row for row in csv.DictReader(fh)}


def write_csv(rows):
    """Write rows sorted by section, then PARI name."""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_doc(rows):
    """Render the Markdown reference from the CSV rows."""
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    lines = [
        "# PARI functions and their ER2 names",
        "",
        "Generated by `tools/sync_pari_functions.py` from the libpari "
        "bundled with cypari2",
        f"(PARI {'.'.join(map(str, cypari2.Pari().version()))}). "
        "**Do not edit by hand**: edit",
        "[er2/data/pari_functions.csv](../er2/data/pari_functions.csv) "
        "and re-run the script.",
        "",
        "| Status | Meaning | Count |",
        "|--------|---------|-------|",
    ]
    for status, meaning in STATUSES.items():
        lines.append(f"| `{status}` | {meaning} | {counts.get(status, 0)} |")
    lines.append(f"| | **total** | {len(rows)} |")
    for section, title in SECTIONS.items():
        section_rows = [r for r in rows if int(r["section"]) == section]
        if not section_rows:
            continue
        lines += [
            "",
            f"## {section}. {title} ({len(section_rows)})",
            "",
            "| PARI | ER2 | Status | Note | Description |",
            "|------|-----|--------|------|-------------|",
        ]
        for r in section_rows:
            er2 = "" if r["status"] == "python" else f"`{r['er2_name']}`"
            cells = [
                f"`{r['pari_name']}`",
                er2,
                r["status"],
                r["note"],
                r["summary"],
            ]
            lines.append(
                "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
            )
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Merge libpari's table into the CSV and regenerate the docs."""
    existing = load_csv()
    rows = []
    for name, section, summary in read_pari_table():
        row = existing.get(name) or default_row(name, section, summary)
        row["section"], row["summary"] = section, summary
        rows.append(row)
    rows.sort(key=lambda r: (int(r["section"]), r["pari_name"].lower()))
    removed = set(existing) - {r["pari_name"] for r in rows}
    write_csv(rows)
    write_doc(rows)
    print(
        f"{len(rows)} functions -> {CSV_PATH.relative_to(ROOT)}, "
        f"{DOC_PATH.relative_to(ROOT)}"
    )
    if removed:
        print("no longer in PARI (dropped):", ", ".join(sorted(removed)))


if __name__ == "__main__":
    main()
