"""Private, fail-closed quarantine evidence for poisoned mailbox recovery.

This module intentionally does not alter GitHub watcher cursor or dispatch.
The owner must qualify the integration separately before activation.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from .bridge_protocol import REQUEST_ID_RE

MAX_QUARANTINE_FILE_BYTES = 262_144
DEFAULT_QUARANTINE_ENTRIES = 512
DEFAULT_FAILURE_BUDGET = 3
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION = 1


class RecoveryQuarantineError(RuntimeError):
    """Public-safe failure category without raw storage or payload details."""


class RecoveryFailureKind(StrEnum):
    INVALID_REQUEST = "invalid-request"
    AMBIGUOUS_CLAIM = "ambiguous-claim"
    RESULT_MISSING = "result-missing"
    TRANSPORT_UNAVAILABLE = "transport-unavailable"
    PERSISTENCE_FAILURE = "persistence-failure"


class RecoveryQuarantineState(StrEnum):
    RETRY = "retry"
    OPERATOR_REQUIRED = "operator-required"


@dataclass(frozen=True, slots=True)
class RecoveryQuarantineRecord:
    request_id: str
    fingerprint: str
    reason: RecoveryFailureKind
    attempts: int
    state: RecoveryQuarantineState


def _valid_request_id(value: object) -> bool:
    return isinstance(value, str) and REQUEST_ID_RE.fullmatch(value) is not None


def _valid_fingerprint(value: object) -> bool:
    return isinstance(value, str) and _FINGERPRINT_RE.fullmatch(value) is not None


class RecoveryQuarantineLedger:
    """Bounded private file ledger. Never automatically permits retry after quarantine.

    The caller must supply an already computed digest over trusted, bounded
    canonical recovery identity/evidence, not a raw exception or provider message.
    """

    def __init__(
        self,
        path: Path,
        *,
        max_records: int = DEFAULT_QUARANTINE_ENTRIES,
        failure_budget: int = DEFAULT_FAILURE_BUDGET,
    ) -> None:
        if type(max_records) is not int or not 1 <= max_records <= 4096:
            raise RecoveryQuarantineError("quarantine entry limit is invalid")
        if type(failure_budget) is not int or not 1 <= failure_budget <= 16:
            raise RecoveryQuarantineError("quarantine retry budget is invalid")
        if not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts:
            raise RecoveryQuarantineError("quarantine storage path is invalid")
        self._path = path
        self._max_records = max_records
        self._failure_budget = failure_budget

    def inspect(self, request_id: str) -> RecoveryQuarantineRecord | None:
        self._check_request_id(request_id)
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
                return self._read(handle).get(request_id)
        except OSError as exc:
            raise RecoveryQuarantineError("quarantine inspection unavailable") from exc

    def record_failure(
        self,
        *,
        request_id: str,
        fingerprint: str,
        reason: RecoveryFailureKind,
    ) -> RecoveryQuarantineRecord:
        self._check_request_id(request_id)
        self._check_fingerprint(fingerprint)
        if not isinstance(reason, RecoveryFailureKind):
            raise RecoveryQuarantineError("quarantine reason is not allow-listed")
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                records = self._read(handle)
                existing = records.get(request_id)
                if existing is not None and existing.fingerprint != fingerprint:
                    raise RecoveryQuarantineError("recovery identity changed; operator required")
                if existing is not None and existing.reason != reason:
                    raise RecoveryQuarantineError("recovery reason changed; operator required")
                if existing is not None and existing.state == RecoveryQuarantineState.OPERATOR_REQUIRED:
                    return existing
                if existing is None and len(records) >= self._max_records:
                    raise RecoveryQuarantineError("quarantine capacity exhausted")
                attempts = 1 if existing is None else existing.attempts + 1
                state = (
                    RecoveryQuarantineState.OPERATOR_REQUIRED
                    if attempts >= self._failure_budget
                    else RecoveryQuarantineState.RETRY
                )
                record = RecoveryQuarantineRecord(request_id, fingerprint, reason, attempts, state)
                records[request_id] = record
                self._write(handle, records)
                return record
        except OSError as exc:
            raise RecoveryQuarantineError("quarantine failure record unavailable") from exc

    def rearm(
        self,
        *,
        request_id: str,
        expected_fingerprint: str,
        operator_approved: bool,
    ) -> RecoveryQuarantineRecord:
        """Data-layer gate only; caller must separately enforce operator authorization."""
        self._check_request_id(request_id)
        self._check_fingerprint(expected_fingerprint)
        if operator_approved is not True:
            raise RecoveryQuarantineError("explicit operator approval is required")
        fd = self._open()
        try:
            with os.fdopen(fd, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                records = self._read(handle)
                existing = records.get(request_id)
                if existing is None or existing.fingerprint != expected_fingerprint:
                    raise RecoveryQuarantineError("quarantine rearm identity mismatch")
                if existing.state != RecoveryQuarantineState.OPERATOR_REQUIRED:
                    raise RecoveryQuarantineError("quarantine rearm requires terminal record")
                restored = RecoveryQuarantineRecord(
                    request_id, expected_fingerprint, existing.reason, 0,
                    RecoveryQuarantineState.RETRY,
                )
                records[request_id] = restored
                self._write(handle, records)
                return restored
        except OSError as exc:
            raise RecoveryQuarantineError("quarantine rearm unavaila    def _open(self) -> int:
        """Open the stable lock inode, never the replaceable data-file inode."""
        parent = self._path.parent
        try:
            info = parent.lstat()
            if parent.resolve(strict=True) != parent or (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or info.st_uid != os.getuid()
                or (info.st_mode & 0o077)
            ):
                raise RecoveryQuarantineError("quarantine directory is unsafe")
            lock_path = parent / (self._path.name + ".lock")
            if lock_path.is_symlink():
                raise RecoveryQuarantineError("quarantine lock is unsafe")
            nofollow = getattr(os, "O_NOFOLLOW", 0)
            if nofollow == 0:
                raise RecoveryQuarantineError("quarantine symlink protection unavailable")
            fd = os.open(
                lock_path, os.O_RDWR | os.O_CREAT | nofollow | getattr(os, "O_CLOEXEC", 0),
                0o600,
            )
            metadata = os.fstat(fd)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or (metadata.st_mode & 0o077)
            ):
                os.close(fd)
                raise RecoveryQuarantineError("quarantine lock permissions are unsafe")
            return fd
        except OSError as exc:
            raise RecoveryQuarantineError("quarantine storage unavailable") from exc

    def _read(self, _lock_handle) -> dict[str, RecoveryQuarantineRecord]:
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        if nofollow == 0:
            raise RecoveryQuarantineError("quarantine symlink protection unavailable")
        if self._path.is_symlink():
            raise RecoveryQuarantineError("quarantine file is unsafe")
        try:
            fd = os.open(self._path, os.O_RDONLY | nofollow)
        except FileNotFoundError:
            return {}
        except OSError as exc:
            raise RecoveryQuarantineError("quarantine data is unavailable") from exc
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or (opened.st_mode & 0o077)
        ):
            os.close(fd)
            raise RecoveryQuarantineError("quarantine file permissions are unsafe")
        try:
            with os.fdopen(fd, "r", encoding="utf-8", closefd=True) as handle:
                raw = handle.read(MAX_QUARANTINE_FILE_BYTES + 1)
        except UnicodeError as exc:
            raise RecoveryQuarantineError("quarantine data is invalid") from exc
        if len(raw.encode("utf-8")) > MAX_QUARANTINE_FILE_BYTES:
            raise RecoveryQuarantineError("quarantine data exceeds bound")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise RecoveryQuarantineError("quarantine data is invalid") from exc
        if not isinstance(data, dict) or set(data) != {"schemaVersion", "records"}:
            raise RecoveryQuarantineError("quarantine schema is invalid")
        if type(data["schemaVersion"]) is not int or data["schemaVersion"] != _SCHEMA_VERSION:
            raise RecoveryQuarantineError("quarantine schema version is invalid")
        rows = data["records"]
        if not isinstance(rows, dict) or len(rows) > self._max_records:
            raise RecoveryQuarantineError("quarantine record count is invalid")
        records = {}
        for request_id, row in rows.items():
            if not _valid_request_id(request_id) or not isinstance(row, dict):
                raise RecoveryQuarantineError("quarantine record identity is invalid")
            if set(row) != {"request_id", "fingerprint", "reason", "attempts", "state"}:
                raise RecoveryQuarantineError("quarantine record schema is invalid")
            if row["request_id"] != request_id or not _valid_fingerprint(row["fingerprint"]):
                raise RecoveryQuarantineError("quarantine fingerprint is invalid")
            try:
                reason = RecoveryFailureKind(row["reason"])
                state = RecoveryQuarantineState(row["state"])
            except (ValueError, TypeError) as exc:
                raise RecoveryQuarantineError("quarantine category is invalid") from exc
            attempts = row["attempts"]
            if type(attempts) is not int or not 0 <= attempts <= self._failure_budget:
                raise RecoveryQuarantineError("quarantine retry count is invalid")
            if (attempts >= self._failure_budget) != (
                state == RecoveryQuarantineState.OPERATOR_REQUIRED
            ):
                raise RecoveryQuarantineError("quarantine state is inconsistent")
            records[request_id] = RecoveryQuarantineRecord(
                request_id, row["fingerprint"], reason, attempts, state
            )
        return records

    def _write(self, _lock_handle, records: dict[str, RecoveryQuarantineRecord]) -> None:
        """Fsync private temp file, replace atomically, then fsync directory.

        This method always executes while holding the stable separate .lock.
        """
        encoded = json.dumps(
            {
                "schemaVersion": _SCHEMA_VERSION,
                "records": {key: asdict(record) for key, record in sorted(records.items())},
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded) > MAX_QUARANTINE_FILE_BYTES:
            raise RecoveryQuarantineError("quarantine data exceeds bound")
        if self._path.is_symlink():
            raise RecoveryQuarantineError("quarantine file is unsafe")
        parent = self._path.parent
        fd, temporary = tempfile.mkstemp(prefix=".quarantine-", dir=parent)
        try:
            try:
                view = memoryview(encoded)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise RecoveryQuarantineError("quarantine write unavailable")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(temporary, self._path)
            dir_fd = os.open(
                parent, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

ndle.fileno())

    @staticmethod
    def _check_request_id(value: str) -> None:
        if not _valid_request_id(value):
            raise RecoveryQuarantineError("quarantine request identity is invalid")

    @staticmethod
    def _check_fingerprint(value: str) -> None:
        if not _valid_fingerprint(value):
            raise RecoveryQuarantineError("quarantine fingerprint is invalid")
