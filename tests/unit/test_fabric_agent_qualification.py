from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp import fabric_agent_qualification as qualification
from runner_mcp.fabric_agent_qualification import (
    FabricAgentQualificationError,
    fabric_agent_qualification_configured,
    run_fabric_agent_qualification_process,
)
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


def _private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "private"
    paths = install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    return paths


def _append_bridge(paths, *, endpoint: str = "http://127.0.0.1:9020/mcp") -> str:
    token = "q" * 48
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"RUNNER_FABRIC_AGENT_RESOURCE_URL={endpoint}\n")
        handle.write(f"RUNNER_FABRIC_AGENT_BEARER_TOKEN={token}\n")
    return token


def test_qualification_agent_is_optional_until_bridge_is_complete(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)

    assert fabric_agent_qualification_configured(paths.config_dir) is False

    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(
            "RUNNER_FABRIC_AGENT_RESOURCE_URL=http://127.0.0.1:9020/mcp\n"
        )

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is incomplete",
    ):
        fabric_agent_qualification_configured(paths.config_dir)


def test_qualification_agent_rejects_non_loopback_endpoint(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths, endpoint="http://fabric.example.invalid:9020/mcp")

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is invalid",
    ):
        fabric_agent_qualification_configured(paths.config_dir)


def test_qualification_agent_forwards_only_fixed_optional_target_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    token = _append_bridge(paths)
    external_config = tmp_path / "private-target.json"
    external_config.write_text("{}\n", encoding="utf-8")
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(f"RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG={external_config}\n")
        handle.write("UNRELATED_PRIVATE_VALUE=must-not-leak\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == token
    assert environment["RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG"] == str(external_config)
    assert "UNRELATED_PRIVATE_VALUE" not in environment
    assert set(environment) == {
        "HOME",
        "PATH",
        "LANG",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN",
        "RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG",
    }


def test_qualification_agent_rejects_relative_external_target_config(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG=relative.json\n")

    with pytest.raises(
        FabricAgentQualificationError,
        match="configuration is invalid",
    ):
        run_fabric_agent_qualification_process(paths.config_dir, execve=lambda *_: object())


def test_qualification_agent_execs_only_fixed_qualification_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    token = _append_bridge(paths)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert (
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=fake_execve,
        )
        == 0
    )

    assert captured["path"] == str(executable)
    assert captured["argv"] == [str(executable), "agent-serve-qualification"]
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["RUNNER_FABRIC_AGENT_RESOURCE_URL"] == (
        "http://127.0.0.1:9020/mcp"
    )
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == token
    assert set(environment) == {
        "HOME",
        "PATH",
        "LANG",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN",
    }


def test_qualification_agent_start_failure_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    secret = _append_bridge(paths)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )

    def fail_execve(_path: str, _argv: list[str], _env: dict[str, str]) -> object:
        raise OSError(f"private={secret}")

    with pytest.raises(FabricAgentQualificationError) as exc:
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=fail_execve,
        )

    assert str(exc.value) == "Runner Fabric qualification agent could not start"
    assert secret not in str(exc.value)


_A6_VALUES = {
    "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": "/private/a6-journal",
    "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN": "control:evidence",
    "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN": "target:runner-mcp",
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": "http://127.0.0.1:8000/mcp",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": "r" * 48,
    "RUNNER_FABRIC_SYNTHETIC_PROBE_ID": "fleet-a6",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT": "runner:aifordable-lab",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION": "f" * 40,
    "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS": "60",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT": "/private/a6-evidence",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION": "f" * 40,
}


def _append_a6(paths, values: dict[str, str] | None = None) -> None:
    selected = _A6_VALUES if values is None else values
    with paths.env_file.open("a", encoding="utf-8") as handle:
        for key, value in selected.items():
            handle.write(f"{key}={value}\n")


