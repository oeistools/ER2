"""The Mermaid diagram in ARCHITECTURE.md §2 stays well formed.

GitHub renders Mermaid; this repository has no JavaScript toolchain, so
nothing here can prove the diagram *looks* right.  What it can prove is
that the block is structurally sound, which is where Mermaid actually
breaks in practice: an unbalanced ``subgraph``/``end``, an edge to a
node that was never declared, or a class applied to a name with no
``classDef``.  Any of those renders as an error box on GitHub instead
of a diagram, and would otherwise be noticed only by a reader.
"""

import re
from pathlib import Path

import pytest

ARCHITECTURE = Path(__file__).resolve().parent.parent / "ARCHITECTURE.md"
BLOCK = re.compile(r"^```mermaid\n(.*?)^```$", re.MULTILINE | re.DOTALL)
# A node declaration: an identifier followed by [, ( or { .
DECLARATION = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[\[({]")
# An edge: NODE --> NODE, with an optional |label| between.
EDGE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?:-->|---|-\.->)\s*"
    r"(?:\|[^|]*\|\s*)?"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)


@pytest.fixture(scope="module")
def diagram():
    blocks = BLOCK.findall(ARCHITECTURE.read_text(encoding="utf-8"))
    assert len(blocks) == 1, "§2 should hold exactly one Mermaid diagram"
    return blocks[0]


def test_the_diagram_declares_its_type(diagram):
    assert diagram.lstrip().startswith("flowchart ")


def test_subgraphs_are_balanced(diagram):
    """An unmatched ``end`` is the usual way a Mermaid block breaks."""
    opened = closed = 0
    for line in diagram.splitlines():
        stripped = line.strip()
        if stripped.startswith("subgraph "):
            opened += 1
        elif stripped == "end":
            closed += 1
    assert opened and opened == closed


def test_every_edge_joins_declared_nodes(diagram):
    """A typo in an edge silently invents an empty node."""
    declared = set()
    for line in diagram.splitlines():
        found = DECLARATION.match(line)
        if found and found.group(1) not in ("subgraph", "classDef", "class"):
            declared.add(found.group(1))
    # Subgraph identifiers are valid edge endpoints too.
    for line in diagram.splitlines():
        if line.strip().startswith("subgraph "):
            declared.add(line.split()[1])
    used = set()
    for line in diagram.splitlines():
        if line.strip().startswith(("classDef", "class ")):
            continue
        for left, right in EDGE.findall(line):
            used.update({left, right})
    assert used, "the diagram should have edges"
    assert used <= declared, f"undeclared nodes: {sorted(used - declared)}"


def test_styling_refers_to_defined_classes(diagram):
    """``class X missing`` leaves the node unstyled, without an error."""
    defined = {
        line.split()[1]
        for line in diagram.splitlines()
        if line.strip().startswith("classDef")
    }
    applied = {
        line.split()[2]
        for line in diagram.splitlines()
        if line.strip().startswith("class ")
    }
    assert applied <= defined, f"undefined: {sorted(applied - defined)}"


def test_the_plain_text_fallback_is_kept(diagram):
    """Readers without Mermaid still get the picture (§2)."""
    text = ARCHITECTURE.read_text(encoding="utf-8")
    assert "<details>" in text and "```text" in text
    # Both versions must name the same components, or they will drift.
    for component in ("er2.preparser", "er2.dispatch", "er2.printing"):
        assert component in diagram
        assert text.count(component) > 1
