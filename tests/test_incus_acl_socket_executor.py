"""#520 — synthetische rootgrens-, replay-, audit- en crashregressies.

Deze tests starten GEEN echte root-unit, sudo, setfacl of Incus-actie.
De echte hostcanary en oorspronkelijke MCP-acceptatie zijn aparte gates.
"""

from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import os
import stat
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
    monkeypatch.setattr(sut, "_binding", lambda: (1001, 1001, 108))
    monkeypatch.setattr(sut, "_socket_generation", lambda _gid: "10:20:30")
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
            f"{NONCE} PENDING\n{NONCE} PASS:already_restored:10:20:30\n"
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
        assert f.read().endswith(f"{NONCE} PASS:{state}:10:20:30\n".encode())


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
        checks = iter([True, False])
        monkeypatch.setattr(sut, "_same_peer", lambda *_a: next(checks))
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
        f"{NONCE} PASS:revoked:10:20:30\n",
        f"{NONCE} PENDING\n{NONCE} PENDING\n",
        (f"{NONCE} PENDING\n{NONCE} PASS:already_restored:10:20:30\n"
         f"{NONCE} PASS:revoked:10:20:30\n"),
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
        sut._peer(Peer(), 1001, 1001, 108)


def test_foreign_cgroup_is_denied(monkeypatch):
    class Peer:
        def getsockopt(self, *_a):
            return struct.pack("3i", 123, 1001, 1001)

    monkeypatch.setattr(
        Path, "read_text", lambda path, **_kw: "0::/user.slice/foreign.service\n"
    )
    with pytest.raises(sut.Denied, match="peer_unit"):
        sut._peer(Peer(), 1001, 1001, 108)


@pytest.mark.parametrize(
    ("groups", "cap_eff", "owner_gid", "code"),
    [
        ("1001 108", "0000000000000000", 1001, "peer_socket_group"),
        ("", "0000000000000001", 1001, "peer_security"),
        ("1001", "0000000000000000", 108, "peer_socket_group"),
    ],
)
def test_serving_peer_cannot_gain_socket_group_or_effective_capability(
    monkeypatch, groups, cap_eff, owner_gid, code,
):
    class Peer:
        def getsockopt(self, *_a):
            return struct.pack("3i", 123, 1001, owner_gid)

    cgroup = (
        "/user.slice/user-1001.slice/user@1001.service/"
        "app.slice/runner-mcp.service"
    )
    def read(path, **_kw):
        value = str(path)
        if value == "/proc/123/cgroup":
            return f"0::{cgroup}\n"
        if value.endswith("/cgroup.procs"):
            return "123\n"
        if value == "/proc/123/status":
            return (
                "Uid:\t1001\t1001\t1001\t1001\n"
                f"Gid:\t{owner_gid}\t{owner_gid}\t{owner_gid}\t{owner_gid}\n"
                "NoNewPrivs:\t1\n"
                "CapInh:\t0000000000000000\n"
                "CapPrm:\t0000000000000000\n"
                f"CapEff:\t{cap_eff}\n"
                "CapAmb:\t0000000000000000\n"
                f"Groups:\t{groups}\n"
            )
        if value == "/proc/123/comm":
            return "runner-mcp\n"
        raise AssertionError(value)
    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(sut, "_start_ticks", lambda _pid: "55")
    with pytest.raises(sut.Denied, match=code):
        sut._peer(Peer(), 1001, owner_gid, 108)


@pytest.mark.parametrize("cap_key", ["CapInh", "CapPrm", "CapAmb"])
def test_peer_cannot_hold_reactivatable_capabilities(monkeypatch, cap_key):
    """Effective=0 must not hide capabilities retained in another set."""
    class Peer:
        def getsockopt(self, *_args):
            return struct.pack("3i", 123, 1001, 1001)

    cgroup = (
        "/user.slice/user-1001.slice/user@1001.service/"
        "app.slice/runner-mcp.service"
    )

    def read(path, **_kw):
        value = str(path)
        if value == "/proc/123/cgroup":
            return f"0::{cgroup}\n"
        if value.endswith("/cgroup.procs"):
            return "123\n"
        if value == "/proc/123/status":
            caps = {key: "0000000000000000" for key in (
                "CapInh", "CapPrm", "CapEff", "CapAmb"
            )}
            caps[cap_key] = "0000000000000001"
            return (
                "Uid:\t1001\t1001\t1001\t1001\n"
                "Gid:\t1001\t1001\t1001\t1001\n"
                "NoNewPrivs:\t1\n"
                "Groups:\t100 1001\n"
                + "".join(f"{key}:\t{value}\n" for key, value in caps.items())
            )
        if value == "/proc/123/comm":
            return "runner-mcp\n"
        raise AssertionError(value)

    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(sut, "_start_ticks", lambda _pid: "55")
    with pytest.raises(sut.Denied, match="peer_security"):
        sut._peer(Peer(), 1001, 1001, 108)


