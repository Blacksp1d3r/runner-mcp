"""#520 — synthetische rootgrens-, replay-, audit- en crashregressies.

Deze tests starten GEEN echte root-unit, sudo, setfacl of Incus-actie.
De echte hostcanary en oorspronkelijke MCP-acceptatie zijn aparte gates.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/incus_acl_socket_executor.py"
SPEC = importlib.util.spec_from_file_location("incus_acl_socket_executor_source", SOURCE)
assert SPEC is not None and SPEC.loader is not None
sut = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sut)

NONCE = "a" * 32
OTHER = "b" * 32


class Client:
    """Vast protocol zonder gebruiker, pad, opdracht of ACL-invoer."""

    def __init__(self, token=NONCE):
        self.payload = f"RMCP520/1 {token}\n".encode("ascii")
        self.reply = []
        self.timeout = None

    def recv(self, _count):
        data, self.payload = self.payload, b""
        return data

    def sendall(self, value):
        self.reply.append(value)

    def settimeout(self, value):
        self.timeout = value


def setup_synthetic(monkeypatch, fd, *, state="already_restored"):
    """Simuleer alleen de reeds geautoriseerde rootgrens."""
    count = []
    monkeypatch.setattr(sut, "_root_only", lambda: None)
    monkeypatch.setattr(sut, "_binding", lambda: (1001, 1001))
    monkeypatch.setattr(sut, "_peer", lambda *_a: (123, "55555"))
    monkeypatch.setattr(sut, "_same_peer", lambda *_a: True)
    monkeypatch.setattr(sut, "_ledger_open", lambda: os.dup(fd))

    def helper():
        count.append(state)
        return state

    monkeypatch.setattr(sut, "_helper", helper)
    return count


def test_first_durable_ack_then_replay_executes_fixed_helper_once(monkeypatch, tmp_path):
    file = tmp_path / "root-ledger"
    with file.open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        first = Client()
        sut.execute(first)
        second = Client()
        sut.execute(second)
        expected = f"RMCP520/1 {NONCE} PASS already_restored\n".encode()
        assert first.reply == [expected]
        assert second.reply == [expected]
        assert called == ["already_restored"]
        f.seek(0)
        assert f.read() == (
            f"{NONCE} PENDING\n{NONCE} PASS:already_restored\n"
        ).encode()
        assert first.timeout == 3


@pytest.mark.parametrize("state", ["already_restored", "revoked"])
def test_root_ack_only_after_persisted_helper_result(monkeypatch, tmp_path, state):
    with (tmp_path / "ledger").open("w+b") as f:
        count = setup_synthetic(monkeypatch, f.fileno(), state=state)
        client = Client()
        sut.execute(client)
        assert count == [state]
        assert client.reply == [f"RMCP520/1 {NONCE} PASS {state}\n".encode()]
        f.seek(0)
        assert f.read().endswith(f"{NONCE} PASS:{state}\n".encode())


def test_helper_failure_keeps_pending_and_blocks_new_work(monkeypatch, tmp_path):
    with (tmp_path / "ledger").open("w+b") as f:
        count = setup_synthetic(monkeypatch, f.fileno())

        def fail():
            count.append("called")
            raise sut.Denied("helper_denied")

        monkeypatch.setattr(sut, "_helper", fail)
        first = Client()
        with pytest.raises(sut.Denied, match="helper_denied"):
            sut.execute(first)
        assert first.reply == []
        f.seek(0)
        assert f.read() == f"{NONCE} PENDING\n".encode()
        second = Client(OTHER)
        with pytest.raises(sut.Denied, match="recovery_required"):
            sut.execute(second)
        assert second.reply == []
        assert count == ["called"]


def test_peer_generation_changed_keeps_pending_and_no_success(monkeypatch, tmp_path):
    with (tmp_path / "ledger").open("w+b") as f:
        count = setup_synthetic(monkeypatch, f.fileno())
        monkeypatch.setattr(sut, "_same_peer", lambda *_a: False)
        client = Client()
        with pytest.raises(sut.Denied, match="peer_generation"):
            sut.execute(client)
        assert count == ["already_restored"]
        assert client.reply == []
        f.seek(0)
        assert f.read() == f"{NONCE} PENDING\n".encode()


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"EXEC /bin/sh\n",
        b"RMCP520/1 ../var/lib/incus\n",
        b"RMCP520/1 " + b"a" * 32 + b" GRANT\n",
        b"RMCP520/1 " + b"a" * 32 + b"\nINJECT\n",
        b"RMCP520/1 " + b"a" * 32,
    ],
)
def test_untrusted_command_or_parameter_is_denied_without_helper(
    monkeypatch, tmp_path, payload,
):
    with (tmp_path / "ledger").open("w+b") as f:
        count = setup_synthetic(monkeypatch, f.fileno())
        client = Client()
        client.payload = payload
        with pytest.raises(sut.Denied, match="request_invalid"):
            sut.execute(client)
        assert count == []
        f.seek(0)
        assert f.read() == b""


@pytest.mark.parametrize(
    "content",
    [
        "PRIVATE_DATA\n",
        f"{NONCE} PASS:revoked\n",
        f"{NONCE} PENDING\n{NONCE} PENDING\n",
        (f"{NONCE} PENDING\n{NONCE} PASS:already_restored\n"
         f"{NONCE} PASS:revoked\n"),
        f"{NONCE} PENDING",
        "x" * 65537,
    ],
)
def test_corrupted_or_ambiguous_ledger_never_executes_helper(
    monkeypatch, tmp_path, content,
):
    with (tmp_path / "ledger").open("w+b") as f:
        f.write(content.encode())
        f.flush()
        called = setup_synthetic(monkeypatch, f.fileno())
        with pytest.raises(sut.Denied):
            sut.execute(Client(OTHER))
        assert called == []


def test_host_root_attestation_rejects_nonroot_and_user_namespace(monkeypatch):
    monkeypatch.setattr(sut.os, "geteuid", lambda: 1001)
    with pytest.raises(sut.Denied, match="not_host_root"):
        sut._root_only()

    monkeypatch.setattr(sut.os, "geteuid", lambda: 0)
    actual_stat = sut.os.stat

    def foreign_userns(path):
        if path == "/proc/self/ns/user":
            return SimpleNamespace(st_ino=42)
        if path == "/proc/1/ns/user":
            return SimpleNamespace(st_ino=43)
        return actual_stat(path)

    monkeypatch.setattr(sut.os, "stat", foreign_userns)
    with pytest.raises(sut.Denied, match="not_host_root"):
        sut._root_only()


@pytest.mark.parametrize("uid,gid", [(1000, 1001), (1001, 0), (0, 0)])
def test_unauthorized_peer_denied_before_cgroup_and_helper(monkeypatch, uid, gid):
    class Peer:
        def getsockopt(self, _level, _name, _size):
            return struct.pack("3i", 123, uid, gid)

    with pytest.raises(sut.Denied, match="peer_credentials"):
        sut._peer(Peer(), 1001, 1001)


def test_foreign_cgroup_is_denied(monkeypatch):
    class Peer:
        def getsockopt(self, *_a):
            return struct.pack("3i", 123, 1001, 1001)

    monkeypatch.setattr(
        Path, "read_text", lambda path, **_kw: "0::/user.slice/foreign.service\n"
    )
    with pytest.raises(sut.Denied, match="peer_unit"):
        sut._peer(Peer(), 1001, 1001)


@pytest.mark.parametrize("tamper", ["host", "digest", "uid"])
def test_existing_private_policy_binding_blocks_wrong_host_or_helper(
    monkeypatch, tamper,
):
    helper = b"root-owned synthetic helper"
    fields = {
        "schema": sut._SCHEMA,
        "host_short": "unit-test-host",
        "owner_name": "test-owner",
        "owner_uid": 1001,
        "owner_gid": 1001,
        "socket_path": "/var/lib/incus/unix.socket",
        "socket_gid": 108,
        "installed_sha256": hashlib.sha256(helper).hexdigest(),
    }
    if tamper == "host":
        fields["host_short"] = "another-host"
    if tamper == "digest":
        fields["installed_sha256"] = "0" * 64
    if tamper == "uid":
        fields["owner_uid"] = -1
    monkeypatch.setattr(
        sut.os, "uname", lambda: SimpleNamespace(nodename="unit-test-host")
    )
    monkeypatch.setattr(
        sut.pwd, "getpwnam",
        lambda _name: SimpleNamespace(pw_uid=1001, pw_gid=1001),
    )
    monkeypatch.setattr(
        sut, "_trusted_file",
        lambda path, *_a, **_kw: (
            json.dumps(fields).encode() if path == sut._POLICY else helper
        ),
    )
    if tamper == "host":
        code = "host_policy"
    elif tamper == "digest":
        code = "helper_digest"
    else:
        code = "host_policy"
    with pytest.raises(sut.Denied, match=code):
        sut._binding()


def test_root_script_contains_no_dynamic_cli_shell_or_acl_grant():
    assert sut._ACTION == "incus_qualification_acl_revoke"
    assert sut._HELPER.name == "runner-mcp-incus-acl-revoke"
    assert sut._OUTCOMES == {
        "INCUS_ACL_REVOKE=PASS:already_restored\n": "already_restored",
        "INCUS_ACL_REVOKE=PASS:revoke_only\n": "revoked",
    }
    assert sut._MAX_ENTRIES <= 512
