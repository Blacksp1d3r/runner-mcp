"""No GitHub Release asset metadata can authorize Fabric deployment."""

from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.fabric_update import (
    FabricUpdateError,
    FabricUpdateManager,
    bounded_fabric_readiness_failure,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy

COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"


def _manager(tmp_path: Path, *, runtime_safe: bool = True) -> FabricUpdateManager:
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    manager = FabricUpdateManager(
        config_dir=config,
        safety=guard,
        self_update_status_provider=lambda: {
            "active_update": not runtime_safe,
            "restart_pending": False,
            "install_recovery_pending": False,
        },
        home=home,
    )
    root = manager.state_root / "slots" / ("a" * 40) / "venv" / "bin"
    root.mkdir(parents=True, mode=0o700)
    binary = root / "runner-fabric"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o700)
    manager.launcher.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    manager.launcher.symlink_to(binary)
    return manager


def _metadata() -> tuple[dict, dict]:
    tag = "fabric-q7-bundle-" + COMMIT
    names = (
        "BUNDLE.json", "BOOTSTRAP.py", "COMMIT_SHA", "SHA256SUMS",
        "runner_fabric-0.0.1-py3-none-any.whl",
    )
    release = {
        "id": 123,
        "tag_name": tag,
        "target_commitish": COMMIT,
        "draft": False,
        "prerelease": True,
        "assets": [
            {"id": i + 1, "name": n, "size": 100, "digest": "sha256:" + "a" * 64}
            for i, n in enumerate(names)
        ],
    }
    ref = {"ref": "refs/tags/" + tag, "object": {"type": "commit", "sha": COMMIT}}
    return release, ref


def test_live_release_preflight_proves_only_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _manager(tmp_path)
    r, tag = _metadata()
    calls: list[str] = []
    monkeypatch.setattr(manager, "_github_token", lambda: "synthetic")
    def api(_token, path, *, category):
        calls.append(path)
        assert category == "fabric_release_metadata_unavailable"
        return tag if "/git/ref/tags/" in path else r
    monkeypatch.setattr(manager, "_api_json", api)
    monkeypatch.setattr(
        manager, "_download_artifact",
        lambda *_args: pytest.fail("never download or mutate during preflight"),
    )
    result = manager.release_assets_readiness(COMMIT)
    assert result["state"] == "ready"
    assert result["source"] == "github-release"
    assert result["asset_count"] == 5
    assert result["mutation_authorized"] is False
    assert result["download_performed"] is False
    assert calls == [
        "/repos/Blacksp1d3r/Runner-Fabric/releases/tags/fabric-q7-bundle-" + COMMIT,
        "/repos/Blacksp1d3r/Runner-Fabric/git/ref/tags/fabric-q7-bundle-" + COMMIT,
    ]
    assert not any(manager.local_bundles_root.iterdir())


def test_mismatched_release_metadata_is_a_bounded_denial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _manager(tmp_path)
    release, ref = _metadata()
    release["assets"][0]["digest"] = "sha256:not-a-real-digest"
    monkeypatch.setattr(manager, "_github_token", lambda: "synthetic")
    monkeypatch.setattr(
        manager, "_api_json",
        lambda _token, path, *, category: (
            ref if "/git/ref/tags/" in path else release
        ),
    )
    with pytest.raises(
        FabricUpdateError, match="^fabric_release_assets_unqualified$"
    ):
        manager.release_assets_readiness(COMMIT)
    assert bounded_fabric_readiness_failure(
        FabricUpdateError("fabric_release_assets_unqualified"),
        source="github-release",
    ) == {
        "state": "blocked",
        "reasonCode": "fabric_release_assets_unqualified",
        "artifact_ready": False,
        "source": "github-release",
    }


def test_metadata_readiness_blocked_during_local_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _manager(tmp_path, runtime_safe=False)
    monkeypatch.setattr(
        manager, "_github_token",
        lambda: pytest.fail("token must not be read while update active"),
    )
    with pytest.raises(FabricUpdateError, match="runner_mcp_self_update_active"):
        manager.release_assets_readiness(COMMIT)
