"""Multi-parent managed-project discovery stays read-only and fail-closed."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.known_project_catalog import (
    KnownProjectRegistrationError,
    preflight_known_project,
    prepare_known_project,
)


def _registry(tmp_path: Path) -> tuple[ProjectRegistry, Path, Path]:
    left = tmp_path / "left"
    right = tmp_path / "right"
    first = left / "runner-mcp"
    second = right / "safety"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    registry = ProjectRegistry(
        projects={
            "runner-mcp": ProjectConfig(
                display_name="Runner MCP",
                repository="Blacksp1d3r/runner-mcp",
                root=first,
            ),
            "safety": ProjectConfig(
                display_name="Safety",
                repository="Blacksp1d3r/safety",
                root=second,
            ),
        }
    )
    return registry, left, right


def _exact_repo_runner(argv, **kwargs):
    assert argv[0:2] == ["git", "-C"]
    assert argv[3:] == ["config", "--get", "remote.origin.url"]
    assert kwargs["shell"] is False
    return subprocess.CompletedProcess(
        argv, 0, stdout="https://github.com/Blacksp1d3r/AIfordable.git\n", stderr=""
    )


def test_mixed_parents_one_existing_exact_clone_is_ready(tmp_path: Path) -> None:
    registry, left, _right = _registry(tmp_path)
    candidate = left / "AIfordable"
    candidate.mkdir()

    result = preflight_known_project(
        registry, project_id="aifordable", runner=_exact_repo_runner
    )
    assert result == {
        "code": "aifordable",
        "repository": "Blacksp1d3r/AIfordable",
        "state": "already-prepared",
    }
    assert candidate.is_dir()


def test_mixed_parents_prepare_existing_clone_never_clones(tmp_path: Path) -> None:
    registry, left, _right = _registry(tmp_path)
    candidate = left / "AIfordable"
    candidate.mkdir()
    result = prepare_known_project(
        registry, project_id="aifordable", runner=_exact_repo_runner
    )
    assert result == {
        "code": "aifordable",
        "name": "AIfordable",
        "repository": "Blacksp1d3r/AIfordable",
        "state": "already-prepared",
    }
    assert sorted(path.name for path in left.iterdir()) == ["AIfordable", "runner-mcp"]


@pytest.mark.parametrize("candidate_count", [0, 2])
def test_mixed_parents_without_unique_clone_refuse_destination(
    tmp_path: Path, candidate_count: int,
) -> None:
    registry, left, right = _registry(tmp_path)
    for parent in [left, right][:candidate_count]:
        (parent / "AIfordable").mkdir()

    result = preflight_known_project(
        registry, project_id="aifordable", runner=_exact_repo_runner
    )
    assert result["state"] == "ambiguous-parent"
    with pytest.raises(
        KnownProjectRegistrationError, match="destination is ambiguous"
    ):
        prepare_known_project(registry, project_id="aifordable", runner=_exact_repo_runner)


def test_wrong_origin_does_not_create_readiness(tmp_path: Path) -> None:
    registry, left, _right = _registry(tmp_path)
    (left / "AIfordable").mkdir()

    def wrong_origin(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv, 0, stdout="https://github.com/Blacksp1d3r/not-aifordable.git\n",
            stderr="",
        )

    result = preflight_known_project(
        registry, project_id="aifordable", runner=wrong_origin
    )
    assert result["state"] == "ambiguous-parent"


def test_symlink_candidate_is_never_treated_as_clone(tmp_path: Path) -> None:
    registry, left, right = _registry(tmp_path)
    (left / "AIfordable").symlink_to(right / "safety", target_is_directory=True)

    def no_git(*args, **kwargs):
        raise AssertionError("symlinked candidate cannot be inspected by Git")

    assert preflight_known_project(
        registry, project_id="aifordable", runner=no_git
    )["state"] == "ambiguous-parent"


def test_single_parent_old_prepare_readiness_unchanged(tmp_path: Path) -> None:
    registry, _left, _right = _registry(tmp_path)
    registry.projects.pop("safety")
    assert preflight_known_project(
        registry, project_id="aifordable", runner=_exact_repo_runner
    )["state"] == "ready-to-prepare"


def test_explicit_configured_project_anchor_disambiguates_without_host_path(
    tmp_path: Path,
) -> None:
    registry, left, right = _registry(tmp_path)

    def no_git(*_args, **_kwargs):
        raise AssertionError("preflight must not contact Git for absent target")

    assert preflight_known_project(
        registry, project_id="enercue", anchor_project_id="runner-mcp", runner=no_git,
    ) == {
        "code": "enercue",
        "repository": "Blacksp1d3r/EnerCue",
        "state": "ready-to-prepare",
    }
    assert preflight_known_project(
        registry, project_id="enercue", anchor_project_id="safety", runner=no_git,
    )["state"] == "ready-to-prepare"
    assert not (left / "EnerCue").exists()
    assert not (right / "EnerCue").exists()
    assert preflight_known_project(
        registry, project_id="enercue", runner=no_git,
    )["state"] == "ambiguous-parent"


@pytest.mark.parametrize("invalid", ["not-configured", "runner-mcp/../safety", "", None])
def test_invalid_anchor_denied_without_cloning(tmp_path: Path, invalid) -> None:
    registry, _left, _right = _registry(tmp_path)
    if invalid is None:
        # None deliberately retains the old ambiguous-parent behaviour.
        assert preflight_known_project(
            registry, project_id="enercue",
            anchor_project_id=None,
        )["state"] == "ambiguous-parent"
        return

    def no_git(*_args, **_kwargs):
        raise AssertionError("unverified anchor cannot contact Git")

    with pytest.raises(KnownProjectRegistrationError, match="already configured"):
        preflight_known_project(
            registry, project_id="enercue",
            anchor_project_id=invalid, runner=no_git,
        )
    with pytest.raises(KnownProjectRegistrationError, match="already configured"):
        prepare_known_project(
            registry, project_id="enercue",
            anchor_project_id=invalid, runner=no_git,
        )


def test_explicit_anchor_rejects_existing_exact_clone_on_other_parent(
    tmp_path: Path,
) -> None:
    registry, left, right = _registry(tmp_path)
    (left / "EnerCue").mkdir()
    def exact(argv, **_kwargs):
        return subprocess.CompletedProcess(
            argv, 0, stdout="https://github.com/Blacksp1d3r/EnerCue.git\n",
            stderr="",
        )

    assert preflight_known_project(
        registry, project_id="enercue", anchor_project_id="safety", runner=exact,
    )["state"] == "exact-clone-elsewhere"
    with pytest.raises(KnownProjectRegistrationError, match="another parent"):
        prepare_known_project(
            registry, project_id="enercue", anchor_project_id="safety",
            runner=exact,
        )
    assert not (right / "EnerCue").exists()
    assert prepare_known_project(
        registry, project_id="enercue",
        anchor_project_id="runner-mcp", runner=exact,
    )["state"] == "already-prepared"


def test_explicit_anchor_blocks_symlink_target(tmp_path: Path) -> None:
    registry, left, right = _registry(tmp_path)
    (right / "EnerCue").symlink_to(left / "runner-mcp", target_is_directory=True)
    assert preflight_known_project(
        registry, project_id="enercue", anchor_project_id="safety",
    )["state"] == "unsafe-destination"
    with pytest.raises(KnownProjectRegistrationError, match="occupied"):
        prepare_known_project(
            registry, project_id="enercue", anchor_project_id="safety",
        )


def test_prepare_clones_only_below_the_selected_existing_project_parent(
    tmp_path: Path,
) -> None:
    registry, left, right = _registry(tmp_path)
    calls: list[list[str]] = []

    def fake_git(argv, **kwargs):
        calls.append(argv)
        assert kwargs.get("shell", False) is False
        if "clone" in argv:
            assert kwargs["cwd"] == str(right)
            Path(argv[-1]).mkdir()
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if "config" in argv:
            return subprocess.CompletedProcess(
                argv, 0,
                stdout="https://github.com/Blacksp1d3r/EnerCue.git\n",
                stderr="",
            )
        if "checkout" in argv:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        raise AssertionError("unapproved Git action")

    result = prepare_known_project(
        registry, project_id="enercue", anchor_project_id="safety",
        runner=fake_git, github_token=None,
    )
    assert result["state"] == "prepared"
    assert (right / "EnerCue").is_dir()
    assert not (left / "EnerCue").exists()
    assert len([cmd for cmd in calls if "clone" in cmd]) == 1
    assert prepare_known_project(
        registry, project_id="enercue", anchor_project_id="safety",
        runner=fake_git,
    )["state"] == "already-prepared"
