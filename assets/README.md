# ER2 brand assets

| File | Use |
|------|-----|
| `er2-logo.svg` | The wordmark on a light background (README, docs, slides). |
| `er2-logo-dark.svg` | The same on a dark background. |
| `er2-icon.svg` | The tile on its own: favicon, avatar, app icon. |

**These three files are generated.** Do not edit them by hand; edit
[tools/make_logo.py](../tools/make_logo.py) and run it:

```bash
uv run --with fonttools python tools/make_logo.py
uv run --with fonttools python tools/make_logo.py --check   # CI-style check
```

`fontTools` is a tool-only dependency, deliberately not one of ER2's
(CLAUDE.md keeps the runtime to `sympy` + `cypari2`), so it is pulled in for
the run and thrown away.

## The idea

The wordmark is `ER` beside a tile reading `^2`. It is the line you would
actually type in an `.er2` source: `^` is a power, which is the one thing
that separates ER2 from Python, where the same line would be an XOR
(ARCHITECTURE.md §1.1). The logo teaches the syntax instead of decorating it.

The tile is also the icon, so the icon is the second half of the name rather
than a separate symbol. `2` is set at full size, not as a superscript — the
caret already carries the exponent.

## How it is built

| Decision | Why |
|----------|-----|
| Letters as `<path>`, never `<text>` | A logo that names a font breaks on machines without it. The outlines come from Exo 2 at `wght=800` and no longer depend on the font. |
| The caret is a filled polygon, not a stroke | Flipping font coordinates needs a negative scale, and some renderers drop a stroked path under one — the caret vanished, leaving `ER   2`. Fills also survive SVG conversion and sanitisers better. |
| Caret about 2:1, wider than tall | At 250×230 it read as an arrowhead. 400×190 reads as the `^` operator. |
| Tile exactly as tall as the capitals, on the baseline | It reads as the name's second half, not as a badge stuck beside the word. |
| Tagline set to the wordmark's width | The two lines lock together at any size; the script solves for the scale rather than hard-coding it. |
| Same rust tile in light and dark | The icon looks identical wherever it appears. Only the letters and tagline change colour. |

The geometry lives in named constants at the top of the script, so the gap
around the caret, the tile's corner radius and the tagline's tracking are all
one edit away.

## Colours

| Token | Hex | Where |
|-------|-----|-------|
| Ink | `#100D0B` | The letters on a light background. |
| Rust | `#9E2F10` | The tile, in both versions. |
| Paper | `#FAF6F3` | The `^2` inside the tile; the letters on a dark background. |
| Muted | `#57514C` | The tagline, light background. |
| Muted dark | `#9A8F88` | The tagline, dark background. |

Paper on rust is 6.9:1, so the mark passes WCAG AA even at small sizes.

**Do not use Python's blue and yellow, and never put the Python logo inside
the mark.** That logo is a PSF trademark and its guidelines do not allow it
in another project's identity. ER2 says "Python" in words instead. Dark navy
with gold reads as Python's pairing even with different hex values, which is
why the palette is a warm near-black with rust.

## Known limits

- At 16 px the `^2` inside the tile turns to mush; the tile still reads as a
  mark. If a true 16 px favicon is needed, generate a variant with the caret
  alone — one shape survives that size, two do not.
- Regenerating downloads Exo 2 from Google Fonts' `main` branch. If upstream
  revises the font the outlines move, so `--check` would report the files as
  stale. Pass `--font path/to/Exo2[wght].ttf` to pin a copy.

## Typography

[Exo 2](https://fonts.google.com/specimen/Exo+2) by Natanael Gama, under the
[SIL Open Font License 1.1](https://openfontlicense.org/): ExtraBold (800)
for the wordmark, SemiBold (600) for the tagline. The OFL allows converting
glyphs to outlines for a mark like this; no font file is redistributed here.
