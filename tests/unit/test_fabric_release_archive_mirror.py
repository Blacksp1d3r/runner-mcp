"""#587 fixed protected-release BACKUP tests. No host filesystem/network."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner_mcp import fabric_release_archive_mirror as module
from runner_mcp.fabric_release_archive_mirror import (
    ProtectedReleaseArchiveMirror,
    ProtectedReleaseMirrorError,
)
from runner_mcp.operational_safety import (
    OperatorSafetyGuard,
    OperatorStopActive,
    RetentionPolicy,
)

ACTIVE = "a" * 40
PRIOR = "b" * 40
KEYS = (
    "RUNNER_MCP_FABRIC_RELEASE_CUSTODY_ROOT",
    "RUNNER_MCP_FABRIC_RELEASE_MIRROR_MOUNT_ROOT",
    "RUNNER_MCP_FABRIC_RELEASE_MIRROR_ROOT",
)


class Ready:
    def __init__(self, ready=True):
        self.ready = ready

    def status(self):
        return {"ready": self.ready}


def _setup(tmp_path, monkeypatch, *, ready=True, already=False, blocked=None):
    home = tmp_path / "owner-home"
    home.mkdir(mode=0o700)
    state = home / ".local/state/runner-fabric/control-plane-update"
    state.mkdir(parents=True, mode=0o700)
    txn = state / "transaction.json"
    transaction = {
        "schemaVersion": "runner.fabric/control-plane-update-transaction/v1",
        "phase": "active",
        "commitSha": ACTIVE,
        "previousTarget": str(state / "slots" / PRIOR / "venv/bin/runner-fabric"),
        "newTarget": str(state / "slots" / ACTIVE / "venv/bin/runner-fabric"),
    }
    txn.write_text(json.dumps(transaction), encoding="utf-8")
    txn.chmod(0o600)
    roots = tuple(tmp_path / name for name in ("primary", "device", "mirror"))
    for root in roots:
        root.mkdir(mode=0o700)
    env = dict(zip(KEYS, (str(p) for p in roots), strict=True))
    safety = OperatorSafetyGuard(
        tmp_path / "operator-stop",
        RetentionPolicy(),
        retention_confirmed=True,
    )
    calls = []

    def fake(cmd, **kwargs):
        assert cmd[:2] == [module.sys.executable, "-B"]
        assert kwargs["timeout"] == 120
        assert kwargs["stderr"] == module.subprocess.DEVNULL
        assert kwargs["env"]["HOME"] == str(home)
        assert "RUNNER_MCP_GITHUB_TOKEN" not in kwargs["env"]
        assert "--commit" in cmd
        rev = cmd[cmd.index("--commit") + 1]
        assert rev in (ACTIVE, PRIOR)
        filename = Path(cmd[2]).name
        calls.append((filename, rev))
        if blocked is not None and filename == blocked:
            return SimpleNamespace(returncode=2, stdout=b"")
        if filename == "control_plane_bundle_mirror.py":
            data = {
                "status": "PASS",
                "commitSha": rev,
                "separateDevice": True,
                "alreadyStored": already,
            }
        else:
            data = {
                "status": "PASS",
                "commitSha": rev,
                "retentionDays": 365,
                "bytes": 100,
                "fileCount": 33,
            }
        return SimpleNamespace(returncode=0, stdout=json.dumps(data).encode())

    monkeypatch.setattr(
        module,
        "_checked_tool",
        lambda directory, filename: directory / filename,
    )
    runner = ProtectedReleaseArchiveMirror(
        environment=env,
        safety=safety,
        readiness=Ready(ready),
        home=home,
        runner=fake,
    )
    return runner, calls, txn


@pytest.mark.parametrize("already", [False, True])
def test_only_two_trusted_pins_and_idempotent_counts(tmp_path, monkeypatch, already):
    mirror, calls, txn = _setup(tmp_path, monkeypatch, already=already)
    before = txn.read_bytes()
    result = mirror.run()
    assert result["state"] == "qualified"
    assert result["protectedRevisionCount"] == 2
    assert result["verifiedCount"] == 2
    assert result["mirroredCount"] == (0 if already else 2)
    assert result["alreadyStoredCount"] == (2 if already else 0)
    assert not result["restoreTriggered"]
    assert not result["updateTriggered"]
    assert not result["deleteTriggered"]
    assert txn.read_bytes() == before
    assert calls == [
        ("control_plane_bundle_custody.py", ACTIVE),
        ("control_plane_bundle_mirror.py", ACTIVE),
        ("control_plane_bundle_custody.py", ACTIVE),
        ("control_plane_bundle_custody.py", PRIOR),
        ("control_plane_bundle_mirror.py", PRIOR),
        ("control_plane_bundle_custody.py", PRIOR),
    ]


def test_missing_independent_device_fails_before_mutation(tmp_path, monkeypatch):
    mirror, calls, _ = _setup(tmp_path, monkeypatch, ready=False)
    with pytest.raises(ProtectedReleaseMirrorError, match="independent-storage-not-ready"):
        mirror.run()
    assert calls == []


def test_corrupted_first_party_receipt_fails_closed(tmp_path, monkeypatch):
    mirror, calls, _ = _setup(
        tmp_path,
        monkeypatch,
        blocked="control_plane_bundle_custody.py",
    )
    with pytest.raises(ProtectedReleaseMirrorError, match="first-party-execution-failed"):
        mirror.run()
    assert calls == [("control_plane_bundle_custody.py", ACTIVE)]


def test_disabled_operator_stop_blocks_backup(tmp_path, monkeypatch):
    mirror, calls, _ = _setup(tmp_path, monkeypatch)
    mirror.safety.stop_file.touch()
    with pytest.raises(OperatorStopActive):
        mirror.run()
    assert calls == []


def test_changed_trusted_transaction_is_rejected(tmp_path, monkeypatch):
    mirror, calls, txn = _setup(tmp_path, monkeypatch)
    original = mirror.runner

    def changing_runner(cmd, **kwargs):
        output = original(cmd, **kwargs)
        if Path(cmd[2]).name == "control_plane_bundle_mirror.py":
            content = json.loads(txn.read_text(encoding="utf-8"))
            content["commitSha"] = "c" * 40
            txn.write_text(json.dumps(content), encoding="utf-8")
            txn.chmod(0o600)
        return output

    mirror.runner = changing_runner
    with pytest.raises(ProtectedReleaseMirrorError, match="protected-transaction"):
        mirror.run()
    assert not any(rev == PRIOR for _, rev in calls)


def test_production_tool_pin_rejects_missing_or_tampered_script(tmp_path):
    directory = tmp_path / "tools"
    directory.mkdir(mode=0o700)
    with pytest.raises(ProtectedReleaseMirrorError, match="first-party-tool-unavailable"):
        module._checked_tool(directory, "control_plane_bundle_mirror.py")
    script = directory / "control_plane_bundle_mirror.py"
    script.write_text("print('untrusted')", encoding="utf-8")
    script.chmod(0o600)
    with pytest.raises(ProtectedReleaseMirrorError, match="first-party-tool-untrusted"):
        module._checked_tool(directory, script.name)
