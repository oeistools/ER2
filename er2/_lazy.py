"""Load SymPy only when it is needed.

Importing SymPy takes about 0.3 s, most of an ER2 program's startup.  A
program that only uses numbers and PARI never needs it, so ER2 modules
never import it at module level; they call ``sympy()`` when they need it.

``sympy_loaded()`` is True once SymPy has been imported by anyone, ER2 or
user code.  Until then no object can be a SymPy object, so type checks
can skip it (``is_sympy``, ``is_symbolic``).  ``when_sympy_loaded(hook)``
runs ``hook`` as soon as SymPy is imported (ER2's printer is installed
this way, D11).
"""

import importlib.abc
import importlib.machinery
import sys

_hooks = []


def sympy_loaded():
    """Whether SymPy has been imported (by ER2 or by user code)."""
    module = sys.modules.get("sympy")
    return module is not None and hasattr(module, "Basic")


def is_symbolic(obj):
    """Whether ``obj`` is a SymPy object other than a plain number."""
    if not sympy_loaded():
        return False  # no SymPy object can exist yet
    return isinstance(obj, sys.modules["sympy"].Basic) and not obj.is_Number


def is_sympy(obj):
    """Whether ``obj`` is a SymPy object (always False before SymPy loads)."""
    return sympy_loaded() and isinstance(obj, sys.modules["sympy"].Basic)


def sympy():
    """Import SymPy (if needed) and return the module."""
    import sympy as module

    _run_hooks()
    return module


def when_sympy_loaded(hook):
    """Run ``hook()`` now if SymPy is loaded, else right after it loads."""
    if sympy_loaded():
        hook()
        return
    if hook not in _hooks:
        _hooks.append(hook)
    if not any(isinstance(f, _SympyFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _SympyFinder())


def cancel(hook):
    """Forget a hook registered with ``when_sympy_loaded``."""
    if hook in _hooks:
        _hooks.remove(hook)


def _run_hooks():
    while _hooks:
        _hooks.pop(0)()


class _SympyFinder(importlib.abc.MetaPathFinder):
    """Run the hooks after ``import sympy``, whoever imports it."""

    def find_spec(self, name, path=None, target=None):
        """Wrap the loader of the top-level ``sympy`` package."""
        if name != "sympy":
            return None
        sys.meta_path.remove(self)
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None or spec.loader is None:
            return spec
        loader = spec.loader
        original = loader.exec_module

        def exec_module(module):
            original(module)
            _run_hooks()

        loader.exec_module = exec_module
        return spec
