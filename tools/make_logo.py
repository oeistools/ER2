"""Generate the ER2 logo and icon into ``assets/``.

The mark is ``ER`` beside a tile reading ``^2``: the line you would
actually type in an ``.er2`` source, where ``^`` is a power (the one
thing that separates ER2 from Python, ARCHITECTURE.md §1.1).  The tile
is also the icon, so the icon is the second half of the name.

Everything is emitted as ``<path>``: the letterforms are Exo 2
ExtraBold converted to outlines, so the files render the same on a
machine that does not have the font, and the caret is a filled polygon
rather than a stroke, because some renderers drop a stroked path under
the negative scale that flipping font coordinates needs.

``fontTools`` is a tool-only dependency, not a dependency of ER2::

    uv run --with fonttools python tools/make_logo.py

The font is fetched from Google Fonts unless ``--font`` gives a local
copy.  Upstream may revise Exo 2, which would move the outlines; pass a
pinned file to reproduce a past release exactly.
"""

import argparse
import math
import sys
import urllib.request
from pathlib import Path

FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/"
    "ofl/exo2/Exo2%5Bwght%5D.ttf"
)
ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Exo 2 is drawn on a 1000-unit em with a cap height of 690.
CAP = 690
WORDMARK_WEIGHT = 800
TAGLINE_WEIGHT = 600
TAGLINE = "MATHEMATICAL PYTHON"
TAGLINE_TRACKING = 190
WORD_SPACE = 240

# The tile, in its own 64-unit box: a rounded square holding ``^2``.
TILE_RADIUS = 15
TILE_TWO_CAP = 28.0
# Width, arm y, apex y, thickness.  A caret reads as the operator
# only when it is clearly wider than tall, about 2:1; a narrow one
# reads as an arrowhead.
TILE_CARET = (17.0, 29.5, 21.0, 6.0)
TILE_GAP = 3.4
TILE_BASELINE = 45.5

COLOURS = {
    "ink": "#100D0B",
    "rust": "#9E2F10",
    "paper": "#FAF6F3",
    "muted": "#57514C",
    "muted_dark": "#9A8F88",
}


def chevron(xa, xb, y_arm, y_apex, t):
    """Return a caret as a filled polygon: ``(path_d, bounds)``.

    Each arm end is cut square to its own arm, which suits Exo 2's flat
    terminals.  Offsetting both sides of the two arms and intersecting
    the offsets gives the outline, so there is no stroke to scale.
    """
    a, m, b = (xa, y_arm), ((xa + xb) / 2, y_apex), (xb, y_arm)
    half = t / 2

    def unit(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(dx, dy)
        return dx / length, dy / length

    d1, d2 = unit(a, m), unit(m, b)
    n1, n2 = (-d1[1], d1[0]), (-d2[1], d2[0])

    def meet(p1, dir1, p2, dir2):
        det = dir1[0] * -dir2[1] - -dir2[0] * dir1[1]
        rx, ry = p2[0] - p1[0], p2[1] - p1[1]
        s = (rx * -dir2[1] - -dir2[0] * ry) / det
        return p1[0] + s * dir1[0], p1[1] + s * dir1[1]

    sides = []
    for sign in (1, -1):
        corner_a = (a[0] + sign * half * n1[0], a[1] + sign * half * n1[1])
        corner_b = (b[0] + sign * half * n2[0], b[1] + sign * half * n2[1])
        apex = meet(
            corner_a,
            d1,
            (m[0] + sign * half * n2[0], m[1] + sign * half * n2[1]),
            d2,
        )
        sides.append((corner_a, apex, corner_b))
    (a1, m1, b1), (a2, m2, b2) = sides
    ring = [a1, m1, b1, b2, m2, a2]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in ring) + " Z"
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return path, (min(xs), min(ys), max(xs), max(ys))


def read_font(path):
    """Return the Exo 2 bytes, downloading them unless ``path`` is given."""
    if path:
        return Path(path).read_bytes()
    with urllib.request.urlopen(FONT_URL, timeout=60) as response:
        return response.read()


class Outlines:
    """Exo 2 at one weight, as SVG path data."""

    def __init__(self, data, weight):
        """Instantiate the variable font at ``weight``."""
        import io

        from fontTools.ttLib import TTFont
        from fontTools.varLib.instancer import instantiateVariableFont

        self.font = instantiateVariableFont(
            TTFont(io.BytesIO(data)), {"wght": weight}, inplace=True
        )
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()

    def run(self, text, tracking=0):
        """Return ``(glyphs, xmin, xmax)`` for ``text`` set at ``tracking``.

        ``glyphs`` is a list of ``(path_d, x)`` in font units; ``xmin``
        and ``xmax`` bound the ink, which is what optical spacing needs
        (advance widths include side bearings).
        """
        from fontTools.pens.boundsPen import BoundsPen
        from fontTools.pens.svgPathPen import SVGPathPen

        out, x, xmin, xmax = [], 0, None, None
        for char in text:
            if char == " ":
                x += WORD_SPACE + tracking
                continue
            name = self.cmap[ord(char)]
            pen, bounds = SVGPathPen(self.glyphs), BoundsPen(self.glyphs)
            self.glyphs[name].draw(pen)
            self.glyphs[name].draw(bounds)
            if bounds.bounds:
                lo, hi = x + bounds.bounds[0], x + bounds.bounds[2]
                xmin = lo if xmin is None else min(xmin, lo)
                xmax = hi if xmax is None else max(xmax, hi)
            out.append((pen.getCommands(), x))
            x += self.font["hmtx"][name][0] + tracking
        return out, xmin, xmax


