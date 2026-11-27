"""The ``er2`` command, the REPL and ``.er2`` imports (§3.2)."""

import signal
import subprocess
import sys
import textwrap

import pytest

from er2 import __version__ as er2_version
from er2 import importer

ER2 = [sys.executable, "-m", "er2"]


def er2(*args, stdin=None, cwd=None):
    """Run the ``er2`` command; return the completed process."""
    return subprocess.run(
        [*ER2, *map(str, args)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=120,
    )


def write(path, source):
    path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    return path


def test_m1_acceptance_program(tmp_path):
    program = write(
        tmp_path / "m1.er2",
        """
        sym x
        print(2^10)
        print(1/3)
        print(5 ^^ 3)
        print(x^2 + 1)
        print(latex(1/3))
        """,
    )
    result = er2(program)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "1024\n1/3\n6\nx^2 + 1\n\\frac{1}{3}\n"


def test_m2_acceptance_program(tmp_path):
    """The first half of the MVP (ARCHITECTURE.md §5)."""
    program = write(
        tmp_path / "m2.er2",
        """
        sym x
        f = x^2 + 2*x + 1
        print(f)
        print(expand(f))
        print(factor(f))
        show(factor(f))
        print(latex(f))
        print(integrate(f, (x, 0, 1)), solve(x^2 - 4, x))
        print(series(sin(x), x, 0, 6))
        """,
    )
    result = er2(program)
    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "x^2 + 2*x + 1\n"
        "x^2 + 2*x + 1\n"
        "(x + 1)^2\n"
        "(x + 1)^2\n"
        "x^{2} + 2 x + 1\n"
        "7/3 [-2, 2]\n"
        "x - x^3/6 + x^5/120 + O(x^6)\n"
    )


def test_script_arguments_and_main(tmp_path):
    program = write(
        tmp_path / "args.er2",
        """
        import sys
        if __name__ == "__main__":
            print(sys.argv[1:], __file__.endswith("args.er2"))
        """,
    )
    assert er2(program, "a", "b").stdout == "['a', 'b'] True\n"


def test_errors_report_the_er2_line(tmp_path):
    program = write(
        tmp_path / "boom.er2",
        """
        def f(n):
            return n / 0

        print(f(2^3))
        """,
    )
    result = er2(program)
    assert result.returncode == 1
    assert 'boom.er2", line 2, in f' in result.stderr
    assert 'boom.er2", line 4, in <module>' in result.stderr
    assert result.stderr.rstrip().endswith(
        "ZeroDivisionError: division by zero"
    )
    assert "numbers.py" not in result.stderr
    assert "session.py" not in result.stderr


@pytest.mark.parametrize(
    ("source", "expected", "line"),
    [
        ("y = (2 + 3\nprint(y)\n", "SyntaxError: '(' was never closed", 1),
        ('s = """abc\nprint(1)\n', "unterminated triple-quoted", 1),
        ("n = 5\nif n > 2\n    print(n^2)\n", "SyntaxError: expected ':'", 2),
        ("print(phi(2^10, 3))\n", "TypeError: phi() takes exactly 1", 1),
        (
            "sym x\nprint(factor(x^2 - 1, modulus=4))\n",
            "ValueError: modulus=4 is not a prime",
            2,
        ),
    ],
)
def test_error_messages_show_only_the_program(
    tmp_path, source, expected, line
):
    """Backlog 7: the user's line and a clear message, no ER2 internals."""
    program = tmp_path / "bad.er2"
    program.write_text(source, encoding="utf-8")
    result = er2(program)
    assert result.returncode == 1
    assert f'bad.er2", line {line}' in result.stderr
    assert expected in result.stderr
    for internal in ("preparser.py", "ast.py", "dispatch.py", "sympy", "pxi"):
        assert internal not in result.stderr


def test_exit_codes_match_python(tmp_path):
    """``er2 f.er2`` exits as ``python f.py`` does (D7: Ctrl-C).

    An interrupted program must be distinguishable from a failed one:
    shells read 128 + SIGINT as "interrupted".
    """
    sources = {
        "interrupted": "raise KeyboardInterrupt\n",
        "failed": "raise ValueError('boom')\n",
        "exited": "import sys\nsys.exit(3)\n",
    }
    expected = {}
    for name, source in sources.items():
        script = write(tmp_path / f"{name}.py", source)
        expected[name] = subprocess.run(
            [sys.executable, str(script)], capture_output=True, timeout=120
        ).returncode
    # Python is *killed by* SIGINT rather than exiting: ``subprocess``
    # reports that as a negative code, and a shell shows it as 130.
    assert expected["interrupted"] == -signal.SIGINT
    for name, source in sources.items():
        program = write(tmp_path / f"{name}.er2", source)
        assert er2(program).returncode == expected[name], name


def test_show_python(tmp_path):
    program = write(tmp_path / "p.er2", "y = x^2\n")
    assert er2("--show-python", program).stdout == "y = x**2\n"


