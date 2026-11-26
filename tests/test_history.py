"""The benchmark history draws one graph per section from the runs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))

import history  # noqa: E402


def run(date, commit, ratio):
    """Return a saved run with one benchmark at ``ratio``."""
    return {
        "date": date,
        "commit": commit,
        "branch": "main",
        "note": "",
        "environment": {},
        "benchmarks": [
            {
                "section": "Integer arithmetic (D2)",
                "label": "`a + b`",
                "er2_s": ratio * 1e-7,
                "reference": "`int`",
                "reference_s": 1e-7,
            }
        ],
    }


def test_runs_become_graphs_and_a_table(tmp_path):
    for name, data in [
        ("2.json", run("2026-11-26 10:00", "bbbbbbb", 1.5)),
        ("1.json", run("2026-11-25 10:00", "aaaaaaa", 8.0)),
    ]:
        (tmp_path / name).write_text(json.dumps(data))
    runs = history.load_runs(tmp_path)
    assert [r["commit"] for r in runs] == ["aaaaaaa", "bbbbbbb"]
    sections = history.series(runs)
    assert sections["Integer arithmetic (D2)"]["`a + b` · vs `int`"] == [
        8.0,
        1.5,
    ]
    svg = history.svg_graph(
        "x", sections["Integer arithmetic (D2)"], ["a", "b"]
    )
    assert svg.startswith("<svg") and "polyline" in svg
    md = history.markdown(runs, sections)
    assert (
        "![Integer arithmetic (D2)](performance/integer-arithmetic-d2.svg)"
        in md
    )
    assert "| `a + b` · vs `int` | ×8.00 | ×1.50 | ×0.19 |" in md


def test_the_committed_history_is_drawn():
    """docs/PERFORMANCE.md has a graph for every recorded section."""
    runs = history.load_runs()
    assert runs, "benchmarks/history/ is empty"
    doc = history.DOC.read_text(encoding="utf-8")
    for title in history.series(runs):
        svg = f"performance/{history.slug(title)}.svg"
        assert svg in doc
        for folder in history.GRAPH_DIRS:
            assert (folder / Path(svg).name).is_file()
