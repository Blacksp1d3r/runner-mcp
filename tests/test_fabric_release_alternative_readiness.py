"""Actions-vs-Releases diagnostic fallback, without updating any runner."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from runner_mcp.fabric_update import (
    FabricUpdateError,
    FabricUpdateManager,
    bounded_fabric_readiness_failure,
    read_alternative_release_metadata_after_actions_failure,
)

COMMIT = "a" * 40
DIGEST = "b" * 64


def _manager(monkeypatch, *, response=None, error=None):
    """Constructor-free, fixed release metadata stub; no host side effects."""
    manager = object.__new__(FabricUpdateManager)
    calls = []

    def probe(commit):
        calls.append(commit)
        if error is not None:
            raise error
        return (
            {
                "state": "ready",
                "source": "github-release",
                "commit": COMMIT,
                "asset_count": 33,
                "project_wheel_sha256": DIGEST,
                "mutation_authorized": False,
                "download_performed": False,
            }
            if response is None else response
        )

    monkeypatch.setattr(manager, "release_assets_readiness", probe)
    return manager, calls


def _inspect(manager, error=None, commit=COMMIT):
    return read_alternative_release_metadata_after_actions_failure(
        manager,
        commit,
        FabricUpdateError("actions_run_unavailable") if error is None else error,
    )


def test_actions_failure_shows_alternate_metadata_without_update_authority(
    monkeypatch,
):
    manager, calls = _manager(monkeypatch)
    alternate = _inspect(manager)
    assert calls == [COMMIT]
    assert alternate == {
        "source": "github-release",
        "state": "metadata_observed_unverified",
        "reasonCode": "exact_release_metadata_observed_not_installed",
        "metadata_observed": True,
        "install_authorized": False,
        "download_performed": False,
    }
    original = bounded_fabric_readiness_failure(
        FabricUpdateError("actions_run_unavailable"), source="github-actions",
    )
    original["alternative_release_metadata"] = alternate
    assert original["state"] == "blocked"
    assert original["source"] == "github-actions"
    assert original["artifact_ready"] is False
    assert "installed" not in original
    assert original["alternative_release_metadata"]["install_authorized"] is False


@pytest.mark.parametrize("error", [
    FabricUpdateError("fabric_launcher_unmanaged"),
    FabricUpdateError("fabric_bundle_integrity_failed"),
    FabricUpdateError("runner_mcp_state_unavailable"),
    RuntimeError("private value"),
])
def test_non_actions_failure_never_queries_alternative(monkeypatch, error):
    manager, calls = _manager(monkeypatch)
    assert _inspect(manager, error) is None
    assert calls == []


@pytest.mark.parametrize("commit", [
    "", "a" * 39, "A" * 40, "z" * 40,
])
def test_invalid_source_pin_cannot_probe_release(monkeypatch, commit):
    manager, calls = _manager(monkeypatch)
    assert _inspect(manager, commit=commit) is None
    assert calls == []


@pytest.mark.parametrize(("error", "expected"), [
    (FabricUpdateError("fabric_release_metadata_unavailable"),
     "fabric_release_metadata_unavailable"),
    (FabricUpdateError("fabric_release_assets_unqualified"),
     "fabric_release_assets_unqualified"),
    (FabricUpdateError("/private/secret?token=hidden"),
     "fabric_update_readiness_unavailable"),
    (RuntimeError("private credential"), "release_metadata_probe_unavailable"),
])
def test_unavailable_release_is_distinct_and_redacted(monkeypatch, error, expected):
    manager, calls = _manager(monkeypatch, error=error)
    result = _inspect(manager)
    assert calls == [COMMIT]
    assert result["state"] == "blocked"
    assert result["reasonCode"] == expected
    assert result["install_authorized"] is False
    assert result["metadata_observed"] is False
    assert "secret" not in repr(result)
    assert "hidden" not in repr(result)
    assert "credential" not in repr(result)


@pytest.mark.parametrize("change", [
    {"state": "unknown"},
    {"source": "github-actions"},
    {"commit": "f" * 40},
    {"asset_count": True},
    {"asset_count": -1},
    {"project_wheel_sha256": None},
    {"project_wheel_sha256": "f" * 63},
    {"mutation_authorized": True},
    {"download_performed": True},
])
def test_stubbed_invalid_release_is_not_observed(monkeypatch, change):
    valid = {
        "state": "ready", "source": "github-release", "commit": COMMIT,
        "asset_count": 33, "project_wheel_sha256": DIGEST,
        "mutation_authorized": False, "download_performed": False,
    }
    valid.update(change)
    manager, _calls = _manager(monkeypatch, response=valid)
    report = _inspect(manager)
    assert report["state"] == "blocked"
    assert report["reasonCode"] == "release_metadata_probe_invalid"
    assert report["install_authorized"] is False


def test_existing_server_tool_keeps_actions_as_only_installable_source():
    """Static integration test: no new start/stage/rollback branch added."""
    source = Path(__file__).resolve().parents[1] / "src/runner_mcp/server.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    handlers = [
        node for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef)
        and node.name == "fabric_update_readiness"
    ]
    assert len(handlers) == 1
    names = {
        node.id for node in ast.walk(handlers[0])
        if isinstance(node, ast.Name)
    }
    assert "read_alternative_release_metadata_after_actions_failure" in names
    forbidden = {
        "start", "start_local", "stage_local_bundle", "rollback",
        "download_artifact", "import_signed_pinned_q7_once",
    }
    attrs = {
        node.attr for node in ast.walk(handlers[0])
        if isinstance(node, ast.Attribute)
    }
    assert not (attrs & forbidden)
