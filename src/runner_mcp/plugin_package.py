from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
_MARKER = ".runner-mcp-plugin-package"
_MARKER_CONTENT = "runner-mcp-first-party-plugin-v1\n"
_APP_ID_RE = re.compile(
    r"^(?:plugin_)?(?P<canonical>(?:asdk_app|connector|templated_apps)_"
    r"[A-Za-z0-9][A-Za-z0-9_-]{0,127})$"
)
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class PluginPackageError(RuntimeError):
    """Fail-closed local plugin packaging error."""


def render_registered_app_plugin(
    output_dir: Path,
    *,
    registered_app_id: str,
    version: str,
    overwrite: bool = False,
) -> Path:
    """Render a local ChatGPT/Codex package for an already-registered MCP app."""

    app_id = _canonical_registered_app_id(registered_app_id)
    root = _prepare_output(output_dir, overwrite=overwrite)
    try:
        _write_common(root, version=version)
        _write_json(
            root / ".app.json",
            {
                "apps": {
                    "runner-mcp": {
                        "id": app_id,
                        "required": True,
                    }
                }
            },
        )
        _write_json(
            root / ".codex-plugin" / "plugin.json",
            _compatibility_manifest(version=version, apps="./.app.json"),
        )
        _write_readme(root, mode="registered-app")
        _write_text(root / _MARKER, _MARKER_CONTENT)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def render_http_plugin(
    output_dir: Path,
    *,
    endpoint: str,
    bearer_env_var: str,
    version: str,
    overwrite: bool = False,
) -> Path:
    """Render a local Codex/self-hosted package for Runner MCP over HTTP."""

    endpoint = _validate_endpoint(endpoint)
    bearer_env_var = _validate_env_name(bearer_env_var)
    root = _prepare_output(output_dir, overwrite=overwrite)
    try:
        _write_common(root, version=version)
        _write_json(
            root / ".mcp.json",
            {
                "mcpServers": {
                    "runner_mcp": {
                        "type": "http",
                        "url": endpoint,
                        "bearer_token_env_var": bearer_env_var,
                    }
                }
            },
        )
        _write_json(
            root / ".codex-plugin" / "plugin.json",
            _compatibility_manifest(version=version, mcp_servers="./.mcp.json"),
        )
        _write_readme(root, mode="http")
        _write_text(root / _MARKER, _MARKER_CONTENT)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def _canonical_registered_app_id(value: object) -> str:
    if not isinstance(value, str):
        raise PluginPackageError("registered MCP app identifier is invalid")
    match = _APP_ID_RE.fullmatch(value.strip())
    if match is None:
        raise PluginPackageError("registered MCP app identifier is invalid")
    return match.group("canonical")


def _validate_env_name(value: object) -> str:
    if not isinstance(value, str) or _ENV_NAME_RE.fullmatch(value) is None:
        raise PluginPackageError("bearer token environment variable name is invalid")
    return value


def _validate_endpoint(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise PluginPackageError("Runner MCP plugin endpoint is invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise PluginPackageError("Runner MCP plugin endpoint is invalid") from exc

    host = (parsed.hostname or "").lower()
    if (
        not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != "/mcp"
    ):
        raise PluginPackageError("Runner MCP plugin endpoint is invalid")
    if parsed.scheme == "https":
        pass
    elif parsed.scheme == "http" and host in _LOOPBACK_HOSTS:
        pass
    else:
        raise PluginPackageError(
            "Runner MCP plugin endpoint must use HTTPS or loopback HTTP"
        )
    if port is not None and not 1 <= port <= 65535:
        raise PluginPackageError("Runner MCP plugin endpoint is invalid")
    return value


def _prepare_output(output_dir: Path, *, overwrite: bool) -> Path:
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a Path")
    root = output_dir.expanduser().resolve(strict=False)
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise PluginPackageError("plugin output path is unsafe")
        entries = list(root.iterdir())
        if entries:
            if not overwrite:
                raise PluginPackageError("plugin output directory is not empty")
            marker = root / _MARKER
            if (
                marker.is_symlink()
                or not marker.is_file()
                or marker.read_text(encoding="utf-8") != _MARKER_CONTENT
            ):
                raise PluginPackageError(
                    "refusing to overwrite a directory not owned by Runner MCP"
                )
            shutil.rmtree(root)
    root.mkdir(parents=True, mode=0o700)
    try:
        root.chmod(0o700)
    except OSError as exc:
        shutil.rmtree(root, ignore_errors=True)
        raise PluginPackageError("could not secure plugin output directory") from exc
    return root


def _write_common(root: Path, *, version: str) -> None:
    if not isinstance(version, str) or not version.strip() or len(version) > 64:
        raise PluginPackageError("plugin version is invalid")
    _write_json(
        root / "plugin.json",
        {
            "$schema": _PLUGIN_SCHEMA,
            "name": "runner-mcp-control",
            "version": version,
            "description": (
                "Use Runner MCP and Runner Fabric for bounded, auditable "
                "development operations."
            ),
            "author": {
                "name": "Blacksp1d3r",
                "url": "https://github.com/Blacksp1d3r/runner-mcp",
            },
            "homepage": "https://github.com/Blacksp1d3r/runner-mcp",
            "repository": "https://github.com/Blacksp1d3r/runner-mcp",
            "license": "MIT",
            "keywords": ["runner-mcp", "runner-fabric", "mcp", "devops", "security"],
        },
    )
    _write_text(
        root / "skills" / "runner-mcp-control" / "SKILL.md",
        _skill_text(),
    )


def _compatibility_manifest(
    *,
    version: str,
    apps: str | None = None,
    mcp_servers: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "name": "runner-mcp-control",
        "version": version,
        "description": (
            "Use Runner MCP and Runner Fabric as the primary bounded control path."
        ),
        "skills": "./skills/",
    }
    if apps is not None:
        result["apps"] = apps
    if mcp_servers is not None:
        result["mcpServers"] = mcp_servers
    return result


def _skill_text() -> str:
    return """---
name: runner-mcp-control
description: Use Runner MCP and Runner Fabric for bounded repository and runner operations.
---

Use Runner MCP and Runner Fabric as the normal control path.

For repository-changing work:
1. Prefer `fabric_run_work_unit` with one bounded semantic work unit and an exact expected revision.
2. Use `fabric_get_work_unit` only when status is needed; do not tight-poll.
3. Use `fabric_cancel_work_unit` only for an explicit cancellation or safety need.
4. Treat Runner Fabric policy, fencing, validation, approval, audit, and emergency-stop results as authoritative.
5. Never replace a blocked Fabric action with generic shell, arbitrary Git/GitHub primitives, direct database edits, or broad host-control tooling.
6. Use broad remote-control tools only as break-glass when the bounded first-party path cannot perform a required recovery check.
7. Do not expose credentials, private endpoints, host paths, raw logs, or private infrastructure metadata.

If the three Fabric tools are absent, report that the private Fabric bridge is not configured instead of inventing another execution path.
"""


def _write_readme(root: Path, *, mode: str) -> None:
    _write_text(
        root / "README.txt",
        (
            "Runner MCP first-party plugin package\n\n"
            f"Connection mode: {mode}\n"
            "This package contains no bearer-token value.\n"
            "Keep this generated directory private because connection metadata may be local.\n"
            "Use Runner MCP / Runner Fabric for normal operations; broad remote tooling is break-glass.\n"
        ),
    )


def _write_json(path: Path, value: object) -> None:
    _write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
