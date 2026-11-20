"""#520 — uitsluitend de vaste authenticated MCP -> HOST-root socketactie.

De MCP-server blijft zonder root, sudo en helperstat/UID-controles binnen
zijn geïsoleerde user namespace. Het root-beheerde systemd-executorproces
controleert peer, echte hostroot, helper, audit en duurzame replay-ontvangst.
Geen dynamische host, command, pad, ACL, credentials of shellargumenten.
"""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
import socket

_SOCKET = "/run/runner-mcp/incus-acl-revoke.sock"
_SCHEMA = "runner-mcp/incus-qualification-acl-revoke/v1"
_UNAVAILABLE = "privileged_helper_unavailable"
_LOG = logging.getLogger(__name__)
_VALID = frozenset({"already_restored", "revoked"})
_TOKEN = re.compile(r"[0-9a-f]{32}\Z")
_TIMEOUT = 23


def _bounded(state: str, *, reason: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "schemaVersion": _SCHEMA,
        "state": state,
        "normalActivationEnabled": False,
    }
    if reason is not None:
        result["reasonCode"] = reason
    return result


def _fail_closed(stage: str) -> dict[str, object]:
    """Schrijf alleen begrensde diagnose, zonder hostwaarden of peeroutput."""
    if stage not in {"socket_unavailable", "invalid_receipt"}:
        stage = "socket_unavailable"
    _LOG.warning("incus_acl_revoke_unavailable stage=%s", stage)
    return _bounded("unavailable", reason=_UNAVAILABLE)


def revoke_fixed_incus_qualification_acl() -> dict[str, object]:
    """Één vaste aanvraag, alleen de rootactor mag de helper aanroepen.

    De 32-hex waarde dient uitsluitend voor replay/ACK-correlatie en komt
    niet uit MCP-toolparameters. Ze verleent geen bevoegdheid op zichzelf.
    """
    nonce = secrets.token_hex(16)
    if not _TOKEN.fullmatch(nonce):
        return _fail_closed("invalid_receipt")
    request = f"RMCP520/1 {nonce}\n".encode("ascii")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(_TIMEOUT)
            conn.connect(_SOCKET)
            conn.sendall(request)
            data = bytearray()
            while len(data) <= 96 and b"\n" not in data:
                chunk = conn.recv(97 - len(data))
                if not chunk:
                    break
                data.extend(chunk)
    except (OSError, TimeoutError, ValueError):
        return _fail_closed("socket_unavailable")
    if len(data) > 96:
        return _fail_closed("invalid_receipt")
    match = re.fullmatch(
        rb"RMCP520/1 ([0-9a-f]{32}) PASS (already_restored|revoked)\n",
        bytes(data),
    )
    if match is None or match.group(1).decode("ascii") != nonce:
        return _fail_closed("invalid_receipt")
    state = match.group(2).decode("ascii")
    if state not in _VALID:
        return _fail_closed("invalid_receipt")
    _LOG.info(
        "incus_acl_revoke_ack receipt=%s",
        hashlib.sha256(nonce.encode("ascii")).hexdigest(),
    )
    return _bounded(state)
