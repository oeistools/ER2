"""The release workflow (PLAN.md, M8; docs/RELEASING.md).

The workflow only runs when a tag is pushed, so a mistake in it is
found on release day, which is the worst day to find it.  What can be
checked here is checked here:

* only the publish job may ask for the identity PyPI trusts, and only
  behind the ``pypi`` environment, whose approval is the human step;
* the tag is checked against the version before anything is built;
* the smoke test's expected output is what ER2 really prints, and it is
  the same program ``docs/RELEASING.md`` tells a person to run by hand.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASING = ROOT / "docs" / "RELEASING.md"


def _jobs():
    """Return the text of the build and publish jobs, in that order."""
    text = WORKFLOW.read_text(encoding="utf-8")
    head, _, jobs = text.partition("\njobs:\n")
    build, _, publish = jobs.partition("\n  publish:\n")
    return head, build, publish


def _printf_arguments(text):
    """Return the single-quoted arguments of every ``printf`` in text."""
    return re.findall(r"printf '([^']*)'", text)


def test_only_the_publish_job_can_publish():
    head, build, publish = _jobs()
    assert "id-token: write" not in head
    assert "id-token: write" not in build
    assert "id-token: write" in publish
    assert "name: pypi" in publish
    assert "pypa/gh-action-pypi-publish" in publish
    # No token: trusted publishing is the whole point.
    assert "password" not in publish
    assert "secrets." not in publish


def test_the_workflow_runs_on_version_tags_only():
    head, _, _ = _jobs()
    assert 'tags: ["v*"]' in head
    assert "branches" not in head


def test_the_tag_is_checked_before_building():
    _, build, _ = _jobs()
    version_check = build.index('"v${version}"')
    on_main = build.index("merge-base --is-ancestor")
    assert version_check < build.index("uv build")
    assert on_main < build.index("uv build")
    assert build.index("uv run pytest") < build.index("uv build")


def test_the_smoke_test_matches_the_manual_checklist():
    _, build, _ = _jobs()
    program, expected = _printf_arguments(build)
    assert program in _printf_arguments(RELEASING.read_text("utf-8"))
    assert "1024 1/3 (x - 1)*(x + 1)*(x^2 + 1)" in expected


def test_the_smoke_test_expects_what_er2_prints(tmp_path):
    _, build, _ = _jobs()
    program, expected = _printf_arguments(build)
    source = tmp_path / "first.er2"
    # The workflow passes these through printf, which expands ``\\n``.
    source.write_text(program.replace("\\n", "\n"), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "er2", str(source)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected.replace("\\n", "\n")
