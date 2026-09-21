--- Rewrite the repository's relative links for the site.
---
--- The prose pages include `docs/*.md` verbatim with `{{< include >}}`,
--- so the site and the repository cannot drift apart.  The cost is that
--- those documents link the way the repository is laid out
--- (`PARI_FUNCTIONS.md`, `../CHANGELOG.md`), which resolves nowhere once
--- the text is on a website.
---
--- Rewriting here rather than in the sources keeps both correct: the
--- documents stay readable on GitHub, and the site gets working links.
--- A target this table does not know is left alone and reported by
--- Quarto as an unresolved link, so a new document cannot slip in
--- silently.

local BLOB = "https://github.com/oeistools/ER2/blob/main/"

-- Documents that have a page of their own on the site.
local pages = {
  ["LANGUAGE.md"] = "language.html",
  ["STABILITY.md"] = "stability.html",
  ["PARI_FUNCTIONS.md"] = "reference.html",
  ["BENCHMARKS.md"] = "benchmarks.html",
}

-- Everything else lives in the repository and is linked there.
local repository = {
  ["../ARCHITECTURE.md"] = BLOB .. "ARCHITECTURE.md",
  ["../CHANGELOG.md"] = BLOB .. "CHANGELOG.md",
  ["../PLAN.md"] = BLOB .. "PLAN.md",
  ["../CONTRIBUTING.md"] = BLOB .. "CONTRIBUTING.md",
  ["../README.md"] = BLOB .. "README.md",
  ["../er2/data/pari_functions.csv"] = BLOB .. "er2/data/pari_functions.csv",
}

function Link(link)
  local target = link.target
  local anchor = ""
  local path, fragment = target:match("^([^#]*)#(.*)$")
  if path then
    target, anchor = path, "#" .. fragment
  end

  local rewritten = pages[target] or repository[target]
  if rewritten then
    link.target = rewritten .. anchor
  end
  return link
end
