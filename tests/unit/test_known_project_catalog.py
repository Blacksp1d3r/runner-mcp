from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.known_project_catalog import (
    KNOWN_PROJECTS,
    KnownProjectRegistrationError,
    discover_known_project_root,
    preflight_known_project,
    preflight_known_project_source,
    prepare_known_project,
    register_known_project,
    resolve_known_project_github_token,
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
            Path(argv[-1]).mkdir()
            return _completed("")
        if "checkout" in argv:
            return _completed("")
        return _completed("https://github.com/Blacksp1d3r/AIfordable.git\n")

    result = prepare_known_project(
        registry,
        project_id="aifordable",
        runner=runner,
        github_token="private-token",
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
        "--no-checkout",
        "--branch",
        "main",
        "--single-branch",
        "--",
        "https://github.com/Blacksp1d3r/AIfordable.git",
    ]
    assert Path(clone_call["argv"][-1]).parent == tmp_path
    assert Path(clone_call["argv"][-1]).name.startswith(".aifordable-clone-")
    assert clone_call["cwd"] == str(tmp_path)
    assert clone_call["stdin"] is subprocess.DEVNULL
    assert clone_call["shell"] is False
    assert clone_call["timeout"] == 180.0
    assert "private-token" not in " ".join(clone_call["argv"])
    assert clone_call["env"]["GIT_CONFIG_COUNT"] == "1"
    assert clone_call["env"]["GIT_CONFIG_KEY_0"] == (
        "http.https://github.com/.extraheader"
    )
    assert clone_call["env"]["GIT_CONFIG_VALUE_0"].startswith(
        "AUTHORIZATION: basic "
    )

    checkout_call = calls[1]
    assert checkout_call["argv"][-3:] == [
        "checkout",
        "--detach",
        "origin/main",
    ]
    assert "GIT_CONFIG_VALUE_0" not in checkout_call["env"]
    assert checkout_call["env"]["HOME"] == "/nonexistent"


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


def test_prepare_known_project_rejects_invalid_github_token_before_clone(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    with pytest.raises(
        KnownProjectRegistrationError,
        match="credential is invalid",
    ):
        prepare_known_project(
            _registry(anchor),
            project_id="aifordable",
            runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("git must not run")
            ),
            github_token="bad\ntoken",
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


def test_rasff_lens_is_bounded_known_python_project() -> None:
    project = KNOWN_PROJECTS["rasff-lens"]
    assert project.code == "rasff-lens"
    assert project.display_name == "RASFF Lens"
    assert project.repository == "Blacksp1d3r/rasff-lens"
    assert project.directory_name == "rasff-lens"
    assert project.adapter == "python"


def test_rasff_lens_preflight_reports_ready_to_prepare(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="rasff-lens",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
    )

    assert result == {
        "code": "rasff-lens",
        "repository": "Blacksp1d3r/rasff-lens",
        "state": "ready-to-prepare",
    }


def test_rasff_lens_existing_clone_requires_exact_repository(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "rasff-lens"
    target.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="rasff-lens",
        runner=lambda *_args, **_kwargs: _completed(
            "https://github.com/Blacksp1d3r/rasff-lens.git\n"
        ),
    )
    assert result["state"] == "already-prepared"


@pytest.mark.parametrize(
    ("project_id", "display_name", "repository", "directory_name", "adapter"),
    [
        ("bewind", "Bewind", "Blacksp1d3r/bewind", "bewind", "python"),
        ("enercue", "EnerCue", "Blacksp1d3r/EnerCue", "EnerCue", "generic"),
        ("patrimai", "PatrimAI", "Blacksp1d3r/PatrimAI", "PatrimAI", "generic"),
        ("unifiedesg", "UnifiedESG", "Blacksp1d3r/UnifiedESG", "UnifiedESG", "python"),
        ("pastentrance", "PastEntrance", "Blacksp1d3r/PastEntrance", "PastEntrance", "generic"),
        ("safety", "Safety!", "Blacksp1d3r/safety", "safety", "generic"),
        ("rasff-lens", "RASFF Lens", "Blacksp1d3r/rasff-lens", "rasff-lens", "python"),
    ],
)
def test_aifordable_managed_project_catalog_is_fixed_and_bounded(
    project_id: str,
    display_name: str,
    repository: str,
    directory_name: str,
    adapter: str,
) -> None:
    project = KNOWN_PROJECTS[project_id]
    assert project.code == project_id
    assert project.display_name == display_name
    assert project.repository == repository
    assert project.directory_name == directory_name
    assert project.adapter == adapter


@pytest.mark.parametrize(
    ("project_id", "repository"),
    [
        ("bewind", "Blacksp1d3r/bewind"),
        ("enercue", "Blacksp1d3r/EnerCue"),
        ("patrimai", "Blacksp1d3r/PatrimAI"),
        ("unifiedesg", "Blacksp1d3r/UnifiedESG"),
        ("pastentrance", "Blacksp1d3r/PastEntrance"),
        ("safety", "Blacksp1d3r/safety"),
        ("rasff-lens", "Blacksp1d3r/rasff-lens"),
    ],
)
def test_aifordable_managed_project_preflight_is_ready_without_clone(
    tmp_path: Path,
    project_id: str,
    repository: str,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id=project_id,
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
    )

    assert result == {
        "code": project_id,
        "repository": repository,
        "state": "ready-to-prepare",
    }


def test_known_project_source_preflight_requires_configured_credential() -> None:
    result = preflight_known_project_source(
        project_id="rasff-lens",
        github_token=None,
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
    )
    assert result["credential_configured"] is False
    assert result["reason_code"] == "credential-unconfigured"


def test_known_project_source_preflight_reports_ready_for_exact_main_ref() -> None:
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=("f" * 40) + "\trefs/heads/main\n",
            stderr="",
        )

    result = preflight_known_project_source(
        project_id="rasff-lens",
        github_token="private-token",
        runner=runner,
    )
    assert result["credential_configured"] is True
    assert result["source_reachable"] is True
    assert result["main_ref_available"] is True
    assert result["reason_code"] == "ready"
    argv, kwargs = calls[0]
    assert argv[-2:] == [
        "https://github.com/Blacksp1d3r/rasff-lens.git",
        "refs/heads/main",
    ]
    assert "private-token" not in " ".join(argv)
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert kwargs["env"]["GIT_CONFIG_KEY_0"] == (
        "http.https://github.com/.extraheader"
    )


def test_known_project_source_preflight_scrubs_source_failure() -> None:
    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(
            args=argv,
            returncode=128,
            stdout="",
            stderr="fatal: secret private detail",
        )

    result = preflight_known_project_source(
        project_id="bewind",
        github_token="private-token",
        runner=runner,
    )
    assert result == {
        "code": "bewind",
        "repository": "Blacksp1d3r/bewind",
        "credential_configured": True,
        "source_reachable": False,
        "main_ref_available": False,
        "reason_code": "source-unreachable-or-unauthorized",
    }


def test_known_project_preflight_reports_unwritable_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    monkeypatch.setattr(
        "runner_mcp.known_project_catalog.os.access",
        lambda path, mode: False,
    )

    result = preflight_known_project(
        _registry(anchor),
        project_id="bewind",
    )

    assert result == {
        "code": "bewind",
        "repository": "Blacksp1d3r/bewind",
        "state": "parent-not-writable",
    }


def test_prepare_known_project_rejects_unwritable_parent_before_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    monkeypatch.setattr(
        "runner_mcp.known_project_catalog.os.access",
        lambda path, mode: False,
    )

    with pytest.raises(
        KnownProjectRegistrationError,
        match="destination is not writable",
    ):
        prepare_known_project(
            _registry(anchor),
            project_id="bewind",
            runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("git must not run")
            ),
            github_token="private-token",
        )


