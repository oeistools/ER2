"""``%load_ext er2`` and ``%unload_ext er2`` undo each other (review A-01)."""

import sys

import pytest

pytest.importorskip("IPython")

from IPython.core.interactiveshell import InteractiveShell  # noqa: E402

from er2 import importer  # noqa: E402
from er2.runtime.numbers import Rational  # noqa: E402
from er2.session import (  # noqa: E402
    _ExactOps,
    load_ipython_extension,
    unload_ipython_extension,
)


def test_load_then_unload_leaves_ipython_as_it_was():
    shell = InteractiveShell.instance()
    try:
        load_ipython_extension(shell)
        shell.run_cell("a = 1/3")
        assert shell.user_ns["a"] == Rational(1, 3)
        assert importer._hook in sys.path_hooks
        assert any(isinstance(t, _ExactOps) for t in shell.ast_transformers)

        unload_ipython_extension(shell)
        shell.run_cell("b = 1/2")
        assert shell.user_ns["b"] == 0.5 and type(shell.user_ns["b"]) is float
        assert importer._hook not in sys.path_hooks
        assert not any(
            isinstance(t, _ExactOps) for t in shell.ast_transformers
        )
    finally:
        unload_ipython_extension(shell)
        InteractiveShell.clear_instance()