def paint(glyphs, colour, dx=0):
    """Return ``glyphs`` as filled paths, offset by ``dx`` font units."""
    return "".join(
        f'<path fill="{colour}" transform="translate({dx + x:.0f} 0)"'
        f' d="{d}"/>'
        for d, x in glyphs
    )


class Art:
    """The pieces of the mark, measured once and reused by every file."""

    def __init__(self, data):
        """Measure the letters, the tagline and the tile from ``data``."""
        bold = Outlines(data, WORDMARK_WEIGHT)
        self.two, two_min, two_max = bold.run("2")
        self.er, er_min, self.er_max = bold.run("ER")
        self.er_min = er_min
        self.er_width = self.er_max - er_min
        self.tagline, self.tag_min, tag_max = Outlines(
            data, TAGLINE_WEIGHT
        ).run(TAGLINE, tracking=TAGLINE_TRACKING)
        self.tag_width = tag_max - self.tag_min

        # ``^2`` inside the tile's own 64-unit box.
        self.two_scale = TILE_TWO_CAP / CAP
        caret_d, caret_box = chevron(0, *TILE_CARET)
        self.tile_caret_d = caret_d
        self.tile_caret_box = caret_box
        caret_w = caret_box[2] - caret_box[0]
        two_w = (two_max - two_min) * self.two_scale
        self.tile_x0 = (64 - (caret_w + TILE_GAP + two_w)) / 2
        self.tile_two_x = (
            self.tile_x0 + caret_w + TILE_GAP - two_min * self.two_scale
        )

    def tile_content(self, colour):
        """Return the ``^2`` inside the tile, in its 64-unit box."""
        dx = self.tile_x0 - self.tile_caret_box[0]
        return (
            f'<path fill="{colour}" transform="translate({dx:.2f} 0)"'
            f' d="{self.tile_caret_d}"/>'
            f'<g transform="translate({self.tile_two_x:.2f} {TILE_BASELINE})'
            f' scale({self.two_scale:.5f} {-self.two_scale:.5f})">'
            f"{paint(self.two, colour)}</g>"
        )

    def icon(self, background, colour):
        """Return the square icon on its own."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" \
height="64" viewBox="0 0 64 64" role="img" aria-label="ER2 icon: a caret \
and a two">
  <rect width="64" height="64" rx="{TILE_RADIUS}" fill="{background}"/>
  {self.tile_content(colour)}
</svg>
'''

    def logo(self, letters, tile_bg, tile_fg, muted, pad=28.0, scale=0.200):
        """Return the wordmark: ``ER``, the tile, and the tagline.

        The tile is exactly as tall as the capitals and sits on the
        baseline, so it reads as the name's second half rather than as a
        badge stuck beside it.  The tagline is set to the wordmark's
        width, which is what locks the two lines together.
        """
        cap = CAP * scale
        baseline = pad + cap
        letters_w = self.er_width * scale
        gap = cap * 0.20
        tile_x = pad + letters_w + gap
        word_w = letters_w + gap + cap
        tag_scale = word_w / self.tag_width
        tag_y = baseline + cap * 0.38
        width, height = pad * 2 + word_w, tag_y + pad - 8
        return f'''<svg xmlns="http://www.w3.org/2000/svg" \
width="{width:.0f}" height="{height:.0f}" \
viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="t d">
  <title id="t">ER2</title>
  <desc id="d">The ER2 wordmark: the letters E and R beside a tile reading \
caret two.</desc>
  <g transform="translate({pad - self.er_min * scale:.2f} {baseline:.2f}) \
scale({scale:.5f} {-scale:.5f})">{paint(self.er, letters)}</g>
  <g transform="translate({tile_x:.2f} {pad:.2f}) scale({cap / 64:.5f})">
    <rect width="64" height="64" rx="{TILE_RADIUS}" fill="{tile_bg}"/>
    {self.tile_content(tile_fg)}
  </g>
  <g transform="translate({pad - self.tag_min * tag_scale:.2f} \
{tag_y:.2f}) scale({tag_scale:.5f} {-tag_scale:.5f})">\
{paint(self.tagline, muted)}</g>
</svg>
'''


def main(argv=None):
    """Write the three asset files; return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", help="a local Exo2[wght].ttf")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the files on disk are not what this script makes",
    )
    args = parser.parse_args(argv)
    try:
        import fontTools  # noqa: F401
    except ImportError:
        print(
            "this script needs fontTools, which ER2 itself does not:\n"
            "  uv run --with fonttools python tools/make_logo.py",
            file=sys.stderr,
        )
        return 1
    art = Art(read_font(args.font))
    c = COLOURS
    files = {
        "er2-logo.svg": art.logo(c["ink"], c["rust"], c["paper"], c["muted"]),
        "er2-logo-dark.svg": art.logo(
            c["paper"], c["rust"], c["paper"], c["muted_dark"]
        ),
        "er2-icon.svg": art.icon(c["rust"], c["paper"]),
    }
    stale = []
    for name, body in files.items():
        path = ASSETS / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(name)
            continue
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path.relative_to(ASSETS.parent)}")
    if stale:
        print("out of date: " + ", ".join(stale), file=sys.stderr)
        return 1
    if args.check:
        print("assets are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
