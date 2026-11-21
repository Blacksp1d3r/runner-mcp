"""Synthetic, offline checks for the no-dispatch local source gate."""

import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry, TestProfile
from runner_mcp.local_test_source_preflight import (
    LocalTestSourcePreflightError,
    inspect_local_test_source,
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["/usr/bin/git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def candidate(tmp_path: Path):
    root = tmp_path / "hive-source"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.name", "Local Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "remote", "add", "origin", "https://github.com/Blacksp1d3r/Hive.git")
    (root / "sample.txt").write_text("offline fixture\n", encoding="utf-8")
    git(root, "add", "sample.txt")
    git(root, "commit", "-m", "source fixture")
    revision = git(root, "rev-parse", "HEAD")
    profile = TestProfile(argv=["/usr/bin/python3", "-m", "unittest"])
    project = ProjectConfig(
        display_name="Hive",
        repository="Blacksp1d3r/Hive",
        root=root,
        environment="staging",
        test_profiles={"python-tests": profile},
    )
    return ProjectRegistry(projects={"hive": project}), root, revision


def inspect(registry: ProjectRegistry, revision: str):
    return inspect_local_test_source(
        registry,
        project="hive",
        suite="python-tests",
        expected_sha=revision,
    )


def test_matching_clean_registered_source_is_never_dispatch_authority(
    tmp_path: Path,
) -> None:
    registry, root, revision = candidate(tmp_path)
    before_status = git(root, "status", "--porcelain")
    result = inspect(registry, revision)
    assert result["state"] == "source_checked_wait_f26_guest"
    assert result["source_sha"] == revision
    assert result["checkout_clean"] is True
    assert result["configured_origin_matches"] is True
    assert result["dispatch_authorized"] is False
    assert result["host_local_fallback_allowed"] is False
    assert result["remote_reachability_verified"] is False
    assert result["fabric_lease_verified"] is False
    assert result["guest_identity_verified"] is False
    assert result["source_changed"] is False
    assert str(root) not in repr(result)
    assert "/usr/bin/python3" not in repr(result)
    assert git(root, "rev-parse", "HEAD") == revision
    assert git(root, "status", "--porcelain") == before_status


@pytest.mark.parametrize(
    ("project", "suite", "sha", "reason"),
    [
        ("unknown", "python-tests", "a" * 40, "unknown_or_disabled_project"),
        ("hive", "unknown", "a" * 40, "test_profile_not_registered"),
        ("hive", "python-tests", "latest", "invalid_exact_source_sha"),
        ("hive", "python-tests", "A" * 40, "invalid_exact_source_sha"),
        ("../hive", "python-tests", "a" * 40, "invalid_project_or_profile"),
        ("hive", "python;sh", "a" * 40, "invalid_project_or_profile"),
    ],
)
def test_bad_requests_fail_before_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    project: str,
    suite: str,
    sha: str,
    reason: str,
) -> None:
    registry, _root, _revision = candidate(tmp_path)

    def unexpected(_root):
        raise AssertionError("No source inspection expected")

    monkeypatch.setattr(
        "runner_mcp.local_test_source_preflight.clean_head", unexpected
    )
    with pytest.raises(LocalTestSourcePreflightError, match=reason):
        inspect_local_test_source(
            registry, project=project, suite=suite, expected_sha=sha
        )


def test_wrong_origin_fails_closed(tmp_path: Path) -> None:
    registry, root, revision = candidate(tmp_path)
    git(root, "remote", "set-url", "origin", "https://github.com/example/other.git")
    with pytest.raises(
        LocalTestSourcePreflightError, match="checkout_or_origin_not_verified"
    ):
        inspect(registry, revision)


def test_dirty_tracked_or_untracked_source_fails_closed(tmp_path: Path) -> None:
    registry, root, revision = candidate(tmp_path)
    (root / "other.txt").write_text("not committed", encoding="utf-8")
    with pytest.raises(
        LocalTestSourcePreflightError, match="checkout_or_origin_not_verified"
    ):
        inspect(registry, revision)


def test_exact_sha_mismatch_never_upgrades_to_pass(tmp_path: Path) -> None:
    registry, _root, revision = candidate(tmp_path)
    other = ("0" if revision[0] != "0" else "1") + revision[1:]
    with pytest.raises(
        LocalTestSourcePreflightError, match="exact_source_sha_mismatch"
    ):
        inspect(registry, other)


def test_submodule_metadata_refused(tmp_path: Path) -> None:
    registry, root, revision = candidate(tmp_path)
    (root / ".gitmodules").write_text("[submodule]\n", encoding="utf-8")
    with pytest.raises(
        LocalTestSourcePreflightError, match="checkout_or_origin_not_verified"
    ):
        inspect(registry, revision)


def test_symlinked_project_root_refused(tmp_path: Path) -> None:
    registry, root, revision = candidate(tmp_path)
    link = tmp_path / "linked"
    link.symlink_to(root, target_is_directory=True)
    registry.projects["hive"].root = link
    with pytest.raises(
        LocalTestSourcePreflightError, match="checkout_or_origin_not_verified"
    ):
        inspect(registry, revision)


def test_non_staging_project_refused(tmp_path: Path) -> None:
    registry, _root, revision = candidate(tmp_path)
    registry.projects["hive"].environment = "protected"
    with pytest.raises(
        LocalTestSourcePreflightError, match="non_staging_source_not_admitted"
    ):
        inspect(registry, revision)


def test_no_registry_fails_closed() -> None:
    with pytest.raises(
        LocalTestSourcePreflightError, match="invalid_project_registry"
    ):
        inspect_local_test_source(
            None, project="hive", suite="python-tests", expected_sha="a" * 40
        )
