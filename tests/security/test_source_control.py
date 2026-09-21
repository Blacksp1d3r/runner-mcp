import subprocess
from contextlib import nullcontext
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.source_control import SourceControlError, SourceSynchronizer, clean_head


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



class IdleTests:
    def project_source_guard(self, project: str):
        return nullcontext()

    def project_has_work(self, project: str) -> bool:
        return False


class BusyTests:
    def project_source_guard(self, project: str):
        return nullcontext()

    def project_has_work(self, project: str) -> bool:
        return True


def _synchronizer(tmp_path: Path, tests=None) -> tuple[SourceSynchronizer, Path]:
    root = tmp_path / "sync-project"
    root.mkdir()
    registry = ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                environment="staging",
                root=root,
            )
        }
    )
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    return (
        SourceSynchronizer(
            registry=registry,
            safety=guard,
            tests=tests or IdleTests(),
        ),
        root,
    )


def test_source_sync_accepts_only_origin_reachable_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synchronizer, _root = _synchronizer(tmp_path)
    before = "1" * 40
    target = "2" * 40
    state = {"head": before, "fetched": False}

    def fake_run_git(root, arguments, **kwargs):
        if arguments == ["rev-parse", "--is-inside-work-tree"]:
            return "true"
        if arguments == ["status", "--porcelain=v1", "--untracked-files=normal"]:
            return ""
        if arguments == ["rev-parse", "--verify", "HEAD"]:
            return state["head"]
        if arguments == ["remote", "get-url", "origin"]:
            return "https://github.com/example/demo.git"
        if arguments == [
            "fetch",
            "--prune",
            "--no-tags",
            "origin",
            "+refs/heads/*:refs/remotes/origin/*",
        ]:
            state["fetched"] = True
            return ""
        if arguments == ["rev-parse", "--verify", f"{target}^{{commit}}"]:
            assert state["fetched"] is True
            return target
        if arguments == [
            "for-each-ref",
            "--format=%(refname)",
            f"--contains={target}",
            "refs/remotes/origin/",
        ]:
            return "refs/remotes/origin/feature/test"
        if arguments == ["checkout", "--detach", "--quiet", target]:
            state["head"] = target
            return ""
        raise AssertionError(arguments)

    monkeypatch.setattr("runner_mcp.source_control._run_git", fake_run_git)
    result = synchronizer.sync_project("demo", target)

    assert result == {
        "project": "demo",
        "commit": target,
        "changed": True,
    }


def test_source_sync_rejects_busy_project_before_network(
    tmp_path: Path,
) -> None:
    synchronizer, _root = _synchronizer(tmp_path, BusyTests())
    with pytest.raises(SourceControlError, match="queued or active"):
        synchronizer.sync_project("demo", "a" * 40)


def test_source_sync_rejects_non_commit_reference(tmp_path: Path) -> None:
    synchronizer, _root = _synchronizer(tmp_path)
    with pytest.raises(SourceControlError, match="full Git object ID"):
        synchronizer.sync_project("demo", "main")


def test_main_only_source_sync_rejects_commit_only_on_feature_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synchronizer, _root = _synchronizer(tmp_path)
    before = "1" * 40
    target = "2" * 40
    state = {"head": before}

    def fake_run_git(root, arguments, **kwargs):
        if arguments == ["rev-parse", "--is-inside-work-tree"]:
            return "true"
        if arguments == ["status", "--porcelain=v1", "--untracked-files=normal"]:
            return ""
        if arguments == ["rev-parse", "--verify", "HEAD"]:
            return state["head"]
        if arguments == ["remote", "get-url", "origin"]:
            return "https://github.com/example/demo.git"
        if arguments == [
            "fetch",
            "--prune",
            "--no-tags",
            "origin",
            "+refs/heads/*:refs/remotes/origin/*",
        ]:
            return ""
        if arguments == ["rev-parse", "--verify", f"{target}^{{commit}}"]:
            return target
        if arguments == [
            "for-each-ref",
            "--format=%(refname)",
            f"--contains={target}",
            "refs/remotes/origin/",
        ]:
            return "refs/remotes/origin/feature/test"
        raise AssertionError(arguments)

    monkeypatch.setattr("runner_mcp.source_control._run_git", fake_run_git)

    with pytest.raises(SourceControlError, match="required remote ref"):
        synchronizer.sync_project_main_commit("demo", target)

    assert state["head"] == before


def test_main_only_source_sync_accepts_origin_main_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synchronizer, _root = _synchronizer(tmp_path)
    before = "1" * 40
    target = "2" * 40
    state = {"head": before}

    def fake_run_git(root, arguments, **kwargs):
        if arguments == ["rev-parse", "--is-inside-work-tree"]:
            return "true"
        if arguments == ["status", "--porcelain=v1", "--untracked-files=normal"]:
            return ""
        if arguments == ["rev-parse", "--verify", "HEAD"]:
            return state["head"]
        if arguments == ["remote", "get-url", "origin"]:
            return "https://github.com/example/demo.git"
        if arguments == [
            "fetch",
            "--prune",
            "--no-tags",
            "origin",
            "+refs/heads/*:refs/remotes/origin/*",
        ]:
            return ""
        if arguments == ["rev-parse", "--verify", f"{target}^{{commit}}"]:
            return target
        if arguments == [
            "for-each-ref",
            "--format=%(refname)",
            f"--contains={target}",
            "refs/remotes/origin/",
        ]:
            return "refs/remotes/origin/main\nrefs/remotes/origin/feature/test"
        if arguments == ["checkout", "--detach", "--quiet", target]:
            state["head"] = target
            return ""
        raise AssertionError(arguments)

    monkeypatch.setattr("runner_mcp.source_control._run_git", fake_run_git)

    result = synchronizer.sync_project_main_commit("demo", target)

    assert result["commit"] == target
    assert result["changed"] is True
