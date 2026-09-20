"""ER2 in Jupyter and Quarto (ARCHITECTURE.md §1.2).

Route A is the ``er2`` kernel; route B is ``%load_ext er2`` in a standard
``python3`` kernel.  The Quarto test is skipped when Quarto is missing.
"""

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import nbformat
import pytest
from jupyter_client.manager import start_new_kernel
from nbclient import NotebookClient

from er2.kernel import install_kernel

# CI's Quarto job sets ER2_REQUIRE_QUARTO, so these tests fail instead of
# being skipped if Quarto is missing there.
needs_quarto = pytest.mark.skipif(
    shutil.which("quarto") is None
    and not os.environ.get("ER2_REQUIRE_QUARTO"),
    reason="needs Quarto",
)


@pytest.fixture(scope="module")
def jupyter_path(tmp_path_factory):
    """Install the ER2 kernelspec in a private Jupyter data directory."""
    prefix = tmp_path_factory.mktemp("jupyter")
    install_kernel(user=False, prefix=str(prefix))
    path = str(prefix / "share" / "jupyter")
    old = os.environ.get("JUPYTER_PATH")
    os.environ["JUPYTER_PATH"] = path
    yield path
    if old is None:
        os.environ.pop("JUPYTER_PATH", None)
    else:
        os.environ["JUPYTER_PATH"] = old


def run_notebook(kernel_name, cells, allow_errors=False):
    """Execute ``cells`` in a new notebook; return the executed cells."""
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_code_cell(source) for source in cells]
    NotebookClient(
        nb, kernel_name=kernel_name, timeout=120, allow_errors=allow_errors
    ).execute()
    return nb.cells


def text(cell):
    """Return the text output (stream or plain result) of a cell."""
    parts = []
    for out in cell.outputs:
        if out.output_type == "stream":
            parts.append(out.text)
        elif out.output_type == "execute_result":
            parts.append(out.data["text/plain"] + "\n")
    return "".join(parts)


M1_CELLS = [
    "sym x",
    "print(2^10, 1/3, 5 ^^ 3)",
    "x^2 + 1",
    "latex(x^2)",
]


def check_m1_cells(cells):
    assert text(cells[1]) == "1024 1/3 6\n"
    result = cells[2].outputs[0]
    assert result.data["text/plain"] == "x^2 + 1"
    assert "x^{2} + 1" in result.data["text/latex"]
    assert cells[3].outputs[0].data["text/markdown"] == "$x^{2}$"


# The first half of the MVP (ARCHITECTURE.md §5).
M2_CELLS = [
    "sym x\nf = x^2 + 2*x + 1",
    "print(f)\nprint(expand(f))\nprint(factor(f))",
    "show(factor(f))",
    "print(latex(f))",
    "factor(f)",
    "integrate(f, (x, 0, 1))",
]


def check_m2_cells(cells):
    assert text(cells[1]) == "x^2 + 2*x + 1\nx^2 + 2*x + 1\n(x + 1)^2\n"
    shown = cells[2].outputs[0]
    assert shown.output_type == "display_data"
    assert shown.data["text/latex"] == r"$$\left(x + 1\right)^{2}$$"
    assert text(cells[3]) == "x^{2} + 2 x + 1\n"
    result = cells[4].outputs[0].data
    assert result["text/plain"] == "(x + 1)^2"
    assert r"\left(x + 1\right)^{2}" in result["text/latex"]
    area = cells[5].outputs[0].data
    assert area["text/plain"] == "7/3"
    assert area["text/latex"] == r"$\frac{7}{3}$"


def test_er2_kernel(jupyter_path):
    cells = run_notebook("er2", M1_CELLS + M2_CELLS)
    check_m1_cells(cells[: len(M1_CELLS)])
    check_m2_cells(cells[len(M1_CELLS) :])


def test_load_ext_in_python_kernel():
    cells = run_notebook("python3", ["%load_ext er2", *M1_CELLS, *M2_CELLS])
    check_m1_cells(cells[1 : 1 + len(M1_CELLS)])
    check_m2_cells(cells[1 + len(M1_CELLS) :])


