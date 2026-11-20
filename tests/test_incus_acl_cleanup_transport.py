"""#520: negative tests for the sole first-party OS-authorized revoke call."""

from __future__ import annotations

import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner_mcp import incus_acl_cleanup_transport as sut


def admit_root_owned_install(monkeypatch):
    """Synthetic nonroot server and immutable root-owned installed file."""
    monkeypatch.setattr(sut.os, "geteuid", lambda: 1001)

    def fake_lstat(path):
        if str(path) == str(sut._HELPER):
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o500,
                st_uid=0,
                st_nlink=1,
            )
        if path in sut._ROOT_DIRS:
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        raise FileNotFoundError()

    monkeypatch.setattr(Path, "lstat", fake_lstat)


@pytest.mark.parametrize(
    ("result", "state"),
    [
        ("INCUS_ACL_REVOKE=PASS:already_restored\n", "already_restored"),
        ("INCUS_ACL_REVOKE=PASS:revoke_only\n", "revoked"),
    ],
)
def test_single_fixed_command_and_only_bounded_success(monkeypatch, result, state):
    admit_root_owned_install(monkeypatch)
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, result, "")

    monkeypatch.setattr(sut.subprocess, "run", run)
    assert sut.revoke_fixed_incus_qualification_acl() == {
        "schemaVersion": sut._SCHEMA,
        "state": state,
        "normalActivationEnabled": False,
    }
    assert len(calls) == 1
    argv, params = calls[0]
    assert argv == (
        "/usr/bin/sudo", "-n", "--", "/usr/bin/python3", "-I", "-S",
        "/usr/local/sbin/runner-mcp-incus-acl-revoke",
    )
    assert params["shell"] is False
    assert params["stdin"] == subprocess.DEVNULL
    assert params["stderr"] == subprocess.DEVNULL
    assert params["timeout"] == 20
    assert params["cwd"] == "/"
    assert "HOME" not in params["env"]
    assert "PYTHONPATH" not in params["env"]


@pytest.mark.parametrize(
    "changed",
    [
        {"st_mode": stat.S_IFREG | 0o777},
        {"st_mode": stat.S_IFLNK | 0o777},
        {"st_mode": stat.S_IFREG | 0o550},
        {"st_uid": 1001},
        {"st_nlink": 2},
    ],
)
def test_untrusted_installed_helper_stops_without_sudo(monkeypatch, changed):
    admit_root_owned_install(monkeypatch)
    original = Path.lstat

    def faulty(self):
        result = original(self)
        if self == sut._HELPER:
            data = {
                "st_mode": result.st_mode,
                "st_uid": result.st_uid,
                "st_nlink": result.st_nlink,
            }
            data.update(changed)
            return SimpleNamespace(**data)
        return result

    monkeypatch.setattr(Path, "lstat", faulty)
    monkeypatch.setattr(sut.subprocess, "run", lambda *a, **k: pytest.fail("sudo invoked"))
    assert sut.revoke_fixed_incus_qualification_acl()["reasonCode"] == (
        "privileged_helper_unavailable"
    )


@pytest.mark.parametrize("change", ["nonroot", "missing", "world_writable", "symlink"])
def test_root_directory_or_caller_mismatch_never_invokes_sudo(monkeypatch, change):
    admit_root_owned_install(monkeypatch)
    original = Path.lstat
    if change == "nonroot":
        monkeypatch.setattr(sut.os, "geteuid", lambda: 0)
    else:
        def broken(self):
            row = original(self)
            if self == Path("/usr/local/sbin"):
                if change == "missing":
                    raise FileNotFoundError()
                if change == "world_writable":
                    return SimpleNamespace(st_mode=stat.S_IFDIR | 0o777, st_uid=0)
                return SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_uid=0)
            return row
        monkeypatch.setattr(Path, "lstat", broken)
    monkeypatch.setattr(sut.subprocess, "run", lambda *a, **k: pytest.fail("sudo invoked"))
    assert sut.revoke_fixed_incus_qualification_acl()["state"] == "unavailable"


