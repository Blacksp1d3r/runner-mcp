"""Opaque epoch for the *actual* serving MCP instance.

A process-local correlation handle, NOT a signed artifact, authenticated host
identity, login credential or an update permission. Resolved independently of
a user's shell PATH and historical self-update receipts.
"""

from __future__ import annotations

import hashlib
import os
import secrets


class ServingInstanceEpoch:
    """Keep a stable epoch in one process; do not reuse it after fork.

    The caller constructs one instance per MCP server and uses it in both
    runtime-status and the serving-process observation tool. No PID, paths,
    process command line, host or private service identity leave the server.
    """

    def __init__(self) -> None:
        self._seed = secrets.token_bytes(32)

    def value(self) -> str:
        pid = os.getpid()
        if not 0 < pid < 2**64:
            raise RuntimeError("serving instance epoch unavailable")
        return hashlib.sha256(self._seed + pid.to_bytes(8, "big")).hexdigest()[:32]
