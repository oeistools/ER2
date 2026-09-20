"""The ``er2`` command, the REPL and ``.er2`` imports (§3.2)."""

import signal
import subprocess
import sys
import textwrap

import pytest

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
    assert er2("--show-python", program).stdout == "y = x**__er2_int__(2)\n"


def test_repl():
    result = er2(
        stdin="sym x\nx^2 + 1\nfor i in range(2):\n    print(i^2)\n\n"
    )
    assert result.returncode == 0, result.stderr
    assert "x^2 + 1" in result.stdout
    assert "0\n1\n" in result.stdout


def test_version_and_bad_option():
    assert er2("--version").stdout.startswith("er2 ")
    assert er2("--nope").returncode == 2


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

    import er2 as package

    root = Path(__file__).resolve().parent.parent
    project = tomllib.loads((root / "pyproject.toml").read_text())
    version = project["project"]["version"]
    assert package.__version__ == version
    assert f"version: {version}\n" in (root / "CITATION.cff").read_text()
    assert er2("--version").stdout == f"er2 {version}\n"
