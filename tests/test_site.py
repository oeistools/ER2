"""The documentation site (PLAN.md, M8).

Rendering the site needs Quarto and takes a minute, so that is the
Pages workflow's job, not this suite's.  What is cheap and worth
guarding is the wiring, because each piece fails *silently*:

* a navbar entry pointing at a page that does not exist,
* losing the two files that make cells display as ER2 (D9),
* a link in an included document that ``doc-links.lua`` does not know,
  which reaches the site as a dead relative path.

The last one is the reason this file exists: the prose pages include
``docs/*.md`` verbatim, so a link added there is correct on GitHub and
broken on the site until the filter learns it.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CONFIG = SITE / "_quarto.yml"
FILTER = SITE / "doc-links.lua"

# The documents the site includes verbatim with ``{{< include >}}``.
INCLUDED = (
    "LANGUAGE.md",
    "STABILITY.md",
    "PARI_FUNCTIONS.md",
    "BENCHMARKS.md",
)


def test_the_site_exists():
    assert CONFIG.is_file()
    assert FILTER.is_file()


def test_every_navbar_page_exists():
    """A navbar entry that points nowhere renders as a dead link."""
    config = CONFIG.read_text(encoding="utf-8")
    hrefs = re.findall(r"href:\s*(\S+\.qmd)", config)
    assert hrefs, "the navbar lists no pages"
    missing = sorted(href for href in hrefs if not (SITE / href).is_file())
    assert not missing, f"navbar points at absent pages: {missing}"


def test_the_site_shows_cells_as_er2():
    """D9: the site reuses the examples' syntax definition and filter.

    Copies would drift; a missing one turns every ER2 cell back into a
    Python-looking one without failing the render.
    """
    config = CONFIG.read_text(encoding="utf-8")
    assert "../examples/er2.xml" in config
    assert "../examples/er2-cells.lua" in config
    assert (ROOT / "examples" / "er2.xml").is_file()
    assert (ROOT / "examples" / "er2-cells.lua").is_file()


def test_the_home_page_runs_er2():
    """The site's claim that ER2 runs is checked by running it."""
    index = (SITE / "index.qmd").read_text(encoding="utf-8")
    assert "jupyter: er2" in index
    assert "```{python}" in index, "cells are {python}, never {er2} (D9)"
    assert "```{er2}" not in index


@pytest.mark.parametrize("document", INCLUDED)
def test_every_included_link_is_rewritten(document):
    """A relative link in an included document must reach the site.

    ``doc-links.lua`` maps repository-relative targets either to a page
    of the site or to the file on GitHub. One it does not know arrives
    as a path that resolves nowhere.
    """
    source = (ROOT / "docs" / document).read_text(encoding="utf-8")
    lua = FILTER.read_text(encoding="utf-8")
    targets = {
        target.split("#")[0]
        for _, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", source)
        if not target.startswith(("http", "#", "mailto"))
    }
    unmapped = sorted(t for t in targets - {""} if f'["{t}"]' not in lua)
    assert not unmapped, (
        f"{document} links to {unmapped}, which site/doc-links.lua does "
        f"not map; the site would show a dead link."
    )


def test_the_pages_workflow_installs_the_kernel():
    """Without the er2 kernel the home page cannot execute."""
    workflow = ROOT / ".github" / "workflows" / "pages.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "er2 kernel install --sys-prefix" in text
    assert "QUARTO_PYTHON" in text
    assert "site/_site" in text
