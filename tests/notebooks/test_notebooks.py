"""ER2 in Jupyter and Quarto (ARCHITECTURE.md §1.2).

Route A is the ``er2`` kernel; route B is ``%load_ext er2`` in a standard
``python3`` kernel.  The Quarto test is skipped when Quarto is missing.
"""

import os
import shutil
import subprocess
import sys
import textwrap

import nbformat
import pytest
from jupyter_client.manager import start_new_kernel
from nbclient import NotebookClient

from er2.kernel import install_kernel


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


def test_er2_kernel(jupyter_path):
    check_m1_cells(run_notebook("er2", M1_CELLS))


def test_load_ext_in_python_kernel():
    cells = run_notebook("python3", ["%load_ext er2", *M1_CELLS])
    check_m1_cells(cells[1:])


def test_er2_kernel_errors_show_the_er2_source(jupyter_path):
    cells = run_notebook("er2", ["a = 2^3\nb = a / 0"], allow_errors=True)
    error = cells[0].outputs[0]
    assert error.output_type == "error"
    assert error.ename == "ZeroDivisionError"
    traceback = "".join(error.traceback)
    assert "line 2" in traceback
    assert "__er2_int__" not in traceback


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


@pytest.mark.skipif(shutil.which("quarto") is None, reason="needs Quarto")
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
