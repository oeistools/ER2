"""Import ``.er2`` modules with the normal ``import`` statement (§3.2).

``install()`` adds a ``FileFinder`` path hook that knows Python's own
file types *and* ``.er2``, listed last.  Python's suffixes are checked
first, so a ``.py`` module always wins over an ``.er2`` module with the
same name, and a directory with ``__init__.er2`` is a regular package.
Python's default hook stays in place, after the ER2 one.
"""

import importlib.machinery as machinery
import sys

from er2 import prelude
from er2.preparser import preparse

SUFFIX = ".er2"


class ER2Loader(machinery.SourceFileLoader):
    """Load a module by preparsing and executing its ``.er2`` source.

    No bytecode is cached, so a newer ER2 preparser always takes effect.
    """

    def exec_module(self, module):
        """Execute the module with the ER2 prelude in its namespace."""
        code = self.get_code(module.__name__)
        prelude.inject(module.__dict__, code)
        exec(code, module.__dict__)

    def get_code(self, fullname):
        """Return the code object compiled from the preparsed source."""
        path = self.get_filename(fullname)
        source = self.get_data(path).decode("utf-8")
        return compile(preparse(source, path), path, "exec", dont_inherit=True)


def _loader_details():
    """Return Python's (loader, suffixes) pairs followed by ER2's."""
    return [
        (machinery.ExtensionFileLoader, machinery.EXTENSION_SUFFIXES),
        (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES),
        (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES),
        (ER2Loader, [SUFFIX]),
    ]


_hook = machinery.FileFinder.path_hook(*_loader_details())


def install():
    """Enable ``.er2`` imports (idempotent)."""
    if _hook in sys.path_hooks:
        return
    position = next(
        (
            i
            for i, hook in enumerate(sys.path_hooks)
            if "FileFinder" in getattr(hook, "__qualname__", "")
        ),
        len(sys.path_hooks),
    )
    sys.path_hooks.insert(position, _hook)
    sys.path_importer_cache.clear()


def uninstall():
    """Disable ``.er2`` imports."""
    if _hook in sys.path_hooks:
        sys.path_hooks.remove(_hook)
        sys.path_importer_cache.clear()
