from __future__ import annotations

import datetime
import json
import re
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

_MEMORY_PATTERNS = (
    re.compile(r"\bedac\b.*\b(?:ue|uncorrect(?:ed|able))\b", re.IGNORECASE),
    re.compile(r"\bmemory failure\b", re.IGNORECASE),
    re.compile(r"\buncorrect(?:ed|able)\b.*\bmemory\b", re.IGNORECASE),
    re.compile(r"\bmemory\b.*\buncorrect(?:ed|able)\b", re.IGNORECASE),
)
_HARDWARE_PATTERNS = (
    re.compile(r"\bmce(?:[:\s]|$)", re.IGNORECASE),
    re.compile(r"\bmachine check\b", re.IGNORECASE),
    re.compile(r"\bhardware error\b", re.IGNORECASE),
    re.compile(r"\bprocessor context corrupt\b", re.IGNORECASE),
)
_STORAGE_PATTERNS = (
    re.compile(r"\b(?:buffer )?i/o error\b", re.IGNORECASE),
    re.compile(r"\bblk_update_request\b", re.IGNORECASE),
    re.compile(r"\bcritical medium error\b", re.IGNORECASE),
    re.compile(
        r"\bnvme\b.*\b(?:error|failed|failure|timeout|timed out|reset(?:ting)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:ext4-fs|xfs|btrfs)\b.*\b(?:error|corrupt(?:ion)?|shutdown)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bata\d+\b.*\b(?:failed command|hard resetting link)\b", re.IGNORECASE),
)


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

    def _read_rows(self, argv: list[str]) -> tuple[dict[str, object], ...]:
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

        rows: list[dict[str, object]] = []
        for line in lines:
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HostDiagnosticError("host diagnostics unavailable") from exc
            if not isinstance(row, dict):
                raise HostDiagnosticError("host diagnostics unavailable")
            rows.append(row)
        return tuple(rows)

    @staticmethod
    def _observed_at(
        row: dict[str, object],
        *,
        until: datetime.datetime,
    ) -> datetime.datetime:
        timestamp = row.get("__REALTIME_TIMESTAMP")
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
        return observed_at

    @staticmethod
    def _classify_kernel_message(message: str) -> FatalProcessClass | None:
        # Specific memory/storage evidence is checked before generic hardware
        # wording so callers receive the most useful sanitized class.
        if any(pattern.search(message) for pattern in _MEMORY_PATTERNS):
            return FatalProcessClass.MEMORY_ERROR
        if any(pattern.search(message) for pattern in _STORAGE_PATTERNS):
            return FatalProcessClass.STORAGE_IO_OR_FILESYSTEM
        if any(pattern.search(message) for pattern in _HARDWARE_PATTERNS):
            return FatalProcessClass.HARDWARE_MACHINE_CHECK
        return None

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

        process_argv = [
            "journalctl",
            "--no-pager",
            "--output=json",
            "--output-fields=_EXE,__REALTIME_TIMESTAMP",
            "--priority=0..3",
            f"--since={since.isoformat()}",
            f"--until={until.isoformat()}",
        ]
        process_rows = self._read_rows(process_argv)

        evidence: list[FatalProcessEvidence] = []
        for row in process_rows:
            observed_at = self._observed_at(row, until=until)
            executable = row.get("_EXE")
            if executable is None:
                continue
            if not isinstance(executable, str) or not executable:
                raise HostDiagnosticError("host diagnostics unavailable")
            if executable.rsplit("/", 1)[-1] in _PYTHON_EXECUTABLES:
                evidence.append(
                    FatalProcessEvidence(
                        process_class=FatalProcessClass.PYTHON_RUNTIME,
                        observed_at=observed_at,
                    )
                )

        kernel_argv = [
            "journalctl",
            "--no-pager",
            "--output=json",
            "--output-fields=__REALTIME_TIMESTAMP,_TRANSPORT,MESSAGE",
            "--priority=0..4",
            f"--since={since.isoformat()}",
            f"--until={until.isoformat()}",
            "_TRANSPORT=kernel",
        ]
        kernel_rows = self._read_rows(kernel_argv)
        for row in kernel_rows:
            observed_at = self._observed_at(row, until=until)
            transport = row.get("_TRANSPORT")
            if transport != "kernel":
                raise HostDiagnosticError("host diagnostics unavailable")
            message = row.get("MESSAGE")
            if message is None:
                continue
            if not isinstance(message, str):
                raise HostDiagnosticError("host diagnostics unavailable")
            process_class = self._classify_kernel_message(message)
            if process_class is not None:
                evidence.append(
                    FatalProcessEvidence(
                        process_class=process_class,
                        observed_at=observed_at,
                    )
                )

        return tuple(evidence)
