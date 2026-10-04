from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import urllib.error
import zipfile
from pathlib import Path

import pytest

import runner_mcp.fabric_update as fabric_update_module
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


def _bundle(commit: str, *, tamper_bootstrap: bool = False) -> bytes:
    bootstrap = b"raise SystemExit(0)\n"
    wheel_name = "runner_fabric-0.0.1-py3-none-any.whl"
    wheel = b"synthetic-wheel"
    sums = {
        "BOOTSTRAP.py": hashlib.sha256(bootstrap).hexdigest(),
        wheel_name: hashlib.sha256(wheel).hexdigest(),
    }
    manifest = {
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": commit,
        "python": "3.12",
        "projectWheel": wheel_name,
        "wheelCount": 1,
        "bootstrapSha256": sums["BOOTSTRAP.py"],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("BUNDLE.json", json.dumps(manifest))
        archive.writestr("COMMIT_SHA", commit + "\n")
        archive.writestr(
            "SHA256SUMS",
            "".join(
                f"{digest}  {name}\n"
                for name, digest in sorted(sums.items())
            ),
        )
        archive.writestr(
            "BOOTSTRAP.py",
            b"tampered\n" if tamper_bootstrap else bootstrap,
        )
        archive.writestr(wheel_name, wheel)
    return buffer.getvalue()


def test_artifact_run_must_come_from_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _calls = _manager(tmp_path)
    commit = "f" * 40
    monkeypatch.setattr(
        fabric_update_module,
        "_private_env_value",
        lambda _path, _key: "x" * 40,
    )
    monkeypatch.setattr(
        manager,
        "_api_json",
        lambda _token, _path: {
            "workflow_runs": [
                {
                    "id": 123,
                    "head_sha": commit,
                    "head_branch": "feature",
                    "event": "workflow_dispatch",
                    "conclusion": "success",
                }
            ]
        },
    )

    with pytest.raises(FabricUpdateError, match="fabric_artifact_unavailable"):
        manager._fetch_exact_artifact(commit)


def test_artifact_redirect_rejects_private_host(tmp_path: Path) -> None:
    class RedirectingOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "Found",
                {"Location": "https://127.0.0.1/private"},
                None,
            )

    manager, _calls = _manager(tmp_path)
    manager._opener = RedirectingOpener()

    with pytest.raises(FabricUpdateError, match="fabric_artifact_unavailable"):
        manager._request_redirect(
            "https://api.github.com/repos/Blacksp1d3r/Runner-Fabric/actions/artifacts/1/zip",
            "x" * 40,
        )


def test_artifact_download_strips_bearer_after_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _calls = _manager(tmp_path)
    observed: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        manager,
        "_request_redirect",
        lambda _url, _token: "https://artifact.example.invalid/file.zip",
    )

    def fake_request(url: str, *, token: str | None, max_bytes: int) -> bytes:
        observed.append((url, token))
        assert max_bytes > 0
        return b"zip"

    monkeypatch.setattr(manager, "_request", fake_request)

    assert manager._download_artifact("secret-token", 123) == b"zip"
    assert observed == [
        ("https://artifact.example.invalid/file.zip", None)
    ]


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


def test_bundle_hash_mismatch_blocks_before_bootstrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, calls = _manager(tmp_path)
    _managed_launcher(manager)
    commit = "e" * 40
    monkeypatch.setattr(
        manager,
        "_fetch_exact_artifact",
        lambda value: _bundle(value, tamper_bootstrap=True),
    )

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

    assert result["state"] == "error"
    assert result["error_category"] == "fabric_bundle_integrity_failed"
    assert calls == []


def test_rollback_is_bound_to_current_active_commit(tmp_path: Path) -> None:
    manager, calls = _manager(tmp_path)
    _managed_launcher(manager)
    commit = "c" * 40
    manager.bundle.mkdir(mode=0o700)
    with zipfile.ZipFile(io.BytesIO(_bundle(commit))) as archive:
        archive.extractall(manager.bundle)
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
