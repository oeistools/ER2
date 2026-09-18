"""The ``er2`` command.

Usage::

    er2                          start the interactive console
    er2 FILE.er2 [ARGS...]       run an ER2 program
    er2 --show-python FILE.er2   print the Python generated for FILE
    er2 kernel install [--user | --sys-prefix | --prefix DIR]
                                 install the ER2 Jupyter kernel
    er2 --version
"""

import sys

import er2

USAGE = __doc__.split("Usage::", 1)[1].rstrip()


def main(argv=None):
    """Run the ``er2`` command; return the exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        from er2.session import repl

        repl()
        return 0
    first = args[0]
    if first in ("-h", "--help"):
        print(f"usage:{USAGE}")
        return 0
    if first == "--version":
        print(f"er2 {er2.__version__}")
        return 0
    if first == "--show-python":
        return _show_python(args[1:])
    if first == "kernel":
        return _kernel(args[1:])
    if first.startswith("-"):
        print(f"er2: unknown option {first}\nusage:{USAGE}", file=sys.stderr)
        return 2
    from er2.session import run_file

    return run_file(first, args[1:])


def _show_python(args):
    """Print the Python translation of an ER2 file."""
    if len(args) != 1:
        print("usage: er2 --show-python FILE.er2", file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8") as fh:
        print(er2.preparse(fh.read(), args[0]), end="")
    return 0


def _kernel(args):
    """Handle ``er2 kernel install [...]``."""
    if not args or args[0] != "install":
        print(
            "usage: er2 kernel install [--user | --sys-prefix | --prefix DIR]",
            file=sys.stderr,
        )
        return 2
    options = args[1:]
    user, prefix = True, None
    if "--sys-prefix" in options:
        user, prefix = False, sys.prefix
    elif "--prefix" in options:
        index = options.index("--prefix")
        if index + 1 >= len(options):
            print("er2: --prefix needs a directory", file=sys.stderr)
            return 2
        user, prefix = False, options[index + 1]
    try:
        from er2.kernel import install_kernel
    except ImportError as exc:
        print(f"er2: {exc}", file=sys.stderr)
        return 1
    path = install_kernel(user=user, prefix=prefix)
    print(f"Installed the ER2 kernel in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
