from __future__ import annotations

import json
from pathlib import Path
from tomllib import load


ROOT = Path(__file__).resolve().parents[2]
SERVER_NAME = "io.github.blacksp1d3r/runner-mcp"


def _server_metadata() -> dict:
    return json.loads((ROOT / "server.json").read_text(encoding="utf-8"))


def _project_metadata() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return load(handle)["project"]


def test_distribution_versions_stay_in_sync() -> None:
    server = _server_metadata()
    project = _project_metadata()

    assert server["version"] == project["version"]
    assert server["packages"][0]["version"] == project["version"]


def test_mcp_registry_identity_matches_pypi_readme_marker() -> None:
    server = _server_metadata()
    project = _project_metadata()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert server["name"] == SERVER_NAME
    assert f"<!-- mcp-name: {SERVER_NAME} -->" in readme
    assert project["name"] == "runner-mcp"
    assert server["packages"][0]["identifier"] == project["name"]
    assert server["repository"]["url"] == "https://github.com/Blacksp1d3r/runner-mcp"
    assert server["repository"]["source"] == "github"
    assert server["repository"]["id"] == "1377580607"


def test_registry_launcher_preserves_safe_local_transport_boundary() -> None:
    package = _server_metadata()["packages"][0]
    transport = package["transport"]

    assert package["registryType"] == "pypi"
    assert package["runtimeHint"] == "uvx"
    assert package["packageArguments"] == [{"type": "positional", "value": "serve"}]
    assert transport["type"] == "streamable-http"
    assert transport["url"] == "http://127.0.0.1:8000/mcp"

    auth = transport["headers"][0]
    assert auth["name"] == "Authorization"
    assert auth["isRequired"] is True
    assert auth["isSecret"] is True
    assert auth["value"] == "Bearer {token}"
    assert auth["variables"]["token"]["isRequired"] is True
    assert auth["variables"]["token"]["isSecret"] is True
