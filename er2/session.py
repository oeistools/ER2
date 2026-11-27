"""Start and run ER2 sessions: files, the REPL, and IPython (§3.2).

Every entry point goes through ``start()``, which enables what an ER2
session needs (ER2 printing, D11; ``.er2`` imports).  Nothing here runs
on a plain ``import er2``.
"""

from __future__ import annotations

import fractions
import linecache
import os
import re
import signal
import sys
from pathlib import Path

from er2 import _lazy, importer, prelude, printing
from er2.preparser import (
    IncompleteSourceError,
    _ExactOps,
    compile_er2,
    preparse,
)

TYPE_CHECKING = False
if TYPE_CHECKING:  # annotations only: ``typing`` costs startup
    from collections.abc import Iterable
    from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
_FRACTIONS = Path(fractions.__file__).resolve()


def start() -> None:
    """Enable ER2 printing and ``.er2`` imports in this process."""
    printing.install()
    importer.install()


def run_file(path: str | os.PathLike[str], argv: Iterable[str] = ()) -> int:
    """Run the ER2 program at ``path`` as ``__main__``; return exit code."""
    start()
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    namespace = {
        "__name__": "__main__",
        "__file__": str(path),
        "__builtins__": __builtins__,
    }
    sys.argv = [str(path), *argv]
    # Like ``python script.py``: the script's directory comes first on
    # sys.path, so modules next to it can be imported.
    sys.path[0:1] = [str(Path(path).resolve().parent)]
    try:
        compiled = compile_er2(_preparse_file(source, path), str(path), "exec")
        prelude.inject(namespace, compiled)
        exec(compiled, namespace)
    except SystemExit:
        raise
    except KeyboardInterrupt as exc:
        # Ctrl-C interrupts a long computation (D7); without this branch
        # it would look like any other error, exit code 1.
        _print_user_traceback(exc)
        return _die_from_sigint()
    except BaseException as exc:  # noqa: BLE001 - report like Python does
        _print_user_traceback(exc)
        return 1
    return 0


def _preparse_file(source, path):
    """Preparse a whole program, with Python's message if it is cut short.

    The tokenizer only says "unexpected EOF" at the last line; Python's
    own compiler says which bracket or string was left open, and where:
    "'(' was never closed" on the line of the bracket.
    """
    try:
        return preparse(source, str(path))
    except IncompleteSourceError as incomplete:
        try:
            compile(source, str(path), "exec", dont_inherit=True)
        except SyntaxError as error:
            text = str(error.msg)
            if "never closed" in text or "unterminated" in text:
                raise error from None
        raise incomplete from None


def _die_from_sigint():
    """End the process as CPython does after an uncaught Ctrl-C.

    CPython restores the default SIGINT handler and re-sends the signal,
    so the process is *killed by* SIGINT instead of exiting normally: a
    shell reports 130, and a parent sees ``WIFSIGNALED``, which is how
    it tells "the user interrupted this" from "the program failed".
    Windows cannot signal itself this way; there the code is returned.
    """
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
    return 128 + signal.SIGINT


def _print_user_traceback(exc):
    """Print ``exc`` as Python would, hiding ER2's own machinery."""
    print(_format_user_traceback(exc), end="", file=sys.stderr)


def _format_user_traceback(exc):
    """Return the report of ``exc`` as Python would, without ER2's machinery.

    Frames of the runner (outermost) are dropped, and so is everything
    after the user's last frame: ER2's runtime and the libraries under it
    (SymPy, cypari2, the standard library), whose frames say how ER2
    computes, not where the program went wrong; the backend is not
    observable (ARCHITECTURE §3).  A syntax error in the program shows no
    frames at all, as ``python file.py`` does.  Column markers are removed
    from ``.er2`` frames: they refer to the preparsed line, whose columns
    differ from the source line shown.
    """
    import traceback  # only when there is an error to show

    if not _LIBRARY_DIRS:
        _LIBRARY_DIRS.extend(_library_dirs())
    report = traceback.TracebackException.from_exception(exc)
    for part in _chain(report):
        frames = list(part.stack)
        while frames and frames[0].filename == __file__:
            frames.pop(0)
        if issubclass(part.exc_type or object, SyntaxError) and (
            part.filename or ""
        ).endswith(".er2"):
            frames = []
        user = [i for i, f in enumerate(frames) if _is_user(f.filename)]
        if user:
            # the REPL's own frame (``code.py``) comes before the user's
            del frames[user[-1] + 1 :]
            del frames[: user[0]]
        while len(frames) > 1 and _is_internal(frames[-1].filename):
            frames.pop()
        for frame in frames:
            if frame.filename.endswith(".er2") or frame.filename.startswith(
                "<"
            ):
                frame.colno = frame.end_colno = None
        part.stack = traceback.StackSummary.from_list(frames)
    return "".join(report.format())


def _chain(report):
    """Yield ``report`` and the exceptions it was caused by."""
    seen = set()
    while report is not None and id(report) not in seen:
        seen.add(id(report))
        yield report
        report = report.__cause__ or report.__context__


def _is_user(filename):
    """Return True for the user's code: not ER2, a library or stdlib."""
    if filename.endswith(".er2") or filename.startswith("<"):
        return True
    path = Path(filename)
    if not path.is_absolute() or not path.exists():
        return False  # e.g. cypari2's "cypari2/auto_instance.pxi"
    if _is_internal(filename):
        return False
    return not any(path.resolve().is_relative_to(d) for d in _LIBRARY_DIRS)


def _library_dirs():
    """Return the standard library and site-packages directories."""
    import sysconfig

    names = ("stdlib", "platstdlib", "purelib", "platlib")
    paths = {sysconfig.get_path(name) for name in names}
    return [Path(p).resolve() for p in paths if p]


