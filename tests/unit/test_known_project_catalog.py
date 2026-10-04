from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.known_project_catalog import (
    KnownProjectRegistrationError,
    discover_known_project_root,
    preflight_known_project,
    prepare_known_project,
    register_known_project,
)


def _registry(root: Path) -> ProjectRegistry:
    return ProjectRegistry(
        projects={
            "runner-mcp": ProjectConfig(
                display_name="Runner MCP",
                repository="Blacksp1d3r/runner-mcp",
                root=root,
            )
        }
    )


def _completed(url: str, *, returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["git"],
        returncode=returncode,
        stdout=url,
        stderr="",
    )


def test_discovers_only_exact_allowlisted_sibling_clone(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()
    calls: list[dict[str, object]] = []

    def runner(argv, **kwargs):
        calls.append({"argv": argv, **kwargs})
        return _completed("https://github.com/Blacksp1d3r/AIfordable.git\n")

    project, root = discover_known_project_root(
        _registry(anchor),
        project_id="aifordable",
        runner=runner,
    )

    assert project.code == "aifordable"
    assert project.repository == "Blacksp1d3r/AIfordable"
    assert root == target.resolve()
    assert calls == [
        {
            "argv": [
                "git",
                "-C",
                str(target.resolve()),
                "config",
                "--get",
                "remote.origin.url",
            ],
            "capture_output": True,
            "text": True,
            "timeout": 5.0,
            "check": False,
            "shell": False,
        }
    ]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/example/AIfordable.git",
        "git@github.com:example/AIfordable.git",
        "https://gitlab.com/Blacksp1d3r/AIfordable.git",
        "file:///tmp/AIfordable",
    ],
)
def test_rejects_spoofed_or_wrong_remote(tmp_path: Path, url: str) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    (tmp_path / "AIfordable").mkdir()

    with pytest.raises(
        KnownProjectRegistrationError,
        match="was not found",
    ):
        discover_known_project_root(
            _registry(anchor),
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: _completed(url + "\n"),
        )


