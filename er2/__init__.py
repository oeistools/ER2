"""ER2 — mathematical Python.

Importing ``er2`` from Python has no side effects; ER2 printing and
``.er2`` imports are enabled only by the ER2 entry points (the ``er2``
command, the ER2 kernel, ``%load_ext er2``) or explicitly with
``er2.session.start()``.
"""

from importlib.metadata import PackageNotFoundError, version

from er2.preparser import preparse
from er2.printing import latex, show
from er2.runtime.numbers import Integer, Rational

try:
    __version__ = version("er2")  # single source: pyproject.toml
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0+unknown"
__all__ = ["Integer", "Rational", "latex", "preparse", "show"]


def load_ipython_extension(shell):
    """Enable ER2 in IPython: ``%load_ext er2``."""
    from er2.session import load_ipython_extension

    load_ipython_extension(shell)


def unload_ipython_extension(shell):
    """Disable ER2 in IPython: ``%unload_ext er2``."""
    from er2.session import unload_ipython_extension

    unload_ipython_extension(shell)
