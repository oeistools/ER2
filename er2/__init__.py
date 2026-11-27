"""ER2 — mathematical Python.

Importing ``er2`` from Python has no side effects; ER2 printing and
``.er2`` imports are enabled only by the ER2 entry points (the ``er2``
command, the ER2 kernel, ``%load_ext er2``) or explicitly with
``er2.session.start()``.
"""

from __future__ import annotations

from er2.preparser import preparse
from er2.printing import latex, show
from er2.runtime.numbers import Integer, Rational

TYPE_CHECKING = False
if TYPE_CHECKING:  # annotations only: ``typing`` costs startup
    from typing import Any

__all__ = ["Integer", "Rational", "latex", "preparse", "show"]


def load_ipython_extension(shell: Any) -> None:
    """Enable ER2 in IPython: ``%load_ext er2``."""
    from er2.session import load_ipython_extension

    load_ipython_extension(shell)


def unload_ipython_extension(shell: Any) -> None:
    """Disable ER2 in IPython: ``%unload_ext er2``."""
    from er2.session import unload_ipython_extension

    unload_ipython_extension(shell)


def __getattr__(name: str) -> str:
    """Compute ``__version__`` when asked for (PEP 562).

    ``importlib.metadata`` costs about 35 ms to import, a quarter of
    the start of an ER2 program, and only ``--version``, ``--info`` and
    the kernel need the version.
    """
    if name == "__version__":
        from importlib.metadata import PackageNotFoundError, version

        try:
            value = version("er2")  # single source: pyproject.toml
        except PackageNotFoundError:  # a source tree, not installed
            value = "0+unknown"
        globals()["__version__"] = value
        return value
    raise AttributeError(f"module 'er2' has no attribute {name!r}")