def test_runner_fabric_is_bounded_known_python_project() -> None:
    project = KNOWN_PROJECTS["runner-fabric"]
    assert project.code == "runner-fabric"
    assert project.display_name == "Runner Fabric"
    assert project.repository == "Blacksp1d3r/Runner-Fabric"
    assert project.directory_name == "Runner-Fabric"
    assert project.adapter == "python"


def test_runner_fabric_preflight_reports_ready_to_prepare(tmp_path: Path) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="runner-fabric",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("git must not run")
        ),
    )

    assert result == {
        "code": "runner-fabric",
        "repository": "Blacksp1d3r/Runner-Fabric",
        "state": "ready-to-prepare",
    }


def test_runner_fabric_existing_clone_requires_exact_repository(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    target = tmp_path / "Runner-Fabric"
    target.mkdir()

    result = preflight_known_project(
        _registry(anchor),
        project_id="runner-fabric",
        runner=lambda *_args, **_kwargs: _completed(
            "https://github.com/Blacksp1d3r/Runner-Fabric.git\n"
        ),
    )

    assert result["state"] == "already-prepared"


def _make_private_local_git_source(tmp_path: Path) -> tuple[Path, str]:
    seed = tmp_path / "seed"
    seed.mkdir()
    subprocess.run(["git", "init", "-q", str(seed)], check=True)
    subprocess.run(
        ["git", "-C", str(seed), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(seed), "config", "user.name", "Runner MCP Test"],
        check=True,
    )
    (seed / "README.md").write_text("local source\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(seed), "add", "README.md"], check=True)
    subprocess.run(
        ["git", "-C", str(seed), "commit", "-q", "-m", "seed"],
        check=True,
    )
    revision = subprocess.run(
        ["git", "-C", str(seed), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source = tmp_path / "trusted-source.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(source)],
        check=True,
    )
    os.chmod(source, 0o700)
    return source, revision


def _local_source_binding(
    *,
    project_id: str,
    repository: str,
    source: Path,
    revision: str,
) -> str:
    return json.dumps(
        {
            "schemaVersion": "runner-mcp/known-project-local-sources/v1",
            "projects": {
                project_id: {
                    "repository": repository,
                    "source": str(source),
                    "expectedRevision": revision,
                }
            },
        }
    )


def test_known_project_source_preflight_prefers_trusted_local_source(
    tmp_path: Path,
) -> None:
    source, revision = _make_private_local_git_source(tmp_path)
    raw = _local_source_binding(
        project_id="runner-fabric",
        repository="Blacksp1d3r/Runner-Fabric",
        source=source,
        revision=revision,
    )

    result = preflight_known_project_source(
        project_id="runner-fabric",
        github_token=None,
        local_source_bindings_raw=raw,
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network Git must not run")
        ),
    )

    assert result["source_reachable"] is True
    assert result["main_ref_available"] is True
    assert result["reason_code"] == "local-source-ready"
    assert result["credential_configured"] is False


def test_prepare_known_project_materializes_exact_trusted_local_revision(
    tmp_path: Path,
) -> None:
    anchor = tmp_path / "runner-mcp"
    anchor.mkdir()
    source, revision = _make_private_local_git_source(tmp_path)
    raw = _local_source_binding(
        project_id="runner-fabric",
        repository="Blacksp1d3r/Runner-Fabric",
        source=source,
        revision=revision,
    )

    result = prepare_known_project(
        _registry(anchor),
        project_id="runner-fabric",
        github_token=None,
        local_source_bindings_raw=raw,
    )

    assert result["state"] == "prepared-local"
    target = tmp_path / "Runner-Fabric"
    assert target.is_dir()
    observed = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert observed == revision
    origin = subprocess.run(
        ["git", "-C", str(target), "config", "--get", "remote.origin.url"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert origin == "https://github.com/Blacksp1d3r/Runner-Fabric.git"


def test_malformed_trusted_local_source_fails_closed_before_github(
    tmp_path: Path,
) -> None:
    raw = json.dumps(
        {
            "schemaVersion": "runner-mcp/known-project-local-sources/v1",
            "projects": {
                "runner-fabric": {
                    "repository": "Blacksp1d3r/Runner-Fabric",
                    "source": str(tmp_path / "missing"),
                    "expectedRevision": "a" * 40,
                }
            },
        }
    )

    with pytest.raises(
        KnownProjectRegistrationError,
        match="configuration is invalid",
    ):
        preflight_known_project_source(
            project_id="runner-fabric",
            github_token="private-token",
            local_source_bindings_raw=raw,
            runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("GitHub fallback must not hide an invalid trusted binding")
            ),
        )



def test_bewind_uses_dedicated_source_credential() -> None:
    result = resolve_known_project_github_token(
        project_id="bewind",
        global_token="global-token",
        private_values={"RUNNER_MCP_BEWIND_GITHUB_TOKEN": "bewind-token"},
    )

    assert result == "bewind-token"


@pytest.mark.parametrize(
    "project_id",
    ["aifordable", "rasff-lens", "runner-fabric", "safety"],
)
def test_other_projects_never_consume_bewind_source_credential(
    project_id: str,
) -> None:
    result = resolve_known_project_github_token(
        project_id=project_id,
        global_token="global-token",
        private_values={"RUNNER_MCP_BEWIND_GITHUB_TOKEN": "bewind-token"},
    )

    assert result == "global-token"


def test_bewind_without_dedicated_source_credential_preserves_global_fallback() -> None:
    result = resolve_known_project_github_token(
        project_id="bewind",
        global_token="global-token",
        private_values={},
    )

    assert result == "global-token"


def test_invalid_bewind_dedicated_credential_fails_closed() -> None:
    with pytest.raises(
        KnownProjectRegistrationError,
        match="credential",
    ):
        resolve_known_project_github_token(
            project_id="bewind",
            global_token="global-token",
            private_values={
                "RUNNER_MCP_BEWIND_GITHUB_TOKEN": "bad\ntoken",
            },
        )


def test_unknown_project_cannot_select_private_credential() -> None:
    with pytest.raises(
        KnownProjectRegistrationError,
        match="Unknown managed project",
    ):
        resolve_known_project_github_token(
            project_id="other",
            global_token="global-token",
            private_values={
                "RUNNER_MCP_BEWIND_GITHUB_TOKEN": "bewind-token",
            },
        )
