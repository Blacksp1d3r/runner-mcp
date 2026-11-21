"""Offline regression tests for the ACTUAL Runner-MCP Actions scope classifier.

Runs the Bash embedded in validation.yml against disposable Git histories.
No network calls, hosted CI run, production changes or new dependencies.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/validation.yml"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True,
        check=True, timeout=15,
    ).stdout.strip()


def shell(name):
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    marker = "      - name: " + name
    assert lines.count(marker) == 1, f"missing or repeated CI step: {name}"
    start = lines.index(marker)
    index = next(i for i in range(start + 1, len(lines)) if lines[i] == "        run: |")
    body = []
    for line in lines[index + 1:]:
        if line.startswith("          "):
            body.append(line[10:])
        elif not line.strip():
            body.append("")
        else:
            break
    script = "\n".join(body) + "\n"
    assert script.strip()
    subprocess.run(["bash", "-n"], input=script, text=True, check=True, timeout=5)
    return script


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q", "-b", "base")
    git(root, "config", "user.name", "CI scope test")
    git(root, "config", "user.email", "ci@example.invalid")
    (root / "docs").mkdir()
    (root / "docs/intro.md").write_text("base\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "base")
    return root


def commit(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(root, "add", "--", name)
    git(root, "commit", "-qm", "change " + name)
    return git(root, "rev-parse", "HEAD")


def classify(root, before, event="push", ref="refs/heads/main"):
    output = root.parent / "scope-output"
    output.unlink(missing_ok=True)
    env = {
        **os.environ,
        "GITHUB_EVENT_NAME": event,
        "GITHUB_REF": ref,
        "PUSH_BEFORE": before,
        "GITHUB_OUTPUT": str(output),
        "RUNNER_TEMP": str(root.parent),
    }
    r = subprocess.run(
        ["bash", "-e", "-o", "pipefail"], input=shell("Determine qualification scope (fail closed)"),
        text=True, capture_output=True, cwd=root, env=env, check=True, timeout=15,
    )
    match = re.fullmatch(r"full=(true|false)\n", output.read_text(encoding="utf-8"))
    assert match is not None
    status = "FULL" if match[1] == "true" else "DOCS_ONLY"
    assert "RUNNER_MCP_QUALIFICATION_SCOPE=" + status in r.stdout
    return status


def test_docs_only_push(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "docs/intro.md", "docs only\n")
    assert classify(repo, base) == "DOCS_ONLY"
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "docs/deep/guide.rst", "nested docs only\n")
    assert classify(repo, base) == "DOCS_ONLY"


def test_code_workflow_and_disguised_docs_force_full(repo):
    for name in (
        "src/runner_mcp/source.py", "tools/doc_memory/doc_memory.py",
        ".github/workflows/check.yml", "docs/example.py", "pyproject.toml",
    ):
        base = git(repo, "rev-parse", "HEAD")
        commit(repo, name, "source or config\n")
        assert classify(repo, base) == "FULL", name


def test_multiple_commit_main_push_checks_entire_range(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "src/core.py", "earlier code change\n")
    commit(repo, "docs/intro.md", "last commit docs only\n")
    assert classify(repo, base) == "FULL"
    # HEAD^1 alone would give the wrong, cheap classification.
    assert classify(repo, git(repo, "rev-parse", "HEAD^1")) == "DOCS_ONLY"


def test_docs_only_multi_commit_push(repo):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "docs/intro.md", "docs1\n")
    commit(repo, "README.md", "docs2\n")
    assert classify(repo, base) == "DOCS_ONLY"


def test_pr_synthetic_merge_uses_base_first_parent(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "feature")
    commit(repo, "docs/intro.md", "PR docs\n")
    git(repo, "checkout", "-q", "base")
    git(repo, "merge", "--no-ff", "-qm", "synthetic PR merge", "feature")
    assert git(repo, "rev-parse", "HEAD") != base
    assert classify(repo, "", event="pull_request", ref="refs/pull/42/merge") == "DOCS_ONLY"


def test_missing_base_unknown_event_and_empty_diff_fail_closed(repo):
    base = git(repo, "rev-parse", "HEAD")
    assert classify(repo, base) == "FULL"
    commit(repo, "docs/intro.md", "docs\n")
    assert classify(repo, "") == "FULL"
    assert classify(repo, "0" * 40) == "FULL"
    assert classify(repo, base, event="workflow_dispatch") == "FULL"
    assert classify(repo, base, event="push", ref="refs/heads/feature") == "FULL"


def test_only_deleted_docs_can_use_docs_scope(repo):
    base = git(repo, "rev-parse", "HEAD")
    (repo / "docs/intro.md").unlink()
    git(repo, "add", "-u")
    git(repo, "commit", "-qm", "delete docs")
    assert classify(repo, base) == "DOCS_ONLY"


def test_required_checks_and_release_are_not_bypassed():
    data = WORKFLOW.read_text(encoding="utf-8")
    assert data.count("    name: Ruff and pytest") == 1
    assert "full_qualification:" in data
    assert data.count("if: steps.scope.outputs.full == 'true'") == 6
    assert data.count("if: needs.validate.outputs.full_qualification == 'true'") == 3
    assert "needs: [validate, demo-smoke, disposable-systemd-user]" in data
    for name in (
        "Verify unique shipping version and registry parity",
        "Verify changed docs using existing doc-memory precommit",
        "Whitespace check",
    ):
        index = data.index("- name: " + name)
        assert "if: steps.scope.outputs.full" not in data[index:index + 135]
    version = shell("Verify unique shipping version and registry parity")
    artifact = shell("Classify merged code release candidate")
    assert 'base="$PUSH_BEFORE"' in version
    assert 'base="$PUSH_BEFORE"' in artifact
    assert 'git cat-file -e "$base^{commit}"' in version
    assert 'git cat-file -e "$base^{commit}"' in artifact
