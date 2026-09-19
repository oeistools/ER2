"""The ER2 Jupyter kernel (ARCHITECTURE.md §1.2, D9).

An IPython kernel with ER2 enabled.  Besides cells, it also preparses
``user_expressions``, which is how Quarto evaluates inline code such as
`` `{python} latex(x^2)` ``.  Requires the ``er2[jupyter]`` extra.

Install the kernelspec with ``er2 kernel install``; run the kernel with
``python -m er2.kernel -f <connection file>``.
"""

import json
import sys
import tempfile
from pathlib import Path

try:
    from ipykernel.ipkernel import IPythonKernel
except ImportError as exc:  # pragma: no cover - depends on the extra
    raise ImportError(
        "the ER2 kernel needs ipykernel: install 'er2[jupyter]'"
    ) from exc

import er2
from er2 import session
from er2.preparser import preparse

KERNEL_NAME = "er2"
DISPLAY_NAME = "ER2"


class ER2Kernel(IPythonKernel):
    """IPython kernel that runs ER2 code."""

    implementation = "er2"
    implementation_version = er2.__version__
    # D9: declare Python, so Quarto cells are ```{python} and editors
    # highlight ER2 as the Python superset it is.
    language_info = {
        **IPythonKernel.language_info,
        "file_extension": ".er2",
    }
    banner = "ER2 — mathematical Python"

    def __init__(self, **kwargs):
        """Start the kernel and enable ER2 in its shell."""
        super().__init__(**kwargs)
        session.load_ipython_extension(self.shell)

    async def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
        **kwargs,
    ):
        """Execute a cell; also preparse inline ``user_expressions``."""
        if user_expressions:
            user_expressions = {
                key: _preparse_expression(expr)
                for key, expr in user_expressions.items()
            }
        return await super().do_execute(
            code,
            silent,
            store_history,
            user_expressions,
            allow_stdin,
            **kwargs,
        )


def _preparse_expression(expr):
    """Preparse one inline expression; leave it as is if it fails."""
    try:
        return preparse(expr).strip()
    except SyntaxError:
        return expr


def install_kernel(user=True, prefix=None, name=KERNEL_NAME):
    """Install the ER2 kernelspec; return the directory it went to."""
    from jupyter_client.kernelspec import KernelSpecManager

    spec = {
        "argv": [
            sys.executable,
            "-m",
            "er2.kernel",
            "-f",
            "{connection_file}",
        ],
        "display_name": DISPLAY_NAME,
        "language": "python",
        "metadata": {"debugger": True},
    }
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "kernel.json").write_text(json.dumps(spec, indent=2))
        return KernelSpecManager().install_kernel_spec(
            tmp, kernel_name=name, user=user, prefix=prefix
        )


def main():
    """Launch the kernel (called by Jupyter through the kernelspec)."""
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=ER2Kernel)


if __name__ == "__main__":
    main()