def test_er2_kernel_errors_show_the_er2_source(jupyter_path):
    cells = run_notebook("er2", ["a = 2^3\nb = a / 0"], allow_errors=True)
    error = cells[0].outputs[0]
    assert error.output_type == "error"
    assert error.ename == "ZeroDivisionError"
    traceback = "".join(error.traceback)
    assert "line 2" in traceback
    assert "__er2_int__" not in traceback
    # ER2's own frames are hidden, as in the CLI (M4).
    assert "numbers.py" not in traceback


@pytest.mark.parametrize("kernel", ["er2", "python3"])
def test_tracebacks_end_at_the_user_line(jupyter_path, kernel):
    setup = ["%load_ext er2"] if kernel == "python3" else []
    cells = run_notebook(
        kernel, [*setup, "Mod(2, 4)^-1", "[1, 2][5]"], allow_errors=True
    )
    mod_error, index_error = (c.outputs[0] for c in cells[-2:])
    assert mod_error.evalue == "2 is not invertible modulo 4"
    assert "modular.py" not in "".join(mod_error.traceback)
    assert index_error.ename == "IndexError"


@pytest.mark.parametrize("kernel", ["er2", "python3"])
def test_prelude_survives_reset(jupyter_path, kernel):
    """Quarto runs ``%reset`` before rendering; ER2 must keep working."""
    setup = ["%load_ext er2"] if kernel == "python3" else []
    cells = run_notebook(kernel, [*setup, "%reset -f", "print(2^3, _x^2)"])
    assert text(cells[-1]) == "8 x^2\n"


def test_er2_kernel_preparses_inline_expressions(jupyter_path):
    """Quarto evaluates `{python} expr` through ``user_expressions``."""
    manager, client = start_new_kernel(kernel_name="er2")
    try:
        msg_id = client.execute(
            "sym x", user_expressions={"inline": "latex(x^2 + 1/2)"}
        )
        reply = client.get_shell_msg(timeout=60)
        while reply["parent_header"].get("msg_id") != msg_id:
            reply = client.get_shell_msg(timeout=60)
        inline = reply["content"]["user_expressions"]["inline"]
        assert inline["status"] == "ok", inline
        assert inline["data"]["text/markdown"] == r"$x^{2} + \frac{1}{2}$"
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)