def test_unknown_catalog_id_is_rejected_before_git(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    calls = 0

    def runner(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return _completed("")

    with pytest.raises(
        KnownProjectRegistrationError,
        match="Unknown managed project",
    ):
        discover_known_project_root(
            _registry(anchor),
            project_id="other",
            runner=runner,
        )

    assert calls == 0


def test_missing_sibling_clone_is_rejected(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    with pytest.raises(
        KnownProjectRegistrationError,
        match="was not found",
    ):
        discover_known_project_root(
            _registry(anchor),
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: _completed(""),
        )


def test_symlink_target_is_rejected(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "AIfordable").symlink_to(real, target_is_directory=True)

    with pytest.raises(
        KnownProjectRegistrationError,
        match="was not found",
    ):
        discover_known_project_root(
            _registry(anchor),
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: _completed(
                "https://github.com/Blacksp1d3r/AIfordable.git\n"
            ),
        )


def test_git_failure_is_scrubbed_as_not_found(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    (tmp_path / "AIfordable").mkdir()

    def runner(*_args, **_kwargs):
        raise OSError("private path /secret")

    with pytest.raises(
        KnownProjectRegistrationError,
        match="was not found",
    ) as exc_info:
        discover_known_project_root(
            _registry(anchor),
            project_id="aifordable",
            runner=runner,
        )

    assert "/secret" not in str(exc_info.value)



def test_registration_is_idempotent_for_exact_existing_binding(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    registry = _registry(anchor)
    registry.projects["aifordable"] = ProjectConfig(
        display_name="AIfordable",
        repository="Blacksp1d3r/AIfordable",
        root=tmp_path / "existing-aifordable",
    )

    result = register_known_project(
        tmp_path,
        tmp_path / "projects.yml",
        registry,
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
        add_project_fn=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("add_project must not run")
        ),
    )

    assert result["state"] == "already-registered"
    assert result["code"] == "aifordable"


def test_registration_updates_live_registry_only_after_verified_reload(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()
    registry = _registry(anchor)
    calls: list[dict[str, object]] = []

    def add_project_fn(config_dir, **kwargs):
        calls.append({"config_dir": config_dir, **kwargs})
        return {
            "code": "aifordable",
            "name": "AIfordable",
            "repository": "Blacksp1d3r/AIfordable",
            "environment": "staging",
            "adapter": "generic",
        }

    refreshed = ProjectRegistry(
        projects={
            **registry.projects,
            "aifordable": ProjectConfig(
                display_name="AIfordable",
                repository="Blacksp1d3r/AIfordable",
                root=target,
            ),
        }
    )

    result = register_known_project(
        tmp_path,
        tmp_path / "projects.yml",
        registry,
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: _completed(
            "git@github.com:Blacksp1d3r/AIfordable.git\n"
        ),
        add_project_fn=add_project_fn,
        reload_fn=lambda _path: refreshed,
    )

    assert result["state"] == "registered"
    assert "aifordable" in registry.projects
    assert calls[0]["root"] == target.resolve()
    assert calls[0]["repository"] == "Blacksp1d3r/AIfordable"


def test_registration_rejects_reload_without_expected_project(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()
    registry = _registry(anchor)

    with pytest.raises(
        KnownProjectRegistrationError,
        match="could not be verified",
    ):
        register_known_project(
            tmp_path,
            tmp_path / "projects.yml",
            registry,
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: _completed(
                "https://github.com/Blacksp1d3r/AIfordable.git\n"
            ),
            add_project_fn=lambda *_args, **_kwargs: {
                "code": "aifordable",
                "name": "AIfordable",
                "repository": "Blacksp1d3r/AIfordable",
                "environment": "staging",
                "adapter": "generic",
            },
            reload_fn=lambda _path: _registry(anchor),
        )

    assert "aifordable" not in registry.projects



def test_prepare_known_project_clones_only_fixed_catalog_target(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    registry = _registry(anchor)
    calls: list[dict[str, object]] = []

    def runner(argv, **kwargs):
        calls.append({"argv": argv, **kwargs})
        if "clone" in argv:
            target = Path(argv[-1])
            target.mkdir()
            return _completed("")
        return _completed("https://github.com/Blacksp1d3r/AIfordable.git\n")

    result = prepare_known_project(
        registry,
        project_id="aifordable",
        runner=runner,
    )

    assert result["state"] == "prepared"
    target = tmp_path / "AIfordable"
    assert target.is_dir()
    clone_call = calls[0]
    assert clone_call["argv"][:-1] == [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "clone",
        "--origin",
        "origin",
        "--no-tags",
        "--",
        "https://github.com/Blacksp1d3r/AIfordable.git",
    ]
    assert Path(clone_call["argv"][-1]).parent == tmp_path
    assert Path(clone_call["argv"][-1]).name.startswith(".aifordable-clone-")
    assert clone_call["cwd"] == str(tmp_path)
    assert clone_call["shell"] is False
    assert clone_call["timeout"] == 180.0


def test_prepare_known_project_is_idempotent_for_exact_existing_clone(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()

    result = prepare_known_project(
        _registry(anchor),
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: _completed(
            "git@github.com:Blacksp1d3r/AIfordable.git\n"
        ),
    )

    assert result["state"] == "already-prepared"


def test_prepare_known_project_refuses_wrong_existing_destination(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()

    with pytest.raises(
        KnownProjectRegistrationError,
        match="unexpected repository",
    ):
        prepare_known_project(
            _registry(anchor),
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: _completed(
                "https://github.com/example/AIfordable.git\n"
            ),
        )


def test_prepare_known_project_cleans_failed_temporary_clone(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    def runner(argv, **kwargs):
        target = Path(argv[-1])
        target.mkdir()
        (target / "partial").write_text("partial", encoding="utf-8")
        return _completed("", returncode=1)

    with pytest.raises(KnownProjectRegistrationError, match="clone failed"):
        prepare_known_project(
            _registry(anchor),
            project_id="aifordable",
            runner=runner,
        )

    assert not (tmp_path / "AIfordable").exists()
    assert not any(path.name.startswith(".aifordable-clone-") for path in tmp_path.iterdir())


def test_prepare_known_project_rejects_ambiguous_parent_roots(tmp_path: Path) -> None:
    first = tmp_path / "one" / "runner-mcp"
    second = tmp_path / "two" / "other"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    registry = ProjectRegistry(
        projects={
            "runner-mcp": ProjectConfig(
                display_name="Runner MCP",
                repository="Blacksp1d3r/runner-mcp",
                root=first,
            ),
            "other": ProjectConfig(
                display_name="Other",
                repository="example/other",
                root=second,
            ),
        }
    )

    with pytest.raises(
        KnownProjectRegistrationError,
        match="destination is ambiguous",
    ):
        prepare_known_project(
            registry,
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("git must not run")
            ),
        )



def test_known_project_preflight_reports_missing_destination(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
    )

    assert result == {
        "code": "aifordable",
        "repository": "Blacksp1d3r/AIfordable",
        "state": "ready-to-prepare",
    }


def test_known_project_preflight_reports_exact_existing_clone(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: _completed(
            "https://github.com/Blacksp1d3r/AIfordable.git\n"
        ),
    )

    assert result["state"] == "already-prepared"


def test_known_project_preflight_reports_wrong_existing_clone(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "AIfordable"
    target.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="aifordable",
        runner=lambda *_args, **_kwargs: _completed(
            "https://github.com/example/AIfordable.git\n"
        ),
    )

    assert result["state"] == "wrong-repository"


def test_known_project_preflight_reports_ambiguous_parent(tmp_path: Path) -> None:
    first = tmp_path / "one" / "runner-mcp"
    second = tmp_path / "two" / "other"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    registry = ProjectRegistry(
        projects={
            "runner-mcp": ProjectConfig(
                display_name="Runner MCP",
                repository="Blacksp1d3r/runner-mcp",
                root=first,
            ),
            "other": ProjectConfig(
                display_name="Other",
                repository="example/other",
                root=second,
            ),
        }
    )

    result = preflight_known_project(
        registry,
        project_id="aifordable",
    )

    assert result["state"] == "ambiguous-parent"
