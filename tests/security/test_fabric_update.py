from __future__ import annotations

import io
import json
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def _manager(tmp_path: Path, *, status: dict | None = None):
    config = tmp_path / "config"
    config.mkdir(mode=0o700)
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    guard = OperatorSafetyGuard(
        stop_file=tmp_path / "stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )
    calls: list[tuple[str, ...]] = []

    def runner(argv, **kwargs):
        calls.append(tuple(str(item) for item in argv))
        return subprocess.CompletedProcess(argv, 0, "", "")

    manager = FabricUpdateManager(
        config_dir=config,
        safety=guard,
        self_update_status_provider=lambda: status
        or {
            "active_update": False,
            "restart_pending": False,
            "install_recovery_pending": False,
        },
        runner=runner,
        home=home,
    )
    return manager, calls


def _managed_launcher(manager: FabricUpdateManager) -> None:
    slot = manager.state_root / "slots" / ("a" * 40) / "venv" / "bin"
    slot.mkdir(parents=True, mode=0o700)
    target = slot / "runner-fabric"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o700)
    manager.launcher.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    manager.launcher.symlink_to(target)


def _bundle(commit: str) -> bytes:
    manifest = {
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": commit,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("BUNDLE.json", json.dumps(manifest))
        archive.writestr("COMMIT_SHA", commit + "\n")
        archive.writestr("SHA256SUMS", "placeholder\n")
        archive.writestr("BOOTSTRAP.py", "raise SystemExit(0)\n")
    return buffer.getvalue()


def test_invalid_commit_is_rejected(tmp_path: Path) -> None:
    manager, _calls = _manager(tmp_path)

    with pytest.raises(FabricUpdateError, match="fabric_update_commit_invalid"):
        manager.start("ABC")


def test_self_update_restart_gate_blocks_fabric_update(tmp_path: Path) -> None:
    manager, _calls = _manager(
        tmp_path,
        status={
            "active_update": False,
            "restart_pending": True,
            "install_recovery_pending": False,
        },
    )
    _managed_launcher(manager)

    with pytest.raises(FabricUpdateError, match="runner_mcp_restart_pending"):
        manager.start("b" * 40)


def test_unmanaged_launcher_is_rejected(tmp_path: Path) -> None:
    manager, _calls = _manager(tmp_path)
    manager.launcher.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    manager.launcher.write_text("#!/bin/sh\n", encoding="utf-8")

    with pytest.raises(FabricUpdateError, match="fabric_launcher_unmanaged"):
        manager.start("b" * 40)


def test_exact_bundle_uses_only_fixed_preflight_and_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, calls = _manager(tmp_path)
    _managed_launcher(manager)
    commit = "b" * 40
    monkeypatch.setattr(manager, "_fetch_exact_artifact", lambda value: _bundle(value))

    started = manager.start(commit)
    job_id = started["job_id"]

    for _ in range(200):
        result = manager.status(job_id)
        if result["state"] in {"completed", "error"}:
            break
        import time

        time.sleep(0.01)
    else:
        raise AssertionError("fabric update did not finish")

    assert result["state"] == "completed"
    assert [call[-1] for call in calls] == ["preflight", "apply"]
    assert all(call[1].endswith("BOOTSTRAP.py") for call in calls)
    assert all(len(call) == 3 for call in calls)


def test_rollback_is_bound_to_current_active_commit(tmp_path: Path) -> None:
    manager, calls = _manager(tmp_path)
    _managed_launcher(manager)
    commit = "c" * 40
    manager.bundle.mkdir(mode=0o700)
    (manager.bundle / "BUNDLE.json").write_text(
        json.dumps(
            {
                "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
                "commitSha": commit,
            }
        ),
        encoding="utf-8",
    )
    (manager.bundle / "COMMIT_SHA").write_text(commit + "\n", encoding="ascii")
    (manager.bundle / "BOOTSTRAP.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    manager.transaction.write_text(
        json.dumps(
            {
                "schemaVersion": "runner.fabric/control-plane-update-transaction/v1",
                "phase": "active",
                "commitSha": commit,
                "previousTarget": "old",
                "newTarget": "new",
            }
        ),
        encoding="utf-8",
    )
    os.chmod(manager.transaction, 0o600)

    with pytest.raises(FabricUpdateError, match="fabric_update_target_mismatch"):
        manager.rollback("d" * 40)

    result = manager.rollback(commit)

    assert result == {"state": "completed", "commit": commit}
    assert calls[-1][-1] == "rollback"
