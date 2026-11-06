"""The existing GitHub Release metadata preflight must stay read-only and bounded."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from runner_mcp.fabric_release_assets import ReleaseAdmission

from runner_mcp.fabric_update import (
    FabricUpdateError,
    FabricUpdateManager,
    bounded_fabric_readiness_failure,
)

_COMMIT = "a" * 40
_SHA = "b" * 64
_TAG = "fabric-update-bundle-" + _COMMIT


def _assets():
    names = [
        "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py",
        "runner_fabric-0.0.1-py3-none-any.whl",
    ]
    return [
        {"name": name, "id": index, "size": 42, "digest": "sha256:" + _SHA}
        for index, name in enumerate(names, start=1)
    ]


def _metadata():
    return {
        "id": 12345, "tag_name": _TAG, "target_commitish": _COMMIT,
        "draft": False, "prerelease": True, "assets": _assets(),
    }


def _tag_ref():
    return {
        "ref": "refs/tags/" + _TAG,
        "object": {"type": "commit", "sha": _COMMIT},
    }


def _manager(monkeypatch, release=None, ref=None):
    """Bypass constructor so no private storage or network is touched."""
    manager = object.__new__(FabricUpdateManager)
    calls = []
    monkeypatch.setattr(manager, "_require_safe_runtime", lambda: calls.append("safe"))
    monkeypatch.setattr(manager, "_assert_managed_launcher", lambda: calls.append("launcher"))
    monkeypatch.setattr(manager, "_github_token", lambda: "synthetic-local-token")
    def fake_api(token, path, *, category):
        assert token == "synthetic-local-token"
        assert category == "fabric_release_metadata_unavailable"
        assert path.startswith("/repos/Blacksp1d3r/Runner-Fabric/")
        calls.append(path)
        if "/releases/tags/" in path:
            assert path.endswith(_TAG)
            return release if release is not None else _metadata()
        if "/git/ref/tags/" in path:
            assert path.endswith(_TAG)
            return ref if ref is not None else _tag_ref()
        pytest.fail("unapproved endpoint")
    monkeypatch.setattr(manager, "_api_json", fake_api)
    return manager, calls


def test_existing_release_preflight_is_metadata_only(monkeypatch):
    manager, calls = _manager(monkeypatch)
    result = manager.release_assets_readiness(_COMMIT)
    assert result == {
        "state": "ready",
        "source": "github-release",
        "commit": _COMMIT,
        "asset_count": 5,
        "project_wheel_sha256": _SHA,
        "mutation_authorized": False,
        "download_performed": False,
    }
    assert calls[:2] == ["safe", "launcher"]
    assert len(calls) == 4
    assert "synthetic-local-token" not in repr(result)


@pytest.mark.parametrize("corruption", [
    {"target_commitish": "c" * 40},
    {"draft": True},
    {"prerelease": False},
    {"assets": []},
    {"tag_name": "fabric-update-bundle-" + "c" * 40},
])
def test_existing_release_preflight_denies_unqualified_release(monkeypatch, corruption):
    manager, _calls = _manager(monkeypatch, release={**_metadata(), **corruption})
    with pytest.raises(FabricUpdateError, match="^fabric_release_assets_unqualified$"):
        manager.release_assets_readiness(_COMMIT)
    result = bounded_fabric_readiness_failure(
        FabricUpdateError("fabric_release_assets_unqualified"),
        source="github-release",
    )
    assert result == {
        "state": "blocked", "reasonCode": "fabric_release_assets_unqualified",
        "artifact_ready": False, "source": "github-release",
    }


def test_release_probe_never_falls_back_to_actions_or_stages(monkeypatch):
    manager, _calls = _manager(monkeypatch)
    monkeypatch.setattr(manager, "_resolve_exact_artifact",
                        lambda *args: pytest.fail("Actions lookup forbidden"))
    monkeypatch.setattr(manager, "_validated_bootstrap",
                        lambda *args, **kwargs: pytest.fail("bootstrap forbidden"))
    manager.release_assets_readiness(_COMMIT)

    source = Path(__file__).resolve().parents[1] / "src/runner_mcp/server.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    handlers = [
        node for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef)
        and node.name == "fabric_release_assets_readiness"
    ]
    assert len(handlers) == 1
    handler = handlers[0]
    assert any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
               and dec.func.attr == "tool" for dec in handler.decorator_list)
    attrs = {
        node.attr for node in ast.walk(handler)
        if isinstance(node, ast.Attribute)
    }
    assert "release_assets_readiness" in attrs
    assert not attrs.intersection({
        "start", "start_local", "stage_local_bundle", "rollback",
        "fetch_exact_artifact", "download_artifact",
    })


def test_internal_exact_release_snapshot_uses_same_two_fixed_endpoints(monkeypatch):
    """Hergebruik dezelfde bronparser; behoud de bestaande publieke velden."""
    manager, calls = _manager(monkeypatch)
    snapshot = manager._read_exact_release_admission(_COMMIT)
    assert type(snapshot) is ReleaseAdmission
    assert snapshot.commit == _COMMIT
    assert snapshot.tag == _TAG
    assert snapshot.release_id == 12345
    assert snapshot.project_wheel == "runner_fabric-0.0.1-py3-none-any.whl"
    assert len(snapshot.files) == 5
    assert snapshot.files[0].sha256 == _SHA
    assert snapshot.public_dict()["mutation_authorized"] is False
    assert calls[:2] == ["safe", "launcher"]
    assert calls[2:] == [
        "/repos/Blacksp1d3r/Runner-Fabric/releases/tags/" + _TAG,
        "/repos/Blacksp1d3r/Runner-Fabric/git/ref/tags/" + _TAG,
    ]

    # Een zelfstandige publieke call moet dezelfde snapshot als beperkt
    # JSON-statusantwoord tonen, zonder nieuw requestpad of download.
    public = manager.release_assets_readiness(_COMMIT)
    assert public == snapshot.public_dict()
    assert len(calls) == 8
    assert "install_authorized" not in public
    assert "token" not in repr(public)


@pytest.mark.parametrize("broken", [
    {"target_commitish": "c" * 40},
    {"assets": []},
    {"draft": True},
    {"tag_name": "fabric-update-bundle-" + "b" * 40},
])
def test_internal_typed_release_snapshot_fails_like_existing_public_probe(
    monkeypatch, broken,
):
    manager, calls = _manager(monkeypatch, release={**_metadata(), **broken})
    with pytest.raises(FabricUpdateError, match="^fabric_release_assets_unqualified$"):
        manager._read_exact_release_admission(_COMMIT)
    assert calls[:2] == ["safe", "launcher"]
    assert len(calls) == 4


def test_private_metadata_snapshot_never_fetches_assets_or_changes_storage(monkeypatch):
    manager, calls = _manager(monkeypatch)
    monkeypatch.setattr(
        manager, "_download_artifact",
        lambda *a: pytest.fail("No Actions artifact download"),
    )
    monkeypatch.setattr(
        manager, "_stage_local_bundle",
        lambda *a: pytest.fail("No local bundle staging"),
    )
    monkeypatch.setattr(
        manager, "_activate_bundle",
        lambda *a: pytest.fail("No active bundle replacement"),
    )
    result = manager._read_exact_release_admission(_COMMIT)
    assert result.release_id == 12345
    assert len(calls) == 4
