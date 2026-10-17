"""Multi-parent managed-project discovery stays read-only and fail-closed."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.known_project_catalog import (
    KnownProjectRegistrationError,
    inspect_known_project_candidates,
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


def test_candidate_inventory_reports_counts_without_paths(tmp_path: Path) -> None:
    registry, left, right = _registry(tmp_path)
    (left / "AIfordable").mkdir()
    (right / "AIfordable").mkdir()

    calls = 0

    def mixed_origin(argv, **kwargs):
        nonlocal calls
        calls += 1
        repository = (
            "https://github.com/Blacksp1d3r/AIfordable.git\n"
            if calls == 1
            else "https://github.com/example/not-aifordable.git\n"
        )
        return subprocess.CompletedProcess(argv, 0, stdout=repository, stderr="")

    result = inspect_known_project_candidates(
        registry,
        project_id="aifordable",
        runner=mixed_origin,
    )

    assert result == {
        "code": "aifordable",
        "repository": "Blacksp1d3r/AIfordable",
        "configured_parent_count": 2,
        "candidate_count": 2,
        "exact_repository_count": 1,
        "missing_count": 0,
        "symlink_count": 0,
        "not_directory_count": 0,
        "unavailable_count": 0,
        "repository_unreadable_count": 0,
        "wrong_repository_count": 1,
        "state": "unique-exact-clone",
    }
    rendered = repr(result)
    assert str(left) not in rendered
    assert str(right) not in rendered


def test_candidate_inventory_distinguishes_missing_and_symlink(tmp_path: Path) -> None:
    registry, left, right = _registry(tmp_path)
    (left / "AIfordable").symlink_to(right / "safety", target_is_directory=True)

    result = inspect_known_project_candidates(
        registry,
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("symlink and missing candidates must not invoke git")
        ),
    )

    assert result["configured_parent_count"] == 2
    assert result["candidate_count"] == 1
    assert result["exact_repository_count"] == 0
    assert result["symlink_count"] == 1
    assert result["missing_count"] == 1
    assert result["state"] == "no-exact-clone"


def test_single_parent_old_prepare_readiness_unchanged(tmp_path: Path) -> None:
    registry, _left, _right = _registry(tmp_path)
    registry.projects.pop("safety")
    assert preflight_known_project(
        registry, project_id="aifordable", runner=_exact_repo_runner
    )["state"] == "ready-to-prepare"
