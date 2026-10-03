from __future__ import annotations

import json
from pathlib import Path

import pytest

from runner_mcp.plugin_package import (
    PluginPackageError,
    render_http_plugin,
    render_registered_app_plugin,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def package_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_registered_app_package_is_bounded_and_normalizes_browser_id(
    tmp_path: Path,
) -> None:
    root = render_registered_app_plugin(
        tmp_path / "plugin",
        registered_app_id="plugin_asdk_app_abc123",
        version="0.1.3",
    )

    manifest = read_json(root / "plugin.json")
    compatibility = read_json(root / ".codex-plugin" / "plugin.json")
    app_manifest = read_json(root / ".app.json")

    assert manifest["name"] == "runner-mcp-control"
    assert manifest["version"] == "0.1.3"
    assert compatibility["apps"] == "./.app.json"
    assert compatibility["skills"] == "./skills/"
    assert app_manifest == {
        "apps": {
            "runner-mcp": {
                "id": "asdk_app_abc123",
                "required": True,
            }
        }
    }
    assert not (root / ".mcp.json").exists()
    assert "fabric_run_work_unit" in (
        root / "skills" / "runner-mcp-control" / "SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "registered_app_id",
    [
        "",
        "plugin_asdk_app_",
        "plugin_other_abc",
        "asdk_app_bad space",
        "https://example.invalid/app",
    ],
)
def test_registered_app_identifier_fails_closed(
    tmp_path: Path,
    registered_app_id: str,
) -> None:
    with pytest.raises(PluginPackageError, match="identifier"):
        render_registered_app_plugin(
            tmp_path / "plugin",
            registered_app_id=registered_app_id,
            version="0.1.3",
        )

    assert not (tmp_path / "plugin").exists()


def test_http_package_uses_environment_reference_not_secret(tmp_path: Path) -> None:
    root = render_http_plugin(
        tmp_path / "plugin",
        endpoint="https://control.example.invalid/mcp",
        bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
        version="0.1.3",
    )

    compatibility = read_json(root / ".codex-plugin" / "plugin.json")
    mcp = read_json(root / ".mcp.json")

    assert compatibility["mcpServers"] == "./.mcp.json"
    assert compatibility["skills"] == "./skills/"
    assert mcp == {
        "mcpServers": {
            "runner_mcp": {
                "type": "http",
                "url": "https://control.example.invalid/mcp",
                "bearer_token_env_var": "RUNNER_MCP_PLUGIN_TOKEN",
            }
        }
    }
    assert not (root / ".app.json").exists()


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://control.example.invalid/mcp",
        "https://user:pass@control.example.invalid/mcp",
        "https://control.example.invalid/",
        "https://control.example.invalid/mcp?token=nope",
        "ftp://control.example.invalid/mcp",
    ],
)
def test_http_endpoint_fails_closed(tmp_path: Path, endpoint: str) -> None:
    with pytest.raises(PluginPackageError, match="endpoint"):
        render_http_plugin(
            tmp_path / "plugin",
            endpoint=endpoint,
            bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
            version="0.1.3",
        )


def test_loopback_http_endpoint_is_allowed_for_self_hosted_use(tmp_path: Path) -> None:
    root = render_http_plugin(
        tmp_path / "plugin",
        endpoint="http://127.0.0.1:8000/mcp",
        bearer_env_var="RUNNER_MCP_PLUGIN_TOKEN",
        version="0.1.3",
    )

    assert read_json(root / ".mcp.json")["mcpServers"]["runner_mcp"]["url"] == (
        "http://127.0.0.1:8000/mcp"
    )


@pytest.mark.parametrize(
    "name",
    ["", "token", "1TOKEN", "RUNNER-MCP-TOKEN", "RUNNER MCP TOKEN"],
)
def test_bearer_environment_name_fails_closed(tmp_path: Path, name: str) -> None:
    with pytest.raises(PluginPackageError, match="environment variable"):
        render_http_plugin(
            tmp_path / "plugin",
            endpoint="https://control.example.invalid/mcp",
            bearer_env_var=name,
            version="0.1.3",
        )


def test_refuses_foreign_nonempty_output_even_with_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "plugin"
    root.mkdir()
    (root / "important.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(PluginPackageError, match="not owned"):
        render_registered_app_plugin(
            root,
            registered_app_id="asdk_app_abc123",
            version="0.1.3",
            overwrite=True,
        )

    assert (root / "important.txt").read_text(encoding="utf-8") == "keep"


def test_owned_package_can_be_deterministically_replaced(tmp_path: Path) -> None:
    root = tmp_path / "plugin"
    render_registered_app_plugin(
        root,
        registered_app_id="asdk_app_abc123",
        version="0.1.3",
    )
    first = package_files(root)

    render_registered_app_plugin(
        root,
        registered_app_id="asdk_app_abc123",
        version="0.1.3",
        overwrite=True,
    )

    assert package_files(root) == first
