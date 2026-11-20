"""#520 — veilige, parameterloze socketclient zonder sudo/UID-overflow-bypass."""

from __future__ import annotations

import pytest

from runner_mcp import incus_acl_cleanup_transport as sut

NONCE = "a" * 32


class FakeConnection:
    """Eén synthetische hostexecutor-reply zonder echte host/root-toegang."""

    def __init__(self, reply: bytes | None = None, error: Exception | None = None):
        self.reply = reply
        self.error = error
        self.sent = []
        self.timeout = None
        self.target = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, path):
        self.target = path
        if self.error:
            raise self.error

    def sendall(self, payload):
        self.sent.append(payload)

    def recv(self, _size):
        value, self.reply = self.reply, None
        return value or b""


def fake_transport(monkeypatch, reply=None, error=None):
    """Vervang uitsluitend het synthetische AF_UNIX endpoint."""
    conn = FakeConnection(reply, error)
    monkeypatch.setattr(sut.secrets, "token_hex", lambda length: NONCE if length == 16 else "")
    monkeypatch.setattr(sut.socket, "socket", lambda *_args: conn)
    return conn


@pytest.mark.parametrize(
    ("name", "expected"),
    [("already_restored", "already_restored"), ("revoked", "revoked")],
)
def test_fixed_action_no_sudo_and_ack_matching(monkeypatch, caplog, name, expected):
    conn = fake_transport(
        monkeypatch, f"RMCP520/1 {NONCE} PASS {name}\n".encode("ascii")
    )
    with caplog.at_level("WARNING", logger=sut.__name__):
        result = sut.revoke_fixed_incus_qualification_acl()
    assert result == {
        "schemaVersion": sut._SCHEMA,
        "state": expected,
        "normalActivationEnabled": False,
    }
    assert conn.target == "/run/runner-mcp-incus-acl-revoke.sock"
    assert conn.timeout == sut._TIMEOUT
    assert conn.sent == [f"RMCP520/1 {NONCE}\n".encode("ascii")]
    assert not caplog.records
    assert not hasattr(sut, "_SUDO_ARGV")
    assert "subprocess" not in sut.__dict__


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"PRIVATE ERROR",
        f"RMCP520/1 {'b' * 32} PASS revoked\n".encode("ascii"),
        f"RMCP520/1 {NONCE} PASS unauthorized\n".encode("ascii"),
        f"RMCP520/1 {NONCE} PASS revoked".encode("ascii"),
        f"RMCP520/1 {NONCE} PASS revoked\nEXTRA\n".encode("ascii"),
        b"x" * 100,
        f"RMCP520/1 {NONCE} PASS revoked\n".encode("ascii") + b"x",
    ],
)
def test_foreign_broken_replayed_or_oversized_ack_is_not_success(
    monkeypatch, caplog, reply,
):
    fake_transport(monkeypatch, reply)
    with caplog.at_level("WARNING", logger=sut.__name__):
        result = sut.revoke_fixed_incus_qualification_acl()
    assert result == {
        "schemaVersion": sut._SCHEMA,
        "state": "unavailable",
        "normalActivationEnabled": False,
        "reasonCode": "privileged_helper_unavailable",
    }
    assert caplog.records[0].message in {
        "incus_acl_revoke_unavailable stage=socket_unavailable",
        "incus_acl_revoke_unavailable stage=invalid_receipt",
    }
    assert "PRIVATE" not in caplog.text


@pytest.mark.parametrize("error", [OSError("PRIVATE_PATH"), TimeoutError("SECRET")])
def test_missing_socket_or_timeout_fails_closed(monkeypatch, caplog, error):
    conn = fake_transport(monkeypatch, error=error)
    with caplog.at_level("WARNING", logger=sut.__name__):
        result = sut.revoke_fixed_incus_qualification_acl()
    assert result["state"] == "unavailable"
    assert result["reasonCode"] == "privileged_helper_unavailable"
    assert conn.sent == []
    assert caplog.records[0].message == (
        "incus_acl_revoke_unavailable stage=socket_unavailable"
    )
    assert "PRIVATE_PATH" not in caplog.text
    assert "SECRET" not in caplog.text


def test_invalid_self_generated_nonce_does_not_access_socket(monkeypatch):
    monkeypatch.setattr(sut.secrets, "token_hex", lambda _n: "invalid")
    monkeypatch.setattr(
        sut.socket, "socket", lambda *_args: pytest.fail("socket attempted")
    )
    assert sut.revoke_fixed_incus_qualification_acl()["state"] == "unavailable"


def test_fragmented_ack_can_be_assembled(monkeypatch):
    conn = fake_transport(monkeypatch)
    fragments = [
        f"RMCP520/1 {NONCE} PASS ".encode("ascii"),
        b"already_restored\n",
    ]
    monkeypatch.setattr(conn, "recv", lambda _length: fragments.pop(0))
    assert sut.revoke_fixed_incus_qualification_acl()["state"] == "already_restored"


def test_transport_has_no_host_root_stat_or_privileged_helper_call():
    assert sut._SOCKET.startswith("/run/")
    assert not hasattr(sut, "_root_installation_reason")
    assert not hasattr(sut, "_root_installation_present")
    assert not hasattr(sut, "_HELPER")
    assert not hasattr(sut, "_SUDO_ARGV")