@needs_quarto
def test_quarto_render(jupyter_path, tmp_path):
    doc = tmp_path / "m1.qmd"
    doc.write_text(
        textwrap.dedent(
            """
            ---
            title: "ER2"
            format: gfm
            jupyter: er2
            execute:
              daemon: false
            ---

            ```{python}
            sym x
            print(2^10, 1/3)
            ```

            Inline: `{python} latex(x^2)`.
            """
        ).lstrip()
    )
    env = {**os.environ, "QUARTO_PYTHON": sys.executable}
    result = subprocess.run(
        ["quarto", "render", str(doc)],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr
    rendered = (tmp_path / "m1.md").read_text()
    assert "1024 1/3" in rendered
    assert "Inline: $x^{2}$." in rendered


M2_QMD = """
---
title: "ER2"
jupyter: er2
execute:
  daemon: false
---

```{python}
sym x
f = x^2 + 2*x + 1
print(factor(f))
show(factor(f))
```

Inline: `{python} latex(integrate(f, (x, 0, 1)))`.
"""


@needs_quarto
@pytest.mark.parametrize("fmt", ["html", "pdf"])
def test_quarto_renders_math(jupyter_path, tmp_path, fmt):
    """Symbolic results render as math in Quarto HTML and PDF (M2)."""
    doc = tmp_path / "m2.qmd"
    doc.write_text(M2_QMD.lstrip())
    env = {**os.environ, "QUARTO_PYTHON": sys.executable}
    command = ["quarto", "render", str(doc), "--to", fmt]
    if fmt == "pdf":
        command += ["-M", "keep-tex:true"]
    result = subprocess.run(
        command, capture_output=True, text=True, env=env, timeout=600
    )
    no_tex = "No TeX installation" in result.stderr
    if fmt == "pdf" and no_tex and not os.environ.get("ER2_REQUIRE_QUARTO"):
        pytest.skip("needs a TeX installation")
    assert result.returncode == 0, result.stderr
    if fmt == "html":
        page = (tmp_path / "m2.html").read_text()
        assert "(x + 1)^2" in page
        assert r"\[\left(x + 1\right)^{2}\]" in page
        inline = r'Inline: <span class="math inline">\(\frac{7}{3}\)</span>'
        assert inline in page
    else:
        assert (tmp_path / "m2.pdf").stat().st_size > 0
        tex = (tmp_path / "m2.tex").read_text()
        # Pandoc versions differ: \[...\] or $$...$$, \(...\) or $...$.
        display = r"\left(x + 1\right)^{2}"
        assert rf"\[{display}\]" in tex or f"$${display}$$" in tex
        inline = r"\frac{7}{3}"
        assert rf"Inline: \({inline}\)" in tex or f"Inline: ${inline}$" in tex


EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"
GOLDEN = Path(__file__).resolve().parent.parent / "examples" / "mvp.out"


def mvp_notebook_output(kernel):
    """Execute ``examples/mvp.ipynb``; return its text and LaTeX output."""
    nb = nbformat.read(EXAMPLES / "mvp.ipynb", as_version=4)
    if kernel == "python3":
        nb.cells.insert(0, nbformat.v4.new_code_cell("%load_ext er2"))
    NotebookClient(nb, kernel_name=kernel, timeout=120).execute()
    code = [cell for cell in nb.cells if cell.cell_type == "code"]
    shown = [
        out.data["text/latex"]
        for cell in code
        for out in cell.outputs
        if out.output_type == "display_data"
    ]
    return "".join(text(cell) for cell in code), shown


@pytest.mark.parametrize("kernel", ["er2", "python3"])
def test_mvp_notebook(jupyter_path, kernel):
    """The MVP (M3 acceptance) in Jupyter, through both routes (§1.2)."""
    output, shown = mvp_notebook_output(kernel)
    golden = GOLDEN.read_text().splitlines(keepends=True)
    # In a notebook, show(factor(f)) renders math instead of printing.
    assert output == "".join(golden[:3] + golden[4:])
    assert shown == [r"$$\left(x + 1\right)^{2}$$"]


@needs_quarto
def test_mvp_quarto(jupyter_path, tmp_path):
    """The MVP (M3 acceptance) rendered by Quarto with the er2 kernel."""
    doc = tmp_path / "mvp.qmd"
    shutil.copy(EXAMPLES / "mvp.qmd", doc)
    env = {**os.environ, "QUARTO_PYTHON": sys.executable}
    result = subprocess.run(
        ["quarto", "render", str(doc), "--to", "gfm"]
        + ["-M", "execute.daemon:false"],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr
    rendered = (tmp_path / "mvp.md").read_text()
    for line in GOLDEN.read_text().splitlines():
        if line != "(x + 1)^2":
            assert line in rendered
    assert r"$$\left(x + 1\right)^{2}$$" in rendered
    assert r"$\varphi(123456789) =$ $82260072$" in rendered
    assert r"$\text{True}$." in rendered


ALGEBRA_SOURCE = Path(__file__).resolve().parent.parent / "examples"
ALGEBRA_GOLDEN = ALGEBRA_SOURCE / "algebra.out"


@pytest.mark.parametrize("kernel", ["er2", "python3"])
def test_algebra_notebook(jupyter_path, kernel):
    """The M5 acceptance in Jupyter, through both routes (§1.2)."""
    source = (ALGEBRA_SOURCE / "algebra.er2").read_text()
    cells = [source] if kernel == "er2" else ["%load_ext er2", source]
    executed = run_notebook(kernel, cells)
    assert text(executed[-1]) == ALGEBRA_GOLDEN.read_text()


# The M5 acceptance list (PLAN.md): every item has to show up rendered.
ALGEBRA_LINES = [
    "-144 3",  # det and rank of a matrix over Z
    "x^3 + 8*x^2 - 84*x + 144",  # charpoly
    "Matrix([[2, 0, 0], [0, 6, 0], [0, 0, 12]])",  # smith_form
    "2 Matrix([[1, -2, 1]])",  # rank and kernel
    "GF(9) 9 a^2 + a + 2",  # arithmetic in GF(9)
    "2 8 2 2",  # a^4, order, trace, norm
    # Quarto indents an output block by four spaces in gfm.
    "\n    5\n",  # resultant(x^2+1, x^3-2, x)
    "\n    -31\n",  # discriminant(x^3+x+1)
    "-7 7",  # the sign convention, D16
    "[x - y, 2*y^2 - 1]",  # a lex Groebner basis
    "True False",  # reduce(f, G) == 0, but `f in G` is not that
    "2 -20 2 [2]",  # Q(sqrt(-5)): h = 2
    "[((2, x + 1), 2)]",  # 2 ramifies
    "[((3, x - 1), 1), ((3, x + 1), 1)]",  # 3 splits
]


@needs_quarto
def test_algebra_quarto(jupyter_path, tmp_path):
    """The M5 acceptance rendered by Quarto with the er2 kernel."""
    doc = tmp_path / "algebra.qmd"
    shutil.copy(EXAMPLES / "algebra.qmd", doc)
    env = {**os.environ, "QUARTO_PYTHON": sys.executable}
    result = subprocess.run(
        ["quarto", "render", str(doc), "--to", "gfm"]
        + ["-M", "execute.daemon:false"],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr
    rendered = (tmp_path / "algebra.md").read_text()
    for line in ALGEBRA_LINES:
        assert line in rendered, line
    # A cell ending in an expression renders as math, not as text.
    assert "x^{2} + x + 2" in rendered  # minpoly(a) in GF(9)
    assert "c^{2} - 1" in rendered  # det of a symbolic matrix
    assert r"\mathbb{Q}[x]/\left(x^{2} + 5\right)" in rendered
    # factor(x^8 - x, modulus=2), as math
    assert r"x \left(x + 1\right)" in rendered


# A scientific article (ARCHITECTURE §1.3): numbers the document computed
# and then put into its own prose.  A render that "succeeds" is not enough
# — the figure silently rendered as nothing once, under Agg.
ARTICLE_VALUES = [
    "0.56145948356688516982",  # exp(-EulerGamma) to 20 digits
    "1605264998400",  # the exact product for x = 50, a rational
    "11573306655157",
    "0.138704",  # the same as a decimal
    "78498",  # primepi(10^6), in the prose and the table
    "0.040638",  # the product at 10^6
]


@needs_quarto
@pytest.mark.parametrize("fmt", ["html", "pdf"])
def test_article_renders(jupyter_path, tmp_path, fmt):
    """`examples/article.qmd` renders, with its computed values and figure."""
    for name in ("article.qmd", "article.bib"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    env = {**os.environ, "QUARTO_PYTHON": sys.executable}
    result = subprocess.run(
        ["quarto", "render", str(tmp_path / "article.qmd"), "--to", fmt]
        + ["-M", "execute.daemon:false"],
        capture_output=True,
        text=True,
        env=env,
        timeout=900,
    )
    no_tex = "No TeX installation" in result.stderr
    if fmt == "pdf" and no_tex and not os.environ.get("ER2_REQUIRE_QUARTO"):
        pytest.skip("needs a TeX installation")
    assert result.returncode == 0, result.stderr
    if fmt == "pdf":
        assert (tmp_path / "article.pdf").stat().st_size > 10_000
        return
    page = (tmp_path / "article.html").read_text()
    for value in ARTICLE_VALUES:
        assert value in page, value
    # The figure is a real image, exactly one of them, and Matplotlib did
    # not fall back to a backend that draws nothing.
    figures = sorted((tmp_path / "article_files" / "figure-html").iterdir())
    assert len(figures) == 1 and figures[0].stat().st_size > 1000
    assert page.count("<img") == 1
    assert "non-interactive" not in page
    # Cross-references and the bibliography.
    assert 'id="eq-mertens"' in page or "eq-mertens" in page
    assert 'id="tbl-ratio"' in page
    assert 'id="refs"' in page
