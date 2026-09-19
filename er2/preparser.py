"""Translate ER2 source code into plain Python (ARCHITECTURE.md §3.1).

The translation works on tokens, never on raw text, so string literals
and comments are left untouched.  Every replacement stays on the line
of the token it replaces, which keeps line numbers identical between the
ER2 source and the generated Python.

Transformations (the §1.1 contract):

=============  =====================================
ER2            Python
=============  =====================================
``a ^ b``      ``a ** b``
``a ^^ b``     ``a ^ b``
``a ^= b``     ``a **= b``
``a ^^= b``    ``a ^= b``
``5``          ``__er2_int__(5)``
``sym x, y``   ``x, y = __er2_sym__("x, y")``
=============  =====================================
"""

import ast
import io
import keyword
import re
import tokenize
import warnings

INTEGER = "__er2_int__"
SYMBOLS = "__er2_sym__"

# Tokens after which a new statement starts.
_STATEMENT_START = {
    tokenize.NEWLINE,
    tokenize.NL,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENCODING,
}
# Operators that signal bit manipulation on the same line as ``^``.
_BITWISE_HINT = re.compile(r"0[xXbB]|&|\||<<|>>|~")


class ER2Warning(UserWarning):
    """Warning emitted by the ER2 preparser."""


class IncompleteSourceError(SyntaxError):
    """The source ends inside a bracket or a multi-line string."""


def preparse(source, filename="<er2>"):
    """Return the Python translation of the ER2 ``source`` string.

    Raise ``IncompleteSourceError`` if ``source`` ends inside a bracket or a
    multi-line string, and ``SyntaxError`` if it cannot be tokenized.
    """
    lines = source.splitlines(keepends=True)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError as exc:
        message, (lineno, offset) = exc.args
        error = IncompleteSourceError if "EOF" in message else SyntaxError
        raise error(message, (filename, lineno, offset + 1, None)) from None
    edits = []
    _power_and_xor(tokens, edits, lines, filename)
    _sym_statements(tokens, edits, filename)
    # Integer literals are wrapped in a second pass over valid Python, so
    # that the literals of ``case`` patterns can be found and left alone.
    python = _apply(lines, edits)
    lines = python.splitlines(keepends=True)
    tokens = list(tokenize.generate_tokens(io.StringIO(python).readline))
    edits = []
    _integer_literals(tokens, edits, _pattern_spans(python))
    return _apply(lines, edits)


def _power_and_xor(tokens, edits, lines, filename):
    """Record the edits for ``^``, ``^^``, ``^=`` and ``^^=``."""
    skip = False
    for i, tok in enumerate(tokens):
        if skip:
            skip = False
            continue
        if tok.type != tokenize.OP or tok.string not in ("^", "^="):
            continue
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        glued = (
            nxt is not None
            and nxt.type == tokenize.OP
            and nxt.start == tok.end
            and tok.string == "^"
            and nxt.string in ("^", "^=")
        )
        if glued:
            # ``^^`` -> ``^`` and ``^^=`` -> ``^=``: Python's XOR.
            edits.append((tok.start, nxt.end, nxt.string))
            skip = True
        else:
            edits.append((tok.start, tok.end, "*" * 2 + tok.string[1:]))
            _warn_if_bitwise(lines, tok.start[0], filename)


def _warn_if_bitwise(lines, lineno, filename):
    """Warn when ``^`` shares a line with obvious bit manipulation."""
    line = lines[lineno - 1] if lineno <= len(lines) else ""
    if _BITWISE_HINT.search(line.split("#", 1)[0]):
        warnings.warn_explicit(
            "'^' is a power in ER2; use '^^' for XOR",
            ER2Warning,
            filename,
            lineno,
        )


