# Releasing ER2

For the maintainer. Publishing is **irreversible**: a version uploaded to PyPI can be yanked but
never replaced, and the project name is claimed for good. So a person always takes the last
step, on purpose. Either they run the upload by hand, or they approve the upload that
`.github/workflows/release.yml` has prepared. Nothing uploads by itself.

## Before you start

The name `er2` was free on PyPI when 0.7.0 was prepared (2026-09-21). Check again before the
first upload, because a name can be taken at any time:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/er2/json   # 404 = free
```

You need a PyPI account. The upload then goes one of two ways. **Trusted publishing** through
the workflow is the one to use: no token exists anywhere. **By hand with an API token** is the
fallback.

## One-time setup for trusted publishing

Nothing here can be done from the repository. It needs your accounts:

1. **On PyPI**, add a publisher at <https://pypi.org/manage/account/publishing/>. For the first
   release the project does not exist yet, so add it as a *pending* publisher, which also
   reserves the name for this repository:

   | Field             | Value         |
   |-------------------|---------------|
   | PyPI project name | `er2`         |
   | Owner             | `oeistools`   |
   | Repository name   | `ER2`         |
   | Workflow name     | `release.yml` |
   | Environment name  | `pypi`        |

2. **On GitHub**, create the environment under **Settings → Environments → New environment**,
   named `pypi`. Give it yourself as a **required reviewer**, and restrict its deployment
   branches and tags to the tag pattern `v*`. The required reviewer is what makes the upload wait
   for a person. Without one, pushing a tag would publish straight away.

PyPI then accepts uploads only from that workflow file, in that repository, running in that
environment. A fork or another workflow cannot publish, and there is no secret to leak.

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

8. **Publish**, with the workflow or by hand.

   **With the workflow** (trusted publishing, set up as above), the tag is what starts it:

   ```bash
   git tag -a v0.7.0 -m "ER2 0.7.0"
   git push origin v0.7.0
   ```

   The *Release* run first checks the tag against `pyproject.toml` and checks that the commit is
   on `main`. It then runs ruff and the full suite, builds, runs `twine check`, and runs the
   built wheel in a clean 3.12 environment (steps 1 and 5–7 again, on a clean machine). Only
   then does it stop and wait at the `pypi` environment. **Approving that deployment is the
   publication.** If anything fails before that point, nothing has been uploaded: delete the tag
   (`git push --delete origin v0.7.0`, then `git tag -d v0.7.0`), fix the problem, and tag again.

   **By hand**, with an API token:

   ```bash
   uv publish                     # asks for the token, or uses UV_PUBLISH_TOKEN
   ```

   To rehearse without claiming anything, use TestPyPI first:

   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/
   ```

9. **Tag and push**, after a manual upload only. The workflow route tagged in step 8.

   ```bash
   git tag -a v0.7.0 -m "ER2 0.7.0"
   git push origin v0.7.0
   ```

   This tag also starts the *Release* workflow. Its upload then fails, harmlessly, because PyPI
   refuses a version that already exists. Reject the pending deployment instead of approving it.

10. **Confirm the install path users will take.**

    ```bash
    uv venv /tmp/er2-pypi --python 3.12
    uv pip install --python /tmp/er2-pypi/bin/python er2
    /tmp/er2-pypi/bin/er2 /tmp/first.er2
    ```

## The documentation site

`.github/workflows/pages.yml` renders `site/` and deploys it to GitHub Pages on every push to
`main`. It passes `enablement: true` to `actions/configure-pages`, so the first run turns Pages
on by itself; no setting has to be clicked. Should that ever be refused, the manual equivalent is
**Settings → Pages → Source: GitHub Actions**. The site also builds locally with `make site`.

The repository is public, so Pages costs nothing. (A *private* repository would need a paid plan
for it.)

The site executes ER2 while it renders, so a build failure there means documented behaviour
stopped being true.

## What not to do

- **Do not re-upload a version.** PyPI refuses it. If something is wrong, yank and release a
  patch.
- **Do not publish from CI without trusted publishing.** A long-lived token in a secret is worth
  more to an attacker than the release is worth to you.
- **Do not leave a tag behind a failed release.** A tag that points at a version nobody can
  install is a lie. With the workflow the tag comes first by design, because it is the trigger.
  So if the run fails or you reject it, delete the tag before doing anything else.
- **Do not remove the `pypi` environment's required reviewer.** It is the only thing between
  pushing a tag and publishing.
