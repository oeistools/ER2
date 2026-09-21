# Releasing ER2

For the maintainer. Publishing is **irreversible**: a version uploaded to PyPI can be yanked but
never replaced, and the project name is claimed for good. Nothing in this repository uploads
anything — the last step is run by a person, on purpose.

## Before you start

The name `er2` was free on PyPI when 0.7.0 was prepared (2026-09-21). Check again before the
first upload, because a name can be taken at any time:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/er2/json   # 404 = free
```

You need a PyPI account and an API token, or a configured trusted publisher.

## The checklist

1. **Everything green.**

   ```bash
   make check          # ruff + the full suite, exactly what CI runs
   ```

2. **The version is right.** `pyproject.toml` is the single source; `er2.__version__` reads it
   from the installed metadata, so there is nothing else to bump.

3. **The changelog has a section for it**, dated, with `## [Unreleased]` left above it holding
   `Nothing yet.`

4. **The status lines agree** with the new version: `README.md` (badge and "Status and roadmap"),
   `ARCHITECTURE.md` (the header), `CLAUDE.md`.

5. **Build.**

   ```bash
   make dist           # rm -rf dist && uv build
   ```

6. **Check the artifacts before they leave.**

   ```bash
   uv run --with twine twine check dist/*
   ```

7. **Install the built wheel somewhere clean and run it.** This is the step that catches a
   missing data file, which no test in the repository can see:

   ```bash
   uv venv /tmp/er2-check --python 3.12
   uv pip install --python /tmp/er2-check/bin/python dist/er2-*.whl
   printf 'sym x\nprint(2^10, 1/3, factor(x^4 - 1))\nprint(isprime(2^521 - 1))\n' > /tmp/first.er2
   /tmp/er2-check/bin/er2 /tmp/first.er2
   ```

   Expected: `1024 1/3 (x - 1)*(x + 1)*(x^2 + 1)` and `True`.

8. **Publish.** Not done by any script here:

   ```bash
   uv publish                     # asks for the token, or uses UV_PUBLISH_TOKEN
   ```

   To rehearse without claiming anything, use TestPyPI first:

   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/
   ```

9. **Tag and push.**

   ```bash
   git tag -a v0.7.0 -m "ER2 0.7.0"
   git push origin v0.7.0
   ```

10. **Confirm the install path users will take.**

    ```bash
    uv venv /tmp/er2-pypi --python 3.12
    uv pip install --python /tmp/er2-pypi/bin/python er2
    /tmp/er2-pypi/bin/er2 /tmp/first.er2
    ```

## The documentation site

`.github/workflows/pages.yml` renders `site/` and deploys it to GitHub Pages on every push to
`main`. It needs **Settings → Pages → Source: GitHub Actions** enabled once. On a private
repository, Pages requires a paid plan; the site otherwise builds locally with `make site`.

The site executes ER2 while it renders, so a build failure there means documented behaviour
stopped being true.

## What not to do

- **Do not re-upload a version.** PyPI refuses it. If something is wrong, yank and release a
  patch.
- **Do not publish from CI without trusted publishing.** A long-lived token in a secret is worth
  more to an attacker than the release is worth to you.
- **Do not tag before the upload succeeds.** A tag that points at a version nobody can install is
  a lie that is awkward to undo.
