from __future__ import annotations

import datetime
import json
import subprocess
from collections.abc import Callable

from .host_integrity import (
    FatalProcessClass,
    FatalProcessEvidence,
    HostDiagnosticError,
)

JOURNALCTL_TIMEOUT_SECONDS = 5
JOURNALCTL_MAX_BYTES = 256 * 1024
JOURNALCTL_MAX_RECORDS = 512
_PYTHON_EXECUTABLES = frozenset({"python3", "python3.12"})


class LinuxJournalDiagnosticAdapter:
    """Fixed local systemd-journal classifier for activation gating.

    This adapter deliberately exposes no caller-controlled journal selector.
    Raw journal/process data never leaves this boundary.
    """

    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    ) -> None:
        self._runner = runner

    def recent_fatal_process_classes(
        self,
        *,
        since: datetime.datetime,
        until: datetime.datetime,
    ) -> tuple[FatalProcessEvidence, ...]:
        if (
            since.tzinfo is None
            or since.utcoffset() is None
            or until.tzinfo is None
            or until.utcoffset() is None
            or since > until
        ):
            raise HostDiagnosticError("host diagnostics unavailable")

        argv = [
            "journalctl",
            "--no-pager",
            "--output=json",
            "--output-fields=_EXE,__REALTIME_TIMESTAMP",
            "--priority=0..3",
            f"--since={since.isoformat()}",
            f"--until={until.isoformat()}",
        ]
        try:
            completed = self._runner(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=JOURNALCTL_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise HostDiagnosticError("host diagnostics unavailable") from exc

        if completed.returncode != 0:
            raise HostDiagnosticError("host diagnostics unavailable")
        stdout = completed.stdout
        if not isinstance(stdout, bytes) or len(stdout) > JOURNALCTL_MAX_BYTES:
            raise HostDiagnosticError("host diagnostics unavailable")
        try:
            text = stdout.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise HostDiagnosticError("host diagnostics unavailable") from exc

        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) > JOURNALCTL_MAX_RECORDS:
            raise HostDiagnosticError("host diagnostics unavailable")

        evidence: list[FatalProcessEvidence] = []
        for line in lines:
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HostDiagnosticError("host diagnostics unavailable") from exc
            if not isinstance(row, dict):
                raise HostDiagnosticError("host diagnostics unavailable")
            executable = row.get("_EXE")
            timestamp = row.get("__REALTIME_TIMESTAMP")
            if not isinstance(executable, str) or not executable:
                raise HostDiagnosticError("host diagnostics unavailable")
            if not isinstance(timestamp, str) or not timestamp.isascii() or not timestamp.isdigit():
                raise HostDiagnosticError("host diagnostics unavailable")
            try:
                observed_at = datetime.datetime.fromtimestamp(
                    int(timestamp) / 1_000_000,
                    tz=datetime.UTC,
                )
            except (OverflowError, OSError, ValueError) as exc:
                raise HostDiagnosticError("host diagnostics unavailable") from exc
            if observed_at > until:
                raise HostDiagnosticError("host diagnostics unavailable")
            if executable.rsplit("/", 1)[-1] in _PYTHON_EXECUTABLES:
                evidence.append(
                    FatalProcessEvidence(
                        process_class=FatalProcessClass.PYTHON_RUNTIME,
                        observed_at=observed_at,
                    )
                )
        return tuple(evidence)
