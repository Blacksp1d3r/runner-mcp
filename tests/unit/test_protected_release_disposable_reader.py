"""#588: exercise the installed Runner-MCP local reader against disposable custody.

SOURCE/CI ONLY. These tests do not read the original host's independent disk and
do not qualify the physical two-release offline restore or any production update.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import pytest

from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
from runner_mcp.protected_release_restore_qualification import (
    ProtectedReleaseRestoreQualification,
)

ACTIVE = "a" * 40
ROLLBACK = "b" * 40
WHEEL = "runner_fabric-0.0.1-py3-none-any.whl"


def _make_manager(root: Path) -> FabricUpdateManager:
    home = root / "disposable-home"
    home.mkdir(mode=0o700)
    config = home / "private-config"
    config.mkdir(mode=0o700)
    safety = OperatorSafetyGuard(home / "operator-stop", RetentionPolicy(), retention_confirmed=True)
    manager = FabricUpdateManager(
        config_dir=config,
        safety=safety,
        home=home,
        self_update_status_provider=lambda: {
            "active_update": False,
            "restart_pending": False,
            "install_recovery_pending": False,
        },
    )
    # This is a disposable, non-serving launcher, never the user's actual launcher.
    executable = manager.state_root / "slots" / "previous" / "venv" / "bin" / "runner-fabric"
    executable.parent.mkdir(parents=True, mode=0o700)
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    manager.launcher.parent.mkdir(parents=True, mode=0o700)
    manager.launcher.symlink_to(executable)
    return manager


def _wheel_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "runner_fabric-0.0.1.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: runner-fabric\nVersion: 0.0.1\n",
        )
        archive.writestr(
            "runner_fabric-0.0.1.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
    return buf.getvalue()


def _make_bundle(manager: FabricUpdateManager, revision: str) -> Path:
    bundle = manager.local_bundles_root / revision
    bundle.mkdir(mode=0o700)
    bootstrap = b"from __future__ import annotations\n"
    wheel = _wheel_bytes()
    files = {
        "BOOTSTRAP.py": bootstrap,
        WHEEL: wheel,
        "COMMIT_SHA": (revision + "\n").encode("ascii"),
        "SHA256SUMS": (
            f"{hashlib.sha256(bootstrap).hexdigest()} BOOTSTRAP.py\n"
            f"{hashlib.sha256(wheel).hexdigest()} {WHEEL}\n"
        ).encode("ascii"),
        "BUNDLE.json": json.dumps(
            {
                "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
                "commitSha": revision,
                "python": "3.12",
                "projectWheel": WHEEL,
                "wheelCount": 1,
                "bootstrapSha256": hashlib.sha256(bootstrap).hexdigest(),
            }
        ).encode("utf-8"),
    }
    for name, data in files.items():
        dest = bundle / name
        dest.write_bytes(data)
        os.chmod(dest, 0o600)
    return bundle


def _mirror_readiness() -> dict[str, object]:
    return {
        "schemaVersion": "runner-mcp/fabric-release-archive-mirror-readiness/v1",
        "configurationState": "configured",
        "ready": True,
        "primaryCustodyReady": True,
        "mountReady": True,
        "mirrorRootReady": True,
        "distinctDeviceReady": True,
        "mutationEnabled": False,
        "reasonCode": "ready",
    }


def test_real_local_reader_accepts_two_exact_disposable_bundles_without_live_access(tmp_path: Path):
    # A sentinel representing production is strictly outside the disposable HOME.
    production = tmp_path / "production"
    production.mkdir(mode=0o700)
    sentinel = production / "transaction.json"
    original = b"production-transaction-must-remain-bit-identical"
    sentinel.write_bytes(original)
    manager = _make_manager(tmp_path)
    for revision in (ACTIVE, ROLLBACK):
        _make_bundle(manager, revision)
        assert manager.local_readiness(revision) == {
            "commit": revision, "artifact_ready": True, "source": "local-custody"
        }
    assert sentinel.read_bytes() == original
    assert tuple(production.iterdir()) == (sentinel,)
    assert manager.home != production
    assert manager.transaction != sentinel


@pytest.mark.parametrize("tamper", ["wheel", "bootstrap", "commit", "symlink"])
def test_real_local_reader_rejects_modified_disposable_bundle(tmp_path: Path, tamper: str):
    manager = _make_manager(tmp_path)
    bundle = _make_bundle(manager, ACTIVE)
    if tamper == "wheel":
        (bundle / WHEEL).write_bytes((bundle / WHEEL).read_bytes() + b"corruption")
    elif tamper == "bootstrap":
        (bundle / "BOOTSTRAP.py").write_bytes(b"corruption")
    elif tamper == "commit":
        (bundle / "COMMIT_SHA").write_text(ROLLBACK, encoding="ascii")
    else:
        external = tmp_path / "external-wheel"
        external.write_bytes((bundle / WHEEL).read_bytes())
        (bundle / WHEEL).unlink()
        (bundle / WHEEL).symlink_to(external)
    with pytest.raises(FabricUpdateError):
        manager.local_readiness(ACTIVE)


def test_actual_reader_success_is_not_a_full_disposable_restore_receipt(tmp_path: Path):
    manager = _make_manager(tmp_path)
    for revision in (ACTIVE, ROLLBACK):
        _make_bundle(manager, revision)

    calls: list[str] = []

    def only_reader(revision: str) -> dict[str, object]:
        calls.append(revision)
        assert manager.local_readiness(revision)["artifact_ready"] is True
        # No bootstrap preflight/apply/rollback, network isolation, or cleanup was
        # proved here: never mint those receipt flags from parser acceptance.
        return {
            "schemaVersion": "runner-mcp/offline-disposable-release-restore/v1",
            "commitSha": revision,
            "revisionVerified": False,
            "localCustodyReaderAccepted": True,
            "offlineNetworkDisabled": False,
            "bootstrapPreflightPassed": False,
            "bootstrapApplyPassed": False,
            "bootstrapRollbackPassed": False,
            "disposableCleanupVerified": False,
            "liveMutationTriggered": False,
        }

    gate = ProtectedReleaseRestoreQualification(
        protected_pins=lambda: (ACTIVE, ROLLBACK),
        mirror_admission=_mirror_readiness,
        mirror_verified=lambda _: True,
        disposable_qualify=only_reader,
        live_transaction_state=lambda: "unchanged-test-transaction",
    )
    result = gate.run()
    assert result["state"] == "blocked"
    assert result["reasonCode"] == "disposable-proof-incomplete"
    assert calls == [ACTIVE]
