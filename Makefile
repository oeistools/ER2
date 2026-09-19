# ER2 development tasks.  Run `make` or `make help` to list them.
#
# Quarto runs its Jupyter bridge on QUARTO_PYTHON, which needs nbformat,
# nbclient and PyYAML: the project's .venv has them (dev group).

VENV_PYTHON := $(CURDIR)/.venv/bin/python
# The user-wide install goes to the usual places even when make runs in a
# sandbox that redefines XDG_DATA_HOME (such as VS Code installed as a snap).
USER_ENV := env -u XDG_DATA_HOME UV_TOOL_DIR=$(HOME)/.local/share/uv/tools \
	UV_TOOL_BIN_DIR=$(HOME)/.local/bin
QUARTO := QUARTO_PYTHON=$(VENV_PYTHON) quarto
FILE ?= examples/demo.qmd

.DEFAULT_GOAL := help
.PHONY: help install install-global uninstall-global test test-fast lint \
	format check render preview bench sync-pari clean

help:  ## List the available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*## "} {printf "  make %-17s %s\n", $$1, $$2}'
	@echo "  (render and preview take FILE=path.qmd; default $(FILE))"

install:  ## Create .venv and register the ER2 kernel in it (for Quarto)
	uv sync
	uv run er2 kernel install --sys-prefix

install-global:  ## Install the `er2` command for your user (editable)
	$(USER_ENV) uv tool install --editable '.[jupyter,oeis]' --force
	$(USER_ENV) $(HOME)/.local/bin/er2 kernel install

uninstall-global:  ## Remove the user-wide `er2` command
	$(USER_ENV) uv tool uninstall er2

test:  ## Run all tests (notebooks and Quarto included)
	uv run pytest -q

test-fast:  ## Run the tests without Jupyter and Quarto
	uv run pytest -q --ignore=tests/notebooks

lint:  ## Check PEP 8 (ruff format --check and ruff check)
	uv run ruff format --check
	uv run ruff check

format:  ## Format the code with ruff
	uv run ruff format
	uv run ruff check --fix

check: lint test  ## Lint and test: what CI runs

render:  ## Render a Quarto document with the ER2 kernel (FILE=...)
	$(QUARTO) render $(FILE) --execute-daemon-restart

preview:  ## Live preview of a Quarto document (FILE=...)
	$(QUARTO) preview $(FILE) --execute-daemon-restart

bench:  ## Run the benchmarks and update docs/BENCHMARKS.md
	uv run python benchmarks/run.py --write

sync-pari:  ## Regenerate docs/PARI_FUNCTIONS.md from the PARI table
	uv run python tools/sync_pari_functions.py

clean:  ## Remove caches and Quarto output
	rm -rf .pytest_cache .ruff_cache .quarto examples/.quarto
	rm -rf examples/*.html examples/*_files examples/*.quarto_ipynb
	find . -name __pycache__ -type d -not -path './.venv/*' -prune \
		-exec rm -rf {} +
