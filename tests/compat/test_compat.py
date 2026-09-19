"""Python compatibility contract (ARCHITECTURE.md §1.1).

Each snippet is plain Python whose behavior must be identical when it is
run as ER2.  Snippets avoid the documented differences (``^``, ``/``
between integers, ``sym``).
"""

import contextlib
import io
import textwrap

import pytest

from er2 import prelude
from er2.preparser import preparse

SNIPPETS = {
    "classes and dataclasses": """
        from dataclasses import dataclass, field

        @dataclass(order=True)
        class P:
            x: int
            y: int = 0
            tags: list = field(default_factory=list)

        print(sorted([P(2, 1), P(1, 5)]), P(1) == P(1))
    """,
    "decorators and closures": """
        import functools

        def twice(f):
            @functools.wraps(f)
            def g(*a, **k):
                return f(f(*a, **k))
            return g

        @twice
        def inc(n):
            return n + 1

        print(inc(3), inc.__name__)
    """,
    "generators and comprehensions": """
        def fib():
            a, b = 0, 1
            while True:
                yield a
                a, b = b, a + b

        import itertools
        print(list(itertools.islice(fib(), 10)))
        print({k: v for k, v in zip("abc", range(3))})
        print({i % 3 for i in range(9)})
    """,
    "match statement": """
        def kind(v):
            match v:
                case 0:
                    return "zero"
                case int(n) if n < 0:
                    return "negative"
                case [first, *rest]:
                    return f"list starting {first}, {len(rest)} more"
                case {"k": value}:
                    return f"dict {value}"
                case _:
                    return "other"

        print([kind(v) for v in (0, -3, [1, 2, 3], {"k": 9}, "s")])
        print(kind(int("0")), kind(-int("3")))  # plain ints, not literals
    """,
    "async": """
        import asyncio

        async def square(n):
            await asyncio.sleep(0)
            return n * n

        async def main():
            return await asyncio.gather(*(square(i) for i in range(5)))

        print(asyncio.run(main()))
    """,
    "exceptions and context managers": """
        import contextlib

        @contextlib.contextmanager
        def tag(name):
            print("<" + name + ">")
            yield
            print("</" + name + ">")

        try:
            with tag("a"):
                raise KeyError(3)
        except KeyError as e:
            print("caught", e.args)
        finally:
            print("done")
    """,
    "integers behave as int": """
        import json, math, struct
        n = 10
        print(isinstance(n, int), issubclass(type(n), int))
        print(json.dumps({"n": n, "l": [1, 2]}), math.gcd(12, 18))
        print(7 // 2, 7 % 3, divmod(17, 5), round(2.5), 2 ** 10)
        print(f"{n:05d} {n:x} {n:b}", hex(255), n.bit_length())
        print(struct.pack("<i", n), list(range(3))[1], "ab" * 2, [0] * 3)
        print(sorted({3: "c", 1: "a"}.items()), bool(0), int("42") + 1)
    """,
    "floats and strings": """
        print(0.1 + 0.2, 1.5 * 2, 3 / 2.0, "a^b", 'sym x', "%d items" % 3)
        print("{:.3f}".format(2.0 / 3), str(10), repr(10), -7 // 2)
    """,
    "type hints": """
        from typing import Generic, TypeVar
        T = TypeVar("T")

        class Box(Generic[T]):
            def __init__(self, item: T) -> None:
                self.item = item

        def first(xs: list[int]) -> int | None:
            return xs[0] if xs else None

        print(Box[int](3).item, first([4, 5]), first([]))
    """,
}


def run(source, er2):
    """Run ``source`` as Python or as ER2; return its standard output."""
    source = textwrap.dedent(source)
    namespace = {"__name__": "__main__"}
    if er2:
        source = preparse(source)
        prelude.inject(namespace)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(compile(source, "<snippet>", "exec"), namespace)
    return out.getvalue()


@pytest.mark.parametrize("name", SNIPPETS)
def test_python_code_behaves_the_same(name):
    snippet = SNIPPETS[name]
    assert run(snippet, er2=True) == run(snippet, er2=False)
