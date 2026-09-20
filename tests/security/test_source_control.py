import subprocess
from pathlib import Path

import pytest

from runner_mcp.source_control import SourceControlError, clean_head


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Runner MCP Test")
    (root / "app.txt").write_text("v1\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root


def test_clean_head_returns_only_safe_commit_state(tmp_path: Path) -> None:
    root = repo(tmp_path)
    result = clean_head(root)
    assert result["clean"] is True
    assert result["commit"] == git(root, "rev-parse", "HEAD")
    assert str(root) not in repr(result)


def test_dirty_worktree_blocks_high_risk_approval(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(SourceControlError, match="clean"):
        clean_head(root)


def test_non_git_project_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "plain"
    root.mkdir()
    with pytest.raises(SourceControlError, match="Git working tree"):
        clean_head(root)