_LIBRARY_DIRS = []


def _is_internal(filename):
    """Return True for files of the ER2 package or of ``fractions``."""
    path = Path(filename).resolve()
    return path.is_relative_to(_PACKAGE_DIR) or path == _FRACTIONS


def _console_class():
    """Return the ER2 console class, importing ``code`` only now.

    ``code`` and ``codeop`` cost about 15 ms to import and only the REPL
    needs them, so a program run with ``er2 file.er2`` does not pay.
    """
    import code
    import codeop

    class _ExactCommandCompiler(codeop.CommandCompiler):
        """The console's compiler, with exact ``/`` and ``**``."""

        def __call__(self, source, filename="<input>", symbol="single"):
            """Return None while incomplete, else the exact code object."""
            if super().__call__(source, filename, symbol) is None:
                return None
            return compile_er2(source, filename, symbol)

    class ER2Console(code.InteractiveConsole):
        """Python's interactive console with the ER2 preparser."""

        def __init__(self, *args, **kwargs):
            """Use the compiler with exact ``/`` and ``**``."""
            super().__init__(*args, **kwargs)
            self.compile = _ExactCommandCompiler()

        def runsource(self, source, filename="<input>", symbol="single"):
            """Preparse ``source``; return True while more input is needed."""
            if _show_help(source, self.locals, sys.stdout.write):
                return False
            try:
                python = preparse(source, filename)
            except IncompleteSourceError:
                return True
            except SyntaxError:
                # Let Python compile the raw source to report the error.
                python = source
            return super().runsource(python, filename, symbol)

        def showtraceback(self):
            """Show the error as ``er2 file.er2`` does: no ER2 frames."""
            exc = sys.exc_info()[1]
            sys.last_exc = exc
            self.write(_format_user_traceback(exc))

    return ER2Console


_HELP = re.compile(r"\s*([A-Za-z_][\w.]*)\s*\?\s*")


def _show_help(source, namespace, write):
    """Write the help of ``name`` for a REPL line ``name?``; True if so.

    Only the REPL reads ``?``, as IPython does; it is not ER2 syntax and
    an ``.er2`` file never sees it.  A name that does not resolve gives
    a short message rather than a traceback.
    """
    match = _HELP.fullmatch(source)
    if match is None:
        return False
    import inspect  # only when help is asked for

    name = match.group(1)
    head, *rest = name.split(".")
    try:
        obj = namespace[head] if head in namespace else eval(head, namespace)
        for part in rest:
            obj = getattr(obj, part)
    except Exception:  # noqa: BLE001 - any failure means "no such name"
        write(f"{name}: not defined\n")
        return True
    try:
        signature = f"{name}{inspect.signature(obj)}"
    except (TypeError, ValueError):
        signature = f"{name}: {type(obj).__name__}"
    doc = inspect.getdoc(obj) or "(no documentation)"
    write(f"{signature}\n\n{doc}\n")
    return True


def history_path() -> Path:
    """Return the REPL history file: ``$XDG_STATE_HOME/er2/history``."""
    state = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return Path(state) / "er2" / "history"


def _line_editing(namespace, path):
    """Turn on readline: history in ``path`` and Tab completion.

    Returns the function that saves the history, or None when readline
    is not available (Windows without it, or a stripped build).
    """
    try:
        import readline
        import rlcompleter
    except ImportError:
        return None
    readline.set_completer(rlcompleter.Completer(namespace).complete)
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")  # macOS
    else:
        readline.parse_and_bind("tab: complete")
    readline.set_history_length(1000)
    try:
        readline.read_history_file(path)
    except OSError:
        pass  # first session, or unreadable: start empty

    def save():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(path)
        except OSError:
            pass  # a read-only home must not break leaving the REPL

    return save


def repl() -> None:
    """Run the interactive ER2 console."""
    start()
    _lazy.preload()
    namespace = prelude.inject({"__name__": "__main__"})
    console = _console_class()(namespace)
    save = (
        _line_editing(namespace, history_path())
        if sys.stdin.isatty()
        else None
    )
    banner = (
        f"ER2 on Python {sys.version.split()[0]}. "
        "'^' is power, '^^' is XOR. 'name?' shows help. Type exit() to quit."
    )
    try:
        console.interact(banner=banner, exitmsg="")
    finally:
        if save is not None:
            save()


def transform_cell(lines: list[str]) -> list[str]:
    """IPython input transformer: preparse a cell given as ``lines``."""
    source = "".join(lines)
    try:
        python = preparse(source)
    except SyntaxError:
        # Let IPython report incomplete or invalid input itself.
        return lines
    return python.splitlines(keepends=True)


def load_ipython_extension(shell: Any) -> None:
    """Enable ER2 in an IPython shell (``%load_ext er2``)."""
    start()
    if transform_cell not in shell.input_transformers_post:
        shell.input_transformers_post.append(transform_cell)
    if not any(isinstance(t, _ExactOps) for t in shell.ast_transformers):
        shell.ast_transformers.append(_ExactOps())
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


def unload_ipython_extension(shell: Any) -> None:
    """Disable ER2 in an IPython shell (``%unload_ext er2``)."""
    if transform_cell in shell.input_transformers_post:
        shell.input_transformers_post.remove(transform_cell)
    if _restore_prelude in shell.events.callbacks["pre_run_cell"]:
        shell.events.unregister("pre_run_cell", _restore_prelude)
    shell.compile.__dict__.pop("cache", None)
    shell.set_custom_exc((), None)
    # undo all of load_ipython_extension (review A-01): the exact ``/``
    # and ``**`` pass (D22) and the ``.er2`` importer too
    shell.ast_transformers[:] = [
        t for t in shell.ast_transformers if not isinstance(t, _ExactOps)
    ]
    importer.uninstall()
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
