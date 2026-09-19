"""SymPy is loaded only when a program needs it (``er2._lazy``)."""

import subprocess
import sys
import textwrap

ER2 = [sys.executable, "-m", "er2"]


def run(tmp_path, source, name="prog.er2"):
    program = tmp_path / name
    program.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    result = subprocess.run(
        [*ER2, str(program)], capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_importing_er2_does_not_import_sympy():
    code = "import sys, er2, er2.prelude, er2.session; er2.session.start(); "
    code += "print('sympy' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.stdout == "False\n", result.stderr


def test_number_theory_programs_never_load_sympy(tmp_path):
    out = run(
        tmp_path,
        """
        import sys
        print(phi(10^6), factor(360), 1/3, isprime(2^127 - 1))
        print(Mod(3, 7)^-1, factorial(20), divisors(12), latex(1/3))
        print(pari.sum(lambda n: 1/n^2, 1, 4), f"{2^3=}", 7r)
        print("sympy" in sys.modules)
        """,
    )
    assert out.splitlines()[-1] == "False"


def test_symbols_load_sympy_and_er2_printing(tmp_path):
    out = run(
        tmp_path,
        """
        import sys
        print("sympy" in sys.modules)
        sym t
        print(t^2, factor(t^2 - 1), factorial(t))
        """,
    )
    assert out == "False\nt^2 (t - 1)*(t + 1) factorial(t)\n"


def test_prelude_sympy_names_are_there_when_used(tmp_path):
    out = run(tmp_path, "print(pi.evalf(5), _x^2, sin(0))\n")
    assert out == "3.1416 x^2 0\n"


def test_dynamic_name_lookups_get_the_full_prelude(tmp_path):
    out = run(tmp_path, 'print(eval("pi"), globals()["oo"])\n')
    assert out == "pi oo\n"


def test_sympy_imported_by_user_code_prints_in_er2_notation(tmp_path):
    out = run(tmp_path, 'import sympy\nprint(sympy.Symbol("t") ** 2)\n')
    assert out == "t^2\n"


def test_er2_modules_get_the_names_they_use(tmp_path):
    (tmp_path / "helper.er2").write_text(
        "def area(r):\n    return pi * r^2\n", encoding="utf-8"
    )
    out = run(tmp_path, "import helper\nprint(helper.area(2))\n")
    assert out == "4*pi\n"
