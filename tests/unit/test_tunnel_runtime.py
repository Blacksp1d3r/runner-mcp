from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.onboarding import SetupAnswers, install_private_configuration
from runner_mcp.tunnel_runtime import TunnelRuntimeError, run_managed_tunnel


def _config(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    paths = install_private_configuration(
        config_dir=tmp_path / "private",
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    return paths.config_dir


def _complete_tunnel_config(config_dir: Path) -> tuple[str, str]:
    tunnel_id = "tunnel_sensitive_placeholder"
    api_key = "api_sensitive_placeholder"
    path = config_dir / "tunnel.env"
    path.write_text(
        f"CONTROL_PLANE_TUNNEL_ID={tunnel_id}\n"
        f"CONTROL_PLANE_API_KEY={api_key}\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    return tunnel_id, api_key


def test_managed_tunnel_requires_complete_private_config(tmp_path: Path) -> None:
    config_dir = _config(tmp_path)

    with pytest.raises(TunnelRuntimeError, match="incomplete or unsafe"):
        run_managed_tunnel(config_dir, exec_fn=lambda *_args: object())


def test_managed_tunnel_execs_only_fixed_loopback_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = _config(tmp_path)
    tunnel_id, api_key = _complete_tunnel_config(config_dir)
    executable = tmp_path / "tunnel-client"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.setattr(
        "runner_mcp.tunnel_runtime._resolve_tunnel_client",
        lambda: executable,
    )
    captured: dict[str, object] = {}

    def fake_exec(path: str, argv: list[str], env: dict[str, str]) -> object:
        captured["path"] = path
        captured["argv"] = argv
        captured["env"] = env
        return object()

    assert run_managed_tunnel(config_dir, port=8123, exec_fn=fake_exec) == 0

    assert captured["path"] == str(executable)
    assert captured["argv"] == [
        str(executable),
        "run",
        "--mcp-server-url",
        "http://127.0.0.1:8123/mcp",
        "--health-listen-addr",
        "127.0.0.1:0",
        "--health-url-file",
        str(config_dir / "tunnel-health.url"),
    ]
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["CONTROL_PLANE_TUNNEL_ID"] == tunnel_id
    assert env["CONTROL_PLANE_API_KEY"] == api_key
    assert not (config_dir / "tunnel-health.url").exists()


def test_managed_tunnel_rejects_symlink_health_evidence_path(
    tmp_path: Path,
) -> None:
    config_dir = _config(tmp_path)
    _complete_tunnel_config(config_dir)
    referent = tmp_path / "foreign"
    referent.write_text("keep\n", encoding="utf-8")
    (config_dir / "tunnel-health.url").symlink_to(referent)

    with pytest.raises(TunnelRuntimeError, match="health evidence path is unsafe"):
        run_managed_tunnel(config_dir, exec_fn=lambda *_args: object())

    assert referent.read_text(encoding="utf-8") == "keep\n"


def test_managed_tunnel_rejects_invalid_port_before_process_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = _config(tmp_path)
    _complete_tunnel_config(config_dir)
    called: list[bool] = []
    monkeypatch.setattr(
        "runner_mcp.tunnel_runtime._resolve_tunnel_client",
        lambda: called.append(True),
    )

    with pytest.raises(TunnelRuntimeError, match="port"):
        run_managed_tunnel(config_dir, port=0)

    assert called == []
