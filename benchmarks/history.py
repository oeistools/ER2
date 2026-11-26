"""Benchmark history: one graph per section, run after run.

Every ``make bench-record`` saves a run in ``benchmarks/history/`` (all
the times, the commit, the machine and the versions).  This script reads
them all and writes ``docs/PERFORMANCE.md``: for each section, an SVG
graph of ``ER2 time / reference time`` per benchmark across the runs,
with the line at 1 where ER2 is as fast as the reference (Python or
PARI), and a table from the first run to the last.

The SVG is written by hand, so the history needs no plotting library.
The graphs go to ``docs/performance/`` and, for the site, to
``site/performance/``: the same relative path works in both.
"""

import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "benchmarks" / "history"
DOC = ROOT / "docs" / "PERFORMANCE.md"
GRAPH_DIRS = [ROOT / "docs" / "performance", ROOT / "site" / "performance"]

# Graph geometry (pixels) and colours, one per benchmark of a section
WIDTH, HEIGHT = 760, 320
LEFT, RIGHT, TOP, BOTTOM = 70, 20, 20, 60
COLOURS = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#9467bd",
    "#ff7f0e",
    "#17becf",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
]


def load_runs(folder=HISTORY):
    """Return the saved runs, oldest first."""
    runs = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(folder.glob("*.json"))
    ]
    return sorted(runs, key=lambda r: r["date"])


def slug(text):
    """Return a file-name form of a section title."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def series(runs):
    """Return ``{section: {label: [ratio or None per run]}}``."""
    out = {}
    for i, run in enumerate(runs):
        for b in run["benchmarks"]:
            labels = out.setdefault(b["section"], {})
            # the same benchmark may be timed against two references
            # (cypari2 and SymPy): both must be kept
            key = f"{b['label']} · vs {b['reference']}"
            ratios = labels.setdefault(key, [None] * len(runs))
            ratios[i] = b["er2_s"] / b["reference_s"]
    return out


def run_name(run):
    """Return the short name of a run: date and commit."""
    return f"{run['date'][:10]} {run.get('commit', '')[:7]}".strip()


def svg_graph(title, lines, names):
    """Return an SVG line graph of ratios (log scale) across runs."""
    values = [v for vs in lines.values() for v in vs if v] + [1.0]
    low = math.log10(min(values)) - 0.1
    high = math.log10(max(values)) + 0.1
    plot_w, plot_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    n = len(names)

    def x(i):
        return LEFT + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)

    def y(v):
        return TOP + plot_h * (high - math.log10(v)) / (high - low)

    legend_h = 18 * len(lines)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT + legend_h}" font-family="sans-serif" '
        'font-size="12">',
        f"<title>{html.escape(title)}</title>",
        f'<rect width="{WIDTH}" height="{HEIGHT + legend_h}" fill="white"/>',
    ]
    for p in range(math.floor(low), math.ceil(high) + 1):
        for m in (1, 2, 5):
            v = m * 10**p
            if low <= math.log10(v) <= high:
                out.append(
                    f'<line x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y(v):.1f}" '
                    f'y2="{y(v):.1f}" stroke="#e5e5e5"/>'
                    f'<text x="{LEFT - 6}" y="{y(v) + 4:.1f}" '
                    f'text-anchor="end">×{v:g}</text>'
                )
    out.append(
        f'<line x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y(1):.1f}" '
        f'y2="{y(1):.1f}" stroke="black" stroke-dasharray="5 3"/>'
        f'<text x="{WIDTH - RIGHT}" y="{y(1) - 4:.1f}" text-anchor="end">'
        "as fast as the reference</text>"
    )
    for i, name in enumerate(names):
        out.append(
            f'<text x="{x(i):.1f}" y="{HEIGHT - BOTTOM + 16}" '
            f'text-anchor="middle" font-size="10">{html.escape(name)}</text>'
        )
    for k, (label, vs) in enumerate(lines.items()):
        colour = COLOURS[k % len(COLOURS)]
        points = [(x(i), y(v)) for i, v in enumerate(vs) if v]
        if len(points) > 1:
            path = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
            out.append(
                f'<polyline points="{path}" fill="none" '
                f'stroke="{colour}" stroke-width="2"/>'
            )
        for px, py in points:
            out.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{colour}"/>'
            )
        ly = HEIGHT - 10 + 18 * k
        out.append(
            f'<rect x="{LEFT}" y="{ly - 9}" width="12" height="12" '
            f'fill="{colour}"/><text x="{LEFT + 18}" y="{ly + 1}">'
            f"{html.escape(label)}</text>"
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def markdown(runs, sections):
    """Return docs/PERFORMANCE.md: graphs and first-to-last tables."""
    first, last = runs[0], runs[-1]
    lines = [
        "# ER2 performance history",
        "",
        "Generated by `uv run python benchmarks/history.py` from the runs in "
        + "`benchmarks/history/` (`make bench-record` adds one); do not "
        + "edit by hand.",
        "",
        "Each graph shows, run after run, how long ER2 takes compared with "
        + "its reference (Python, `fractions`, SymPy or PARI through "
        + "cypari2): below the dashed line ER2 is faster.  The goal is ER2 "
        + "faster than Python and not much slower than PARI/GP.  Ratios are "
        + "compared, not times, so runs on the same machine are comparable "
        + "and the noise of a single run shows as small wiggles.",
        "",
        "Runs: "
        + "; ".join(
            f"{run_name(r)} ({r.get('branch', '?')}"
            + (f", {r['note']}" if r.get("note") else "")
            + ")"
            for r in runs
        )
        + ".",
    ]
    for title, data in sections.items():
        lines += [
            "",
            f"## {title}",
            "",
            f"![{title}](performance/{slug(title)}.svg)",
            "",
            f"| Benchmark | {run_name(first)} | {run_name(last)} | Change |",
            "|---|---|---|---|",
        ]
        for label, vs in data.items():
            a, b = vs[0], vs[-1]
            change = f"×{b / a:.2f}" if a and b else "—"
            fa = f"×{a:.2f}" if a else "—"
            fb = f"×{b:.2f}" if b else "—"
            lines.append(f"| {label} | {fa} | {fb} | {change} |")
    return "\n".join(lines) + "\n"


def main():
    """Write the graphs and docs/PERFORMANCE.md from the history."""
    runs = load_runs()
    if not runs:
        raise SystemExit("no runs in benchmarks/history/ (make bench-record)")
    sections = series(runs)
    names = [run_name(r) for r in runs]
    for folder in GRAPH_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
        for title, data in sections.items():
            svg = svg_graph(title, data, names)
            (folder / f"{slug(title)}.svg").write_text(svg, encoding="utf-8")
    DOC.write_text(markdown(runs, sections), encoding="utf-8")
    print(f"wrote {DOC.relative_to(ROOT)} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