@pytest.mark.parametrize(
    ("uid_map", "gid_map", "allow"),
    [
        ("1001 1001 1\n", "1001 1001 1\n", True),
        ("0 0 1\n1001 1001 1\n", "1001 1001 1\n", False),
        ("1001 1001 2\n", "1001 1001 1\n", False),
        ("1001 1001 1\n", "0 0 1\n1001 1001 1\n", False),
        ("1001 1001 1\n", "1001 1001 2\n", False),
    ],
)
def test_original_peer_user_namespace_must_map_only_its_service_ids(
    monkeypatch, uid_map, gid_map, allow,
):
    """Root UID/GID or even one extra mapping must fail closed."""
    class Peer:
        def getsockopt(self, *_args):
            return struct.pack("3i", 123, 1001, 1001)

    cgroup = (
        "/user.slice/user-1001.slice/user@1001.service/"
        "app.slice/runner-mcp.service"
    )

    def read(path, **_kw):
        key = str(path)
        if key == "/proc/123/cgroup":
            return f"0::{cgroup}\n"
        if key.endswith("/cgroup.procs"):
            return "123\n"
        if key == "/proc/123/status":
            return (
                "Uid:\t1001\t1001\t1001\t1001\n"
                "Gid:\t1001\t1001\t1001\t1001\n"
                "NoNewPrivs:\t1\n"
                "CapInh:\t0000000000000000\n"
                "CapPrm:\t0000000000000000\n"
                "CapEff:\t0000000000000000\n"
                "CapAmb:\t0000000000000000\n"
                "Groups:\t100 1001\n"
            )
        if key == "/proc/123/uid_map":
            return uid_map
        if key == "/proc/123/gid_map":
            return gid_map
        if key == "/proc/123/comm":
            return "runner-mcp\n"
        raise AssertionError(key)

    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(sut, "_start_ticks", lambda _pid: "55555")
    if allow:
        assert sut._peer(Peer(), 1001, 1001, 108) == (123, "55555")
    else:
        with pytest.raises(sut.Denied, match="peer_namespace"):
            sut._peer(Peer(), 1001, 1001, 108)


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



def test_peer_replaced_during_queue_denied_before_root_helper_or_pending(
    monkeypatch, tmp_path,
):
    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        seen = iter([(123, "55555"), (123, "55556")])
        monkeypatch.setattr(sut, "_peer", lambda *_args: next(seen))
        client = Client()
        with pytest.raises(sut.Denied, match="peer_generation"):
            sut.execute(client)
        assert called == []
        assert client.reply == []
        f.seek(0)
        assert f.read() == b""


def test_peer_security_drift_during_queue_denied_before_root_helper(
    monkeypatch, tmp_path,
):
    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        seen = 0

        def peer_recheck(*_args):
            nonlocal seen
            seen += 1
            if seen == 2:
                raise sut.Denied("peer_security")
            return 123, "55555"

        monkeypatch.setattr(sut, "_peer", peer_recheck)
        client = Client()
        with pytest.raises(sut.Denied, match="peer_security"):
            sut.execute(client)
        assert called == []
        assert client.reply == []
        f.seek(0)
        assert f.read() == b""


def test_old_success_is_not_replayed_after_socket_grant_generation_change(
    monkeypatch, tmp_path,
):
    """An old ACK must never claim restoration of a later temporary grant."""
    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        sut.execute(Client(NONCE))
        assert called == ["already_restored"]
        monkeypatch.setattr(sut, "_socket_generation", lambda _gid: "10:20:31")
        replay = Client(NONCE)
        with pytest.raises(sut.Denied, match="stale_replay"):
            sut.execute(replay)
        assert replay.reply == []
        assert called == ["already_restored"]
        # A *fresh* request is still able to invoke the fixed revoke helper.
        fresh = Client(OTHER)
        sut.execute(fresh)
        assert len(called) == 2
        assert fresh.reply == [
            f"RMCP520/1 {OTHER} PASS already_restored\n".encode()
        ]


