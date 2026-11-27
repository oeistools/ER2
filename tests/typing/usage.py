"""What a type checker sees of ER2 from Python (``er2/py.typed``).

Not a pytest module: CI runs ``mypy --strict`` on it against the
installed wheel, as a user's project would.  ``assert_type`` fails the
check if an annotation changes.
"""

from types import CodeType
from typing import assert_type

import er2
from er2.preparser import compile_er2
from er2.printing import Tex
from er2.runtime.numbers import exact_div

python = er2.preparse("sym x\nprint(x^2 + 1/3)\n")
assert_type(python, str)
assert_type(compile_er2(python, "<example>"), CodeType)
assert_type(er2.latex(er2.Rational(1, 3)), Tex)
assert_type(er2.latex(1, display=True), Tex)
assert_type(-er2.Rational(1, 3), er2.Rational)
assert_type(er2.__version__, str)
er2.show(exact_div(1, 3))