def _pattern_spans(python):
    """Return the ``(start, end)`` spans of ``case`` patterns in ``python``.

    A literal pattern (``case 0:``) is compared with ``==``, so it needs no
    ``Integer``, and a call there would be read as a class pattern.  Spans
    are ``(line, column)`` pairs with character columns, like tokens.
    Returns nothing when ``python`` does not parse; compiling it will
    report the error.
    """
    try:
        tree = ast.parse(python)
    except SyntaxError:
        return []
    lines = python.splitlines()
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.match_case):
            pattern = node.pattern
            start = _char_position(lines, pattern.lineno, pattern.col_offset)
            end = _char_position(
                lines, pattern.end_lineno, pattern.end_col_offset
            )
            spans.append((start, end))
    return spans


def _char_position(lines, lineno, byte_offset):
    """Convert an ``ast`` UTF-8 byte offset to a character column."""
    line = lines[lineno - 1].encode("utf-8")
    return lineno, len(line[:byte_offset].decode("utf-8"))


def _integer_literals(tokens, edits, skip=()):
    """Record the edits that wrap integer literals in ``__er2_int__``.

    Literals inside the ``skip`` spans (``case`` patterns) are left alone.
    """
    for tok in tokens:
        if tok.type != tokenize.NUMBER:
            continue
        if any(start <= tok.start and tok.end <= end for start, end in skip):
            continue
        try:
            value = ast.literal_eval(tok.string)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, int):
            edits.append((tok.start, tok.end, f"{INTEGER}({tok.string})"))


def _sym_statements(tokens, edits, filename):
    """Record the edits for ``sym`` statements (a soft keyword, D4)."""
    significant = [t for t in tokens if t.type != tokenize.COMMENT]
    for i, tok in enumerate(significant):
        if tok.type != tokenize.NAME or tok.string != "sym":
            continue
        prev = significant[i - 1] if i else None
        at_start = prev is None or prev.type in _STATEMENT_START
        # ``sym NAME`` is never valid Python, so after ``;`` or ``:`` (as in
        # ``if c: sym x``) it can only be a ``sym`` statement.
        at_start = at_start or (
            prev.type == tokenize.OP and prev.string in (";", ":")
        )
        if not at_start:
            continue
        names, j = _symbol_names(significant, i + 1)
        if names is None:
            continue
        end = significant[j - 1].end
        if tok.start[0] != end[0]:
            raise SyntaxError(
                "a 'sym' statement must fit on one line",
                (filename, tok.start[0], tok.start[1] + 1, None),
            )
        target = ", ".join(names) + ("," if len(names) == 1 else "")
        text = f'{target} = {SYMBOLS}("{", ".join(names)}")'
        edits.append((tok.start, end, text))


def _symbol_names(tokens, j):
    """Parse ``name(, name)*`` at ``tokens[j]``; return names and end index.

    Return ``(None, j)`` when the tokens are not a ``sym`` statement, so
    that ``sym = 3`` or ``sym(x)`` stay plain Python.
    """
    names = []
    while True:
        tok = tokens[j] if j < len(tokens) else None
        if (
            tok is None
            or tok.type != tokenize.NAME
            or keyword.iskeyword(tok.string)
        ):
            return None, j
        names.append(tok.string)
        j += 1
        nxt = tokens[j] if j < len(tokens) else None
        if nxt is not None and nxt.type == tokenize.OP and nxt.string == ",":
            j += 1
            continue
        ends = nxt is None or nxt.type in (
            tokenize.NEWLINE,
            tokenize.ENDMARKER,
        )
        ends = ends or (nxt.type == tokenize.OP and nxt.string == ";")
        return (names, j) if ends else (None, j)


def _apply(lines, edits):
    """Apply single-line ``(start, end, text)`` edits; return the source.

    Edits are applied right to left so earlier columns stay valid.
    """
    lines = list(lines)
    for (row, scol), (erow, ecol), text in sorted(edits, reverse=True):
        assert row == erow, "ER2 edits never span lines"
        lines[row - 1] = lines[row - 1][:scol] + text + lines[row - 1][ecol:]
    return "".join(lines)