def test_socket_fingerprint_requires_root_socket_and_no_posix_extended_acl(
    monkeypatch,
):
    baseline = {
        "st_dev": 10, "st_ino": 20, "st_ctime_ns": 30,
        "st_mode": stat.S_IFSOCK | 0o660,
        "st_uid": 0, "st_gid": 108, "st_nlink": 1,
    }
    monkeypatch.setattr(
        sut.os, "lstat", lambda _path: SimpleNamespace(**baseline)
    )

    def no_acl(_path, _name, **_kw):
        raise OSError(errno.ENODATA, "No ACL")

    monkeypatch.setattr(sut.os, "getxattr", no_acl)
    assert sut._socket_generation(108) == "10:20:30"

    monkeypatch.setattr(sut.os, "getxattr", lambda *_a, **_kw: b"new grant")
    with pytest.raises(sut.Denied, match="socket_acl_unverified"):
        sut._socket_generation(108)
    monkeypatch.setattr(sut.os, "getxattr", no_acl)
    baseline["st_gid"] = 999
    with pytest.raises(sut.Denied, match="socket_generation"):
        sut._socket_generation(108)


def test_socket_mutation_during_acl_readback_is_denied(monkeypatch):
    ctimes = iter([30, 31])

    def stat_socket(_path):
        return SimpleNamespace(
            st_dev=10, st_ino=20, st_ctime_ns=next(ctimes),
            st_mode=stat.S_IFSOCK | 0o660,
            st_uid=0, st_gid=108, st_nlink=1,
        )

    def no_acl(_path, _name, **_kw):
        raise OSError(errno.ENODATA, "No ACL")

    monkeypatch.setattr(sut.os, "lstat", stat_socket)
    monkeypatch.setattr(sut.os, "getxattr", no_acl)
    with pytest.raises(sut.Denied, match="socket_generation"):
        sut._socket_generation(108)


def test_durable_audit_survives_client_disconnect_before_ack(
    monkeypatch, tmp_path, capsys,
):
    """A dropped ACK cannot erase the root-side durable operation record."""
    class Disconnect(Client):
        def sendall(self, _value):
            raise BrokenPipeError("synthetic peer disconnected")

    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        with pytest.raises(BrokenPipeError):
            sut.execute(Disconnect())
        f.seek(0)
        assert f.read().endswith(f"{NONCE} PASS:already_restored:10:20:30\n".encode())
    assert called == ["already_restored"]
    logs = capsys.readouterr().err
    assert "RMCP520_ROOT_DURABLE=PASS receipt=" in logs
    assert "RMCP520_ROOT_SEND=PASS" not in logs


