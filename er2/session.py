"""Start and run ER2 sessions: files, the REPL, and IPython (§3.2).

Every entry point goes through ``start()``, which enables what an ER2
session needs (ER2 printing, D11; ``.er2`` imports).  Nothing here runs
on a plain ``import er2``.
"""

import code
import fractions
import linecache
import sys
import traceback
from pathlib import Path

from er2 import importer, prelude, printing
from er2.preparser import IncompleteSourceError, preparse

_PACKAGE_DIR = Path(__file__).resolve().parent
_FRACTIONS = Path(fractions.__file__).resolve()


def start():
    """Enable ER2 printing and ``.er2`` imports in this process."""
    printing.install()
    importer.install()


def run_file(path, argv=()):
    """Run the ER2 program at ``path`` as ``__main__``; return exit code."""
    start()
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    namespace = prelude.inject(
        {
            "__name__": "__main__",
            "__file__": str(path),
            "__builtins__": __builtins__,
        }
    )
    sys.argv = [str(path), *argv]
    try:
        compiled = compile(preparse(source, str(path)), str(path), "exec")
        exec(compiled, namespace)
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - report like Python does
        _print_user_traceback(exc)
        return 1
    return 0


def _print_user_traceback(exc):
    """Print ``exc`` as Python would, hiding ER2's own machinery.

    Frames of the runner (outermost) and of the ER2 runtime (innermost,
    e.g. inside ``Integer.__truediv__``) are dropped.  Column markers are
    removed from ``.er2`` frames: they refer to the preparsed line, whose
    columns differ from the source line shown.
    """
    report = traceback.TracebackException.from_exception(exc)
    for part in _chain(report):
        frames = list(part.stack)
        while frames and frames[0].filename == __file__:
            frames.pop(0)
        while len(frames) > 1 and _is_internal(frames[-1].filename):
            frames.pop()
        for frame in frames:
            if frame.filename.endswith(".er2") or frame.filename.startswith(
                "<"
            ):
                frame.colno = frame.end_colno = None
        part.stack = traceback.StackSummary.from_list(frames)
    print("".join(report.format()), end="", file=sys.stderr)


def _chain(report):
    """Yield ``report`` and the exceptions it was caused by."""
    seen = set()
    while report is not None and id(report) not in seen:
        seen.add(id(report))
        yield report
        report = report.__cause__ or report.__context__


def _is_internal(filename):
    """Return True for files of the ER2 package or of ``fractions``."""
    path = Path(filename).resolve()
    return path.is_relative_to(_PACKAGE_DIR) or path == _FRACTIONS


class ER2Console(code.InteractiveConsole):
    """Python's interactive console with the ER2 preparser."""

    def runsource(self, source, filename="<input>", symbol="single"):
        """Preparse ``source``; return True while more input is needed."""
        try:
            python = preparse(source, filename)
        except IncompleteSourceError:
            return True
        except SyntaxError:
            # Let Python compile the raw source to report the error.
            python = source
        return super().runsource(python, filename, symbol)


def repl():
    """Run the interactive ER2 console."""
    start()
    console = ER2Console(prelude.inject({"__name__": "__main__"}))
    banner = (
        f"ER2 on Python {sys.version.split()[0]}. "
        "'^' is power, '^^' is XOR. Type exit() to quit."
    )
    console.interact(banner=banner, exitmsg="")


def transform_cell(lines):
    """IPython input transformer: preparse a cell given as ``lines``."""
    source = "".join(lines)
    try:
        python = preparse(source)
    except SyntaxError:
        # Let IPython report incomplete or invalid input itself.
        return lines
    return python.splitlines(keepends=True)


def load_ipython_extension(shell):
    """Enable ER2 in an IPython shell (``%load_ext er2``)."""
    start()
    if transform_cell not in shell.input_transformers_post:
        shell.input_transformers_post.append(transform_cell)
    prelude.inject(shell.user_ns)
    # ``%reset`` (Quarto runs it before every render) clears the user
    # namespace; restore the prelude before each cell.
    if _restore_prelude not in shell.events.callbacks["pre_run_cell"]:
        shell.events.register("pre_run_cell", _restore_prelude)
    _show_er2_source_in_tracebacks(shell)
    shell.set_custom_exc((Exception,), _hide_internal_frames)


def _hide_internal_frames(shell, etype, value, tb, tb_offset=None):
    """Show a notebook traceback without ER2's innermost frames.

    As in the CLI, frames of the ER2 runtime at the end of the traceback
    (such as ``Integer.__truediv__`` raising ``ZeroDivisionError``) are
    implementation details: the error belongs to the user's line.
    """
    frames = []
    current = tb
    while current is not None:
        frames.append(current)
        current = current.tb_next
    while len(frames) > 1 and _is_internal(
        frames[-1].tb_frame.f_code.co_filename
    ):
        frames.pop()
    if frames:
        frames[-1].tb_next = None
    shell.showtraceback((etype, value, tb), tb_offset=tb_offset)


def unload_ipython_extension(shell):
    """Disable ER2 in an IPython shell (``%unload_ext er2``)."""
    if transform_cell in shell.input_transformers_post:
        shell.input_transformers_post.remove(transform_cell)
    if _restore_prelude in shell.events.callbacks["pre_run_cell"]:
        shell.events.unregister("pre_run_cell", _restore_prelude)
    shell.compile.__dict__.pop("cache", None)
    shell.set_custom_exc((), None)
    printing.uninstall()


def _restore_prelude(info=None):
    """Re-inject the prelude into the active IPython namespace."""
    from IPython import get_ipython

    shell = get_ipython()
    if shell is not None:
        prelude.inject(shell.user_ns)


def _show_er2_source_in_tracebacks(shell):
    """Make IPython tracebacks show the ER2 cell, not the preparsed one.

    IPython caches the transformed cell for tracebacks.  The preparser
    keeps line numbers, so the raw cell's lines can replace it one to one.
    """
    compiler = shell.compile
    if "cache" in compiler.__dict__:
        return
    original = type(compiler).cache.__get__(compiler)

    def cache(transformed_code, number=0, raw_code=None):
        name = original(transformed_code, number, raw_code)
        if raw_code is not None:
            raw = [line + "\n" for line in raw_code.splitlines()]
            size, mtime, lines, filename = linecache.cache[name]
            if len(raw) == len(lines):
                linecache.cache[name] = (size, mtime, raw, filename)
        return name

    compiler.cache = cache