def test_repl():
    result = er2(
        stdin="sym x\nx^2 + 1\nfor i in range(2):\n    print(i^2)\n\n"
    )
    assert result.returncode == 0, result.stderr
    assert "x^2 + 1" in result.stdout
    assert "0\n1\n" in result.stdout


def test_repl_errors_show_only_the_input():
    result = er2(
        stdin="print(phi(2^10, 3))\ndef f(n):\n    return n/0\n\nf(2)\n"
    )
    assert 'File "<console>", line 2, in f' in result.stderr
    assert "TypeError: phi() takes exactly 1" in result.stderr
    for internal in ("code.py", "dispatch.py", "numbers.py", "pari_backend"):
        assert internal not in result.stderr


def test_repl_help_with_a_question_mark():
    result = er2(stdin="factor?\npari.zeta?\nnot_a_name?\nprint(2^3)\n")
    assert result.returncode == 0, result.stderr
    assert "factor(obj, *args, **kwargs)" in result.stdout
    assert "Factor an integer" in result.stdout
    assert "Riemann zeta function" in result.stdout
    assert "not_a_name: not defined" in result.stdout
    assert "8" in result.stdout


def test_history_path_follows_xdg(monkeypatch, tmp_path):
    from er2 import session

    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert session.history_path() == tmp_path / "er2" / "history"
    monkeypatch.delenv("XDG_STATE_HOME")
    assert session.history_path().parts[-4:] == (
        ".local",
        "state",
        "er2",
        "history",
    )


@pytest.mark.skipif(sys.platform == "win32", reason="needs a terminal (pty)")
def test_repl_in_a_terminal_keeps_its_history(tmp_path):
    """With a real terminal, readline is on and the history is saved."""
    import os
    import pty

    env = dict(os.environ, XDG_STATE_HOME=str(tmp_path))
    pid, fd = pty.fork()
    if pid == 0:  # the child: the REPL, on the terminal
        os.execvpe(ER2[0], ER2, env)
    output = b""
    try:
        for line in (b"x = 2^5\r", b"print(x)\r", b"exit()\r"):
            os.write(fd, line)
        while True:
            try:
                chunk = os.read(fd, 1024)
            except OSError:  # the REPL has exited
                break
            if not chunk:
                break
            output += chunk
    finally:
        os.waitpid(pid, 0)
    assert b"32" in output
    history = (tmp_path / "er2" / "history").read_text()
    # libedit (python-build-standalone, macOS) writes spaces as \\040
    history = history.replace("\\040", " ")
    assert "x = 2^5" in history and "print(x)" in history


def test_version_and_bad_option():
    assert er2("--version").stdout.startswith("er2 ")
    assert er2("--nope").returncode == 2


def test_info_lists_the_versions():
    """``er2 --info``: one line per component, ER2's version first."""
    out = er2("--info").stdout.splitlines()
    assert out[0].split() == ["er2", er2_version]
    names = [line.split()[0] for line in out]
    assert names == [
        "er2",
        "Python",
        "platform",
        "SymPy",
        "cypari2",
        "libpari",
    ]
    libpari = out[-1].split()[1]
    assert all(part.isdigit() for part in libpari.split("."))


def test_info_does_not_load_sympy():
    """SymPy's version comes from its metadata, not from importing it."""
    code = (
        "import sys; from er2.__main__ import main; main(['--info']); "
        "print('sympy' in sys.modules)"
    )
    run = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert run.stdout.splitlines()[-1] == "False"


@pytest.fixture
def er2_imports(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(tmp_path))
    importer.install()
    yield tmp_path
    importer.uninstall()
    for name in ("mathmod", "pkg", "pkg.sub", "shadow"):
        sys.modules.pop(name, None)


def test_import_er2_module(er2_imports):
    write(er2_imports / "mathmod.er2", "sym t\nsquare = t^2\nthird = 1/3\n")
    import mathmod

    assert str(mathmod.third) == "1/3"
    assert mathmod.square.exp == 2


def test_import_er2_package(er2_imports):
    (er2_imports / "pkg").mkdir()
    write(er2_imports / "pkg" / "__init__.er2", "value = 2^5\n")
    write(
        er2_imports / "pkg" / "sub.er2",
        "from pkg import value\ndouble = 2*value\n",
    )
    import pkg.sub

    assert pkg.value == 32 and pkg.sub.double == 64


def test_python_module_wins_over_er2(er2_imports):
    write(er2_imports / "shadow.py", "origin = 'py'\n")
    write(er2_imports / "shadow.er2", "origin = 'er2'\n")
    import shadow

    assert shadow.origin == "py"


def test_version_is_the_same_everywhere():
    """pyproject.toml is the single source; CITATION.cff must match."""
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    project = tomllib.loads((root / "pyproject.toml").read_text())
    version = project["project"]["version"]
    assert er2_version == version
    assert f"version: {version}\n" in (root / "CITATION.cff").read_text()
    assert er2("--version").stdout == f"er2 {version}\n"