def test_ledger_append_retries_partial_writes(monkeypatch, tmp_path):
    """A simulated short write cannot create a fictitious durable receipt."""
    target = tmp_path / "partial-write-ledger"
    with target.open("w+b") as f:
        original = os.write

        def partial_write(fd, data):
            return original(fd, data[:max(1, len(data) // 3)])

        monkeypatch.setattr(sut.os, "write", partial_write)
        sut._append(f.fileno(), f"{NONCE} PENDING")
        f.seek(0)
        assert f.read() == f"{NONCE} PENDING\n".encode()


def test_ledger_append_zero_write_denied_without_claimed_ack(
    monkeypatch, tmp_path,
):
    with (tmp_path / "zero-write-ledger").open("w+b") as f:
        monkeypatch.setattr(sut.os, "write", lambda _fd, _data: 0)
        with pytest.raises(sut.Denied, match="ledger_io"):
            sut._append(f.fileno(), f"{NONCE} PENDING")
        f.seek(0)
        assert f.read() == b""


def test_ledger_short_read_must_not_hide_later_pending(
    monkeypatch, tmp_path,
):
    # First entry is syntactically valid; the omitted later PENDING must
    # not become invisible to a later request.
    first = f"{NONCE} PENDING\n{NONCE} PASS:already_restored:10:20:30\n".encode()
    later = f"{OTHER} PENDING\n".encode()
    with (tmp_path / "short-read-ledger").open("w+b") as f:
        f.write(first + later)
        f.flush()
        real_read = os.read
        monkeypatch.setattr(
            sut.os, "read",
            lambda fd, size: real_read(fd, min(size, len(first))),
        )
        with pytest.raises(sut.Denied, match="ledger_invalid"):
            sut._records(f.fileno())


def test_existing_pending_blocks_even_successful_cached_replay(
    monkeypatch, tmp_path,
):
    """A cached success must not bypass another unresolved root operation."""
    history = (
        f"{NONCE} PENDING\n"
        f"{NONCE} PASS:already_restored:10:20:30\n"
        f"{OTHER} PENDING\n"
    ).encode("ascii")
    with (tmp_path / "pending-replay-ledger").open("w+b") as f:
        f.write(history)
        f.flush()
        called = setup_synthetic(monkeypatch, f.fileno())
        replay = Client(NONCE)
        with pytest.raises(sut.Denied, match="recovery_required"):
            sut.execute(replay)
        assert replay.reply == []
        assert called == []
        f.seek(0)
        assert f.read() == history


def test_root_replay_is_logged_as_replay_not_new_durable_action(
    monkeypatch, tmp_path, capsys,
):
    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        sut.execute(Client(NONCE))
        capsys.readouterr()
        sut.execute(Client(NONCE))
    assert called == ["already_restored"]
    journal = capsys.readouterr().err
    assert "RMCP520_ROOT_REPLAY=PASS receipt=" in journal
    assert "RMCP520_ROOT_DURABLE=PASS" not in journal


def test_loss_of_peer_authority_after_helper_does_not_create_pass(
    monkeypatch, tmp_path,
):
    with (tmp_path / "ledger").open("w+b") as f:
        called = setup_synthetic(monkeypatch, f.fileno())
        checks = 0

        def peer(*_args):
            nonlocal checks
            checks += 1
            if checks == 3:
                raise sut.Denied("peer_security")
            return 123, "55555"

        monkeypatch.setattr(sut, "_peer", peer)
        client = Client()
        with pytest.raises(sut.Denied, match="peer_security"):
            sut.execute(client)
        assert called == ["already_restored"]
        assert client.reply == []
        f.seek(0)
        assert f.read() == f"{NONCE} PENDING\n".encode()


def test_socket_unit_keeps_root_inode_custody_and_owner_group_access():
    """The service account must never own/chmod the privileged IPC inode."""
    path = (
        Path(__file__).resolve().parents[1]
        / "packaging/systemd/runner-mcp-incus-acl-revoke.socket.in"
    )
    source = path.read_text(encoding="utf-8")
    assert "SocketUser=root\n" in source
    assert "SocketGroup=@SERVICE_PRIMARY_GROUP@\n" in source
    assert "SocketMode=0660\n" in source
    assert "SocketUser=@SERVICE_ACCOUNT@" not in source
    assert "ListenStream=/run/runner-mcp-incus-acl-revoke.sock\n" in source
    assert "Accept=yes\n" in source


def test_root_script_contains_no_dynamic_cli_shell_or_acl_grant():
    assert sut._ACTION == "incus_qualification_acl_revoke"
    assert sut._HELPER.name == "runner-mcp-incus-acl-revoke"
    assert sut._OUTCOMES == {
        "INCUS_ACL_REVOKE=PASS:already_restored\n": "already_restored",
        "INCUS_ACL_REVOKE=PASS:revoke_only\n": "revoked",
    }
    assert sut._MAX_ENTRIES <= 512


@pytest.mark.parametrize(
    ("target", "phase"),
    [
        ("_root_only", "root_context"),
        ("_binding", "host_policy"),
        ("_peer", "peer_inspect"),
        ("_ledger_open", "ledger_open"),
    ],
)
def test_runtime_before_ledger_is_bounded_without_execution(
    monkeypatch, target, phase,
):
    """A host sandbox syscall error must not expose paths or start root work."""
    monkeypatch.setattr(sut, "_root_only", lambda: None)
    monkeypatch.setattr(sut, "_binding", lambda: (1001, 1001, 108))
    monkeypatch.setattr(sut, "_peer", lambda *_args: (123, "55555"))
    monkeypatch.setattr(
        sut, "_ledger_open",
        lambda: pytest.fail("ledger must not be opened before a failing stage"),
    )
    monkeypatch.setattr(
        sut, "_helper",
        lambda: pytest.fail("root helper must not run on a pre-ledger error"),
    )

    def denied_runtime(*_args):
        raise PermissionError("PRIVATE_PATH_AND_TOKEN_MUST_NOT_LEAK")

    monkeypatch.setattr(sut, target, denied_runtime)
    client = Client()
    with pytest.raises(sut.RuntimePhase) as raised:
        sut.execute(client)
    assert str(raised.value) == phase
    assert "PRIVATE_PATH" not in str(raised.value)
    assert client.reply == []


def test_runtime_socket_read_is_bounded_and_never_opens_ledger(monkeypatch):
    monkeypatch.setattr(sut, "_root_only", lambda: None)
    monkeypatch.setattr(sut, "_binding", lambda: (1001, 1001, 108))
    monkeypatch.setattr(sut, "_peer", lambda *_args: (123, "55555"))
    monkeypatch.setattr(
        sut, "_ledger_open", lambda: pytest.fail("unexpected ledger open"),
    )

    class BrokenClient(Client):
        def recv(self, _count):
            raise OSError("PRIVATE_PATH_AND_TOKEN_MUST_NOT_LEAK")

    with pytest.raises(sut.RuntimePhase, match="^request_read$"):
        sut.execute(BrokenClient())


def test_runtime_classification_never_swallow_explicit_denial(monkeypatch):
    def explicit_deny():
        raise sut.Denied("peer_security")

    with pytest.raises(sut.Denied, match="peer_security"):
        sut._checked("root_context", explicit_deny)


def test_invalid_phase_never_calls_callback():
    with pytest.raises(sut.RuntimePhase, match="unknown"):
        sut._checked("PRIVATE_PATH", lambda: pytest.fail("should not call"))


def test_root_journal_reports_only_runtime_phase(monkeypatch, capsys):
    class SocketContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def faulty_execute(_conn):
        raise sut.RuntimePhase("peer_inspect") from PermissionError(
            "PRIVATE_PATH_AND_TOKEN_MUST_NOT_LEAK"
        )

    monkeypatch.setattr(sut.socket, "socket", lambda **_kwargs: SocketContext())
    monkeypatch.setattr(sut, "execute", faulty_execute)
    assert sut.main() == 1
    journal = capsys.readouterr().err
    assert journal == "RMCP520_ROOT=DENIED reason=runtime stage=peer_inspect\n"
    assert "PRIVATE_PATH" not in journal
    assert "PermissionError" not in journal


@pytest.mark.parametrize(
    ("phase", "target"),
    [
        ("peer_credentials", "<socket>"),
        ("peer_cgroup", "/proc/123/cgroup"),
        ("peer_members", "/sys/fs/cgroup" + (
            "/user.slice/user-1001.slice/user@1001.service/"
            "app.slice/runner-mcp.service/cgroup.procs"
        )),
        ("peer_status", "/proc/123/status"),
        ("peer_uid_map", "/proc/123/uid_map"),
        ("peer_gid_map", "/proc/123/gid_map"),
        ("peer_comm", "/proc/123/comm"),
        ("peer_start_ticks", "/proc/123/stat"),
    ],
)
def test_peer_individual_runtime_phase_does_not_leak(
    monkeypatch, phase, target,
):
    """One source-level sandbox read error yields only a fixed phase code."""
    cgroup = (
        "/user.slice/user-1001.slice/user@1001.service/"
        "app.slice/runner-mcp.service"
    )
    proc_status = (
        "Uid:\\t1001 1001 1001 1001\\n"
        "Gid:\\t1001 1001 1001 1001\\n"
        "Groups:\\t1001\\n"
        "NoNewPrivs:\\t1\\n"
        "CapInh:\\t0000000000000000\\n"
        "CapPrm:\\t0000000000000000\\n"
        "CapEff:\\t0000000000000000\\n"
        "CapAmb:\\t0000000000000000\\n"
    )
    values = {
        "/proc/123/cgroup": "0::" + cgroup + "\\n",
        "/sys/fs/cgroup" + cgroup + "/cgroup.procs": "123\\n",
        "/proc/123/status": proc_status,
        "/proc/123/uid_map": "1001 1001 1\\n",
        "/proc/123/gid_map": "1001 1001 1\\n",
        "/proc/123/comm": "runner-mcp\\n",
        "/proc/123/stat": "123 (runner-mcp) " + " ".join(["0"] * 20),
    }

    class FakePath:
        def __init__(self, name):
            self.name = str(name)

        def read_text(self, encoding="ascii"):
            assert encoding == "ascii"
            if self.name == target:
                raise PermissionError("PRIVATE_HOST_DATA_MUST_NOT_LEAK")
            return values[self.name]

    class FakeConn:
        def getsockopt(self, _level, _option, _length):
            if target == "<socket>":
                raise PermissionError("PRIVATE_HOST_DATA_MUST_NOT_LEAK")
            return struct.pack("3i", 123, 1001, 1001)

    monkeypatch.setattr(sut, "Path", FakePath)
    with pytest.raises(sut.RuntimePhase) as caught:
        sut._peer(FakeConn(), 1001, 1001, 108)
    assert str(caught.value) == phase
    assert "PRIVATE_HOST_DATA" not in str(caught.value)