@pytest.mark.parametrize(
    ("rc", "output"),
    [
        (1, ""),
        (1, "INCUS_ACL_REVOKE=PASS:revoke_only\n"),
        (0, "INCUS_ACL_REVOKE=STOP:root_file_untrusted\n"),
        (0, "INCUS_ACL_REVOKE=PASS:revoke_only\nunexpected\n"),
        (0, "INCUS_ACL_REVOKE=PASS:revoke_only"),
        (0, "INCUS_ACL_REVOKE=PASS:revoked\n"),
        (0, ""),
    ],
)
def test_sudo_failure_or_unexpected_output_never_claims_restored(
    monkeypatch, rc, output,
):
    admit_root_owned_install(monkeypatch)
    monkeypatch.setattr(
        sut.subprocess, "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, rc, output, "private"),
    )
    result = sut.revoke_fixed_incus_qualification_acl()
    assert result == {
        "schemaVersion": sut._SCHEMA,
        "state": "unavailable",
        "normalActivationEnabled": False,
        "reasonCode": "privileged_helper_unavailable",
    }


@pytest.mark.parametrize(
    "error", [OSError("secret"), subprocess.TimeoutExpired("sudo", 20)],
)
def test_unavailable_command_and_timeout_are_sanitized(monkeypatch, error):
    admit_root_owned_install(monkeypatch)

    def fail(argv, **kwargs):
        raise error

    monkeypatch.setattr(sut.subprocess, "run", fail)
    result = sut.revoke_fixed_incus_qualification_acl()
    assert result["state"] == "unavailable"
    assert result["reasonCode"] == "privileged_helper_unavailable"
    assert "secret" not in str(result)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("admission", "admission"),
        ("spawn", "spawn_or_timeout"),
        ("reject", "command_rejected"),
        ("receipt", "invalid_receipt"),
    ],
)
def test_failure_journal_stages_are_bounded_and_private(
    monkeypatch, caplog, kind, expected
):
    """A failed managed call must be diagnosable without logging stderr or paths."""
    admit_root_owned_install(monkeypatch)

    def run(argv, **kwargs):
        if kind == "spawn":
            raise OSError("PRIVATE_SPAWN_DETAIL")
        if kind == "reject":
            return subprocess.CompletedProcess(argv, 1, "", "PRIVATE_SUDO_DETAIL")
        return subprocess.CompletedProcess(
            argv, 0, "UNEXPECTED_PRIVATE_REPLY\n", "PRIVATE_SUDO_DETAIL"
        )

    if kind == "admission":
        monkeypatch.setattr(sut, "_root_installation_present", lambda: False)
        monkeypatch.setattr(
            sut.subprocess, "run", lambda *a, **k: pytest.fail("sudo invoked")
        )
    else:
        monkeypatch.setattr(sut.subprocess, "run", run)

    with caplog.at_level("WARNING", logger=sut.__name__):
        result = sut.revoke_fixed_incus_qualification_acl()

    assert result == {
        "schemaVersion": sut._SCHEMA,
        "state": "unavailable",
        "normalActivationEnabled": False,
        "reasonCode": "privileged_helper_unavailable",
    }
    assert [r.message for r in caplog.records] == [
        f"incus_acl_revoke_unavailable stage={expected}"
    ]
    assert "PRIVATE" not in caplog.text
    assert "/usr/local/sbin" not in caplog.text


def test_success_creates_no_transport_warning(monkeypatch, caplog):
    admit_root_owned_install(monkeypatch)
    monkeypatch.setattr(
        sut.subprocess, "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, "INCUS_ACL_REVOKE=PASS:already_restored\n", ""
        ),
    )
    with caplog.at_level("WARNING", logger=sut.__name__):
        result = sut.revoke_fixed_incus_qualification_acl()
    assert result["state"] == "already_restored"
    assert not caplog.records
