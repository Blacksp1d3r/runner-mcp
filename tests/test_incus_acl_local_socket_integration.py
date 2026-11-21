"""#520 — echte AF_UNIX-protocolproef zonder root- of Incus-installatie.

Client en root-uitvoerder gebruiken hun ongewijzigde broncode voor het
socketverkeer. Alleen de host-root-, proces- en ACL-helpergrenzen worden
synthetisch vervangen. Dit bewijst GEEN fysieke MCP-autorisatie of rollback.
"""

from __future__ import annotations

import importlib.util
import os
import socket
import threading
from pathlib import Path

from runner_mcp import incus_acl_cleanup_transport as client


def test_real_unix_socket_client_to_root_protocol_replay(monkeypatch, tmp_path):
    """Één vaste actie en daarna een replay via echte lokale AF_UNIX-bytes."""
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts/incus_acl_socket_executor.py"
    )
    spec = importlib.util.spec_from_file_location(
        "rmcp520_socket_integration_root", source
    )
    assert spec and spec.loader
    root = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root)
    ledger = tmp_path / "ledger"
    endpoint = str(tmp_path / "s")

    calls = []
    monkeypatch.setattr(root, "_root_only", lambda: None)
    monkeypatch.setattr(root, "_binding", lambda: (1001, 1001, 108))
    monkeypatch.setattr(root, "_peer", lambda *_a: (123, "55555"))
    monkeypatch.setattr(root, "_same_peer", lambda *_a: True)
    monkeypatch.setattr(root, "_socket_generation", lambda _gid: "10:20:30")

    def helper():
        calls.append("already_restored")
        return "already_restored"

    monkeypatch.setattr(root, "_helper", helper)
    monkeypatch.setattr(client, "_SOCKET", endpoint)
    monkeypatch.setattr(client.secrets, "token_hex", lambda _n: "a" * 32)

    with ledger.open("w+b") as state:
        monkeypatch.setattr(root, "_ledger_open", lambda: os.dup(state.fileno()))
        errors = []
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(endpoint)
            listener.listen(2)
            listener.settimeout(3)

            def serve():
                try:
                    for _ in range(2):
                        conn, _ = listener.accept()
                        with conn:
                            root.execute(conn)
                except (OSError, ValueError, root.Denied) as exc:
                    errors.append(type(exc).__name__)

            worker = threading.Thread(target=serve, daemon=True)
            worker.start()
            results = [
                client.revoke_fixed_incus_qualification_acl()
                for _ in range(2)
            ]
            worker.join(timeout=4)

        assert not worker.is_alive()
        assert not errors
        assert [result["state"] for result in results] == [
            "already_restored", "already_restored",
        ]
        assert all(
            result["normalActivationEnabled"] is False for result in results
        )
        assert calls == ["already_restored"]
        state.seek(0)
        assert state.read() == (
            "a" * 32 + " PENDING\n" + "a" * 32
            + " PASS:already_restored:10:20:30\n"
        ).encode("ascii")


def test_real_af_unix_peercred_denies_wrong_owner_without_ledger_or_helper(
    monkeypatch, tmp_path,
):
    """Actual Linux SO_PEERCRED must refuse an alien service owner."""
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts/incus_acl_socket_executor.py"
    )
    spec = importlib.util.spec_from_file_location(
        "rmcp520_socket_foreign_peer_root", source
    )
    assert spec and spec.loader
    root = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root)

    endpoint = str(tmp_path / "foreign.sock")
    calls = []
    errors = []
    monkeypatch.setattr(root, "_root_only", lambda: None)
    foreign = os.getuid() + 1
    monkeypatch.setattr(root, "_binding", lambda: (foreign, foreign, 108))
    monkeypatch.setattr(
        root, "_helper", lambda: calls.append("called") or "already_restored"
    )
    monkeypatch.setattr(
        root, "_ledger_open", lambda: calls.append("ledger") or 0
    )
    monkeypatch.setattr(client, "_SOCKET", endpoint)
    monkeypatch.setattr(client.secrets, "token_hex", lambda _n: "a" * 32)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(endpoint)
        listener.listen(1)
        listener.settimeout(3)

        def serve():
            try:
                conn, _ = listener.accept()
                with conn:
                    root.execute(conn)
            except root.Denied as exc:
                errors.append(str(exc))

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        result = client.revoke_fixed_incus_qualification_acl()
        worker.join(timeout=4)

    assert not worker.is_alive()
    assert errors == ["peer_credentials"]
    assert result["state"] == "unavailable"
    assert result["reasonCode"] == "privileged_helper_unavailable"
    assert calls == []
