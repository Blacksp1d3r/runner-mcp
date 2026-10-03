from __future__ import annotations

import os
from pathlib import Path

import pytest

from runner_mcp.plugin_package import (
    PluginPackageError,
    render_http_plugin,
)


def test_generated_package_permissions_are_private(tmp_path: Path) -> None:
    root = render_http_plugin(
        tmp_path / "plugin",
        endpoint="https://control.example.invalid/mcp",
        bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
        version="0.1.3",
    )

    assert root.stat().st_mode & 0o777 == 0o700
    for path in root.rglob("*"):
        if path.is_dir():
            assert path.stat().st_mode & 0o777 == 0o700
        elif path.is_file():
            assert path.stat().st_mode & 0o777 == 0o600


def test_existing_symlink_output_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    output = tmp_path / "plugin"
    output.symlink_to(target, target_is_directory=True)

    with pytest.raises(PluginPackageError, match="unsafe"):
        render_http_plugin(
            output,
            endpoint="https://control.example.invalid/mcp",
            bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
            version="0.1.3",
        )

    assert list(target.iterdir()) == []


def test_environment_secret_value_is_never_read_into_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "never-write-this-secret-value"
    monkeypatch.setenv("RUNNER_MCP_PLUGIN_TOKEN", secret)

    root = render_http_plugin(
        tmp_path / "plugin",
        endpoint="https://control.example.invalid/mcp",
        bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
        version="0.1.3",
    )

    combined = b"\n".join(
        path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )
    assert secret.encode() not in combined
    assert b"RUNNER_MCP_PLUGIN_TOKEN" in combined


def test_credential_bearing_endpoint_is_rejected_without_output(tmp_path: Path) -> None:
    root = tmp_path / "plugin"

    with pytest.raises(PluginPackageError, match="endpoint"):
        render_http_plugin(
            root,
            endpoint="https://operator:secret@control.example.invalid/mcp",
            bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
            version="0.1.3",
        )

    assert not root.exists()


def test_output_does_not_inherit_permissive_umask(tmp_path: Path) -> None:
    previous = os.umask(0)
    try:
        root = render_http_plugin(
            tmp_path / "plugin",
            endpoint="https://control.example.invalid/mcp",
            bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
            version="0.1.3",
        )
    finally:
        os.umask(previous)

    assert root.stat().st_mode & 0o777 == 0o700
    assert all(
        path.stat().st_mode & 0o777 == 0o700
        for path in root.rglob("*")
        if path.is_dir()
    )
    assert all(
        path.stat().st_mode & 0o777 == 0o600
        for path in root.rglob("*")
        if path.is_file()
    )