def test_qualification_agent_forwards_complete_fixed_a6_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_a6(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("UNRELATED_PRIVATE_VALUE=must-not-leak\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0

    environment = captured["env"]
    assert isinstance(environment, dict)
    for key, value in _A6_VALUES.items():
        assert environment[key] == value
    assert "UNRELATED_PRIVATE_VALUE" not in environment


def test_qualification_agent_rejects_partial_a6_binding(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_a6(
        paths,
        {"RUNNER_FABRIC_UPDATE_JOURNAL_ROOT": "/private/a6-journal"},
    )

    with pytest.raises(
        FabricAgentQualificationError,
        match="A6 qualification configuration is incomplete",
    ):
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=lambda *_: object(),
        )


_WORKER_VALUES = {
    "RUNNER_FABRIC_WORKER_QUALIFICATION_WORKER_ID": "aifordable-lab",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_GENERATION": "1",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_NETWORK_PROFILE": "deny-private",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_CPU_UNITS": "8",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_MEMORY_MIB": "16384",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_DISK_MIB": "65536",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_CPU_UNITS": "2",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_MEMORY_MIB": "2048",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_POLICY_EXPIRES_AT": (
        "2026-10-07T00:00:00+00:00"
    ),
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT": "http://127.0.0.1:8000/mcp",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN": "w" * 48,
}


def _append_worker(paths, values: dict[str, str] | None = None) -> None:
    selected = _WORKER_VALUES if values is None else values
    with paths.env_file.open("a", encoding="utf-8") as handle:
        for key, value in selected.items():
            handle.write(f"{key}={value}\n")


def test_qualification_agent_forwards_complete_worker_binding_without_a6(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_worker(paths)
    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0
    environment = captured["env"]
    assert isinstance(environment, dict)
    for key, value in _WORKER_VALUES.items():
        assert environment[key] == value
    assert "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT" not in environment


def test_qualification_agent_rejects_partial_worker_binding(tmp_path: Path) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_worker(
        paths,
        {"RUNNER_FABRIC_WORKER_QUALIFICATION_WORKER_ID": "aifordable-lab"},
    )

    with pytest.raises(
        FabricAgentQualificationError,
        match="worker qualification configuration is incomplete",
    ):
        run_fabric_agent_qualification_process(
            paths.config_dir,
            execve=lambda *_: object(),
        )


def test_shared_runner_mcp_binding_does_not_cross_trigger_a6_or_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write(
            "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT=http://127.0.0.1:8000/mcp\n"
        )
        handle.write("RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN=" + ("s" * 48) + "\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT" not in environment
    assert "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN" not in environment


def test_qualification_agent_forwards_a6_and_worker_bindings_together(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    _append_a6(paths)
    worker_only = {
        key: value
        for key, value in _WORKER_VALUES.items()
        if key
        not in {
            "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT",
            "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN",
        }
    }
    _append_worker(paths, worker_only)

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification,
        "_fixed_runner_fabric_executable",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir,
        execve=fake_execve,
    ) == 0
    environment = captured["env"]
    assert isinstance(environment, dict)
    for key, value in _A6_VALUES.items():
        assert environment[key] == value
    for key, value in worker_only.items():
        assert environment[key] == value


_AF585_ISSUER = "af585-control-issuer.env"
_AF585_VALUES = {
    "RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE": "machine_control_credential",
    "RUNNER_FABRIC_CONTROL_RELAY_ORIGIN": "https://staging.fiscero.com",
    "RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL": "z" * 48,
}


def _write_af585_issuer(paths, values=None):
    issuer = paths.config_dir / _AF585_ISSUER
    source = _AF585_VALUES if values is None else values
    issuer.write_text(
        "".join(f"{key}={value}\n" for key, value in source.items()),
        encoding="utf-8",
    )
    issuer.chmod(0o600)
    return issuer


def test_af585_private_issuer_is_forwarded_to_existing_agent_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _private_config(tmp_path)
    token = _append_bridge(paths)
    _write_af585_issuer(paths)
    with paths.env_file.open("a", encoding="utf-8") as handle:
        handle.write("RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL=untrusted-main-env\n")
        handle.write("UNRELATED_PRIVATE_VALUE=must-not-leak\n")

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification, "_fixed_runner_fabric_executable", lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir, execve=fake_execve,
    ) == 0
    environment = captured["env"]
    assert isinstance(environment, dict)
    for key, value in _AF585_VALUES.items():
        assert environment[key] == value
    assert environment["RUNNER_FABRIC_AGENT_BEARER_TOKEN"] == token
    assert captured["argv"] == [str(executable), "agent-serve-qualification"]
    assert "UNRELATED_PRIVATE_VALUE" not in environment
    assert set(environment) == {
        "HOME", "PATH", "LANG",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL",
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN",
        *_AF585_VALUES,
    }


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE": "operator_mfa_bearer"}, "mode"),
        ({"RUNNER_FABRIC_CONTROL_RELAY_ORIGIN": "https://other.example"}, "origin"),
        ({"RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL": "short"}, "credential"),
        ({"RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL": "x" * 5000}, "length"),
    ],
)
def test_af585_private_issuer_rejects_wrong_role_origin_or_secret(
    tmp_path: Path, changes: dict[str, str], reason: str,
) -> None:
    del reason
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    values = {**_AF585_VALUES, **changes}
    _write_af585_issuer(paths, values)

    with pytest.raises(
        FabricAgentQualificationError,
        match="original issuer configuration is invalid",
    ) as exc:
        qualification.qualification_agent_environment_additions(paths.config_dir)
    assert _AF585_VALUES["RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL"] not in str(exc.value)


def test_af585_private_issuer_rejects_missing_key(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    values = dict(_AF585_VALUES)
    del values["RUNNER_FABRIC_CONTROL_RELAY_ORIGIN"]
    _write_af585_issuer(paths, values)
    with pytest.raises(
        FabricAgentQualificationError,
        match="original issuer configuration is invalid",
    ):
        qualification.qualification_agent_environment_additions(paths.config_dir)


def test_af585_private_issuer_rejects_insecure_mode_and_symlink(
    tmp_path: Path,
) -> None:
    paths = _private_config(tmp_path)
    _append_bridge(paths)
    issuer = _write_af585_issuer(paths)
    issuer.chmod(0o644)
    with pytest.raises(FabricAgentQualificationError):
        qualification.qualification_agent_environment_additions(paths.config_dir)
    issuer.chmod(0o600)
    target = tmp_path / "elsewhere-private"
    target.write_text(issuer.read_text(encoding="utf-8"), encoding="utf-8")
    issuer.unlink()
    issuer.symlink_to(target)
    with pytest.raises(FabricAgentQualificationError):
        qualification.qualification_agent_environment_additions(paths.config_dir)


def _default_original_publisher_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """Synthetic same-owner default Runner-MCP tree, never a real host."""
    home = tmp_path / "owner-home"
    home.mkdir(mode=0o700)
    home_config = home / ".config"
    home_config.mkdir(mode=0o700)
    monkeypatch.setattr(Path, "home", lambda: home)
    project = tmp_path / "project"
    project.mkdir()
    paths = install_private_configuration(
        config_dir=home_config / "runner-mcp",
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    return paths, home_config / "runner-fabric"


def _write_original_custody(issuer_dir: Path, values=None) -> Path:
    issuer_dir.mkdir(mode=0o700)
    file = issuer_dir / _AF585_ISSUER
    source = _AF585_VALUES if values is None else values
    file.write_text(
        "".join(f"{key}={value}\n" for key, value in source.items()),
        encoding="utf-8",
    )
    file.chmod(0o600)
    return file


def test_af585_original_owner_sibling_forwards_without_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    _append_bridge(paths)
    _write_original_custody(issuer_dir)
    assert not (paths.config_dir / _AF585_ISSUER).exists()

    executable = tmp_path / "runner-fabric"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        qualification, "_fixed_runner_fabric_executable", lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured.update(path=path, argv=argv, env=env)
        return object()

    assert run_fabric_agent_qualification_process(
        paths.config_dir, execve=fake_execve,
    ) == 0
    env = captured["env"]
    assert isinstance(env, dict)
    assert all(env[key] == value for key, value in _AF585_VALUES.items())
    assert not (paths.config_dir / _AF585_ISSUER).exists()
    assert captured["argv"] == [str(executable), "agent-serve-qualification"]


def test_af585_two_owner_issuer_files_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    _append_bridge(paths)
    _write_af585_issuer(paths)
    _write_original_custody(issuer_dir)
    with pytest.raises(
        FabricAgentQualificationError,
        match="original issuer configuration is invalid",
    ):
        qualification.qualification_agent_environment_additions(paths.config_dir)


@pytest.mark.parametrize("invalid", ["world-readable-dir", "symlink-dir", "symlink-file", "world-readable-file"])
def test_af585_sibling_rejects_unsafe_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str,
) -> None:
    paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    _append_bridge(paths)
    if invalid == "symlink-dir":
        outside = tmp_path / "elsewhere"
        _write_original_custody(outside)
        issuer_dir.symlink_to(outside, target_is_directory=True)
    else:
        file = _write_original_custody(issuer_dir)
        if invalid == "world-readable-dir":
            issuer_dir.chmod(0o755)
        elif invalid == "symlink-file":
            target = tmp_path / "outside-issuer"
            target.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
            file.unlink()
            file.symlink_to(target)
        else:
            file.chmod(0o644)
    with pytest.raises(
        FabricAgentQualificationError,
        match="original issuer configuration is invalid",
    ):
        qualification.qualification_agent_environment_additions(paths.config_dir)


def test_af585_unrelated_config_must_not_implicitly_adopt_sibling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    _write_original_custody(issuer_dir)
    assert qualification._af585_private_issuer_additions(tmp_path / "other") == {}


def test_af585_sibling_invalid_role_or_origin_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    values = {**_AF585_VALUES, "RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE": "operator_mfa_bearer"}
    _write_original_custody(issuer_dir, values)
    with pytest.raises(
        FabricAgentQualificationError,
        match="original issuer configuration is invalid",
    ):
        qualification.qualification_agent_environment_additions(paths.config_dir)


def test_af585_no_sibling_file_preserves_disabled_mode_with_nonprivate_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, issuer_dir = _default_original_publisher_config(tmp_path, monkeypatch)
    _append_bridge(paths)
    issuer_dir.mkdir(mode=0o755)
    assert qualification._af585_private_issuer_additions(paths.config_dir) == {}
