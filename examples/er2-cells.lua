-- Show ER2 cells as ER2 (ARCHITECTURE.md §1.2, D9).
--
-- Cells stay ```{python} in the source: that is what Quarto's Jupyter
-- engine executes and what editor tooling understands.  A document
-- with `jupyter: er2` runs every one of them through the ER2
-- preparser, so every executable Python block *is* ER2 and can be
-- relabelled without a marker -- which is why no `#| classes: er2` is
-- needed in 62 separate cells.
--
-- Quarto runs Lua filters after the kernel has run, so this changes
-- only how a block is displayed; it could not make one execute.  The
-- language is renamed to `er2`, which Pandoc highlights from
-- `er2.xml` (loaded by `syntax-definitions:`); without that file the
-- block would render unhighlighted, since Pandoc has no `er2` lexer.
-- The cell div is also marked, as a hook for a theme to style.

function CodeBlock(el)
  if el.classes[1] == "python" then
    el.classes[1] = "er2"
  end
  return el
end

function Div(el)
  if el.classes:includes("cell") and not el.classes:includes("er2") then
    el.classes:insert("er2")
  end
  return el
end
