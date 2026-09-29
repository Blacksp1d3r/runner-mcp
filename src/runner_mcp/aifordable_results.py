from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_MAX_RECORD_BYTES = 96 * 1024
_ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,127}$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,63}$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


class AIfordableResultStoreError(RuntimeError):
    """Safe local result persistence failure."""


class AIfordableTerminalAction(StrEnum):
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class AIfordableDurableResult:
    request_id: str
    fingerprint: str
    relay_version: int
    owner_generation: int
    action: AIfordableTerminalAction
    result_code: str
    result_payload: Mapping[str, object]

    def __post_init__(self) -> None:
        _identifier(self.request_id)
        if (
            not isinstance(self.fingerprint, str)
            or _FINGERPRINT_RE.fullmatch(self.fingerprint) is None
        ):
            raise AIfordableResultStoreError("result fingerprint is invalid")
        _positive_int(self.relay_version)
        _positive_int(self.owner_generation)
        if not isinstance(self.action, AIfordableTerminalAction):
            raise AIfordableResultStoreError("result action is invalid")
        if not isinstance(self.result_code, str) or _CODE_RE.fullmatch(
            self.result_code
        ) is None:
            raise AIfordableResultStoreError("result code is invalid")
        canonical = _safe_payload(self.result_payload)
        object.__setattr__(self, "result_payload", canonical)


class AIfordableResultStore:
    """Private atomic result spool for relay acknowledgement retry."""

    def __init__(self, root: Path) -> None:
        self._root = _private_root(root)
        self._lock_path = self._root / ".aifordable-results.lock"

    def put(
        self,
        result: AIfordableDurableResult,
    ) -> AIfordableDurableResult:
        if not isinstance(result, AIfordableDurableResult):
            raise TypeError("result must be AIfordableDurableResult")
        with self._locked():
            existing = self._read_optional(result.request_id)
            if existing is not None:
                if (
                    existing.fingerprint != result.fingerprint
                    or existing.action is not result.action
                    or existing.result_code != result.result_code
                    or existing.result_payload != result.result_payload
                ):
                    raise AIfordableResultStoreError(
                        "control request already has a different result"
                    )
                if (
                    result.relay_version < existing.relay_version
                    or result.owner_generation < existing.owner_generation
                ):
                    raise AIfordableResultStoreError(
                        "control result fencing moved backwards"
                    )
                if (
                    result.relay_version == existing.relay_version
                    and result.owner_generation == existing.owner_generation
                ):
                    return existing
            self._write(result)
            return result

    def get(self, request_id: str) -> AIfordableDurableResult | None:
        request_id = _identifier(request_id)
        with self._locked():
            return self._read_optional(request_id)

    def acknowledge(self, request_id: str, fingerprint: str) -> None:
        request_id = _identifier(request_id)
        if (
            not isinstance(fingerprint, str)
            or _FINGERPRINT_RE.fullmatch(fingerprint) is None
        ):
            raise AIfordableResultStoreError("result fingerprint is invalid")
        with self._locked():
            existing = self._read_optional(request_id)
            if existing is None:
                return
            if existing.fingerprint != fingerprint:
                raise AIfordableResultStoreError(
                    "control result fingerprint conflict"
                )
            try:
                self._path(request_id).unlink()
                _fsync_directory(self._root)
            except OSError as exc:
                raise AIfordableResultStoreError(
                    "cannot acknowledge control result"
                ) from exc

    def pending(self) -> tuple[AIfordableDurableResult, ...]:
        with self._locked():
            records: list[AIfordableDurableResult] = []
            try:
                entries = sorted(self._root.iterdir(), key=lambda item: item.name)
            except OSError as exc:
                raise AIfordableResultStoreError(
                    "control result store is unavailable"
                ) from exc
            for path in entries:
                if path.name == self._lock_path.name or not path.name.endswith(".json"):
                    continue
                _regular_file(path)
                records.append(self._read_path(path))
            return tuple(records)

    def _path(self, request_id: str) -> Path:
        digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
        return self._root / f"{digest}.json"

    def _read_optional(
        self,
        request_id: str,
    ) -> AIfordableDurableResult | None:
        path = self._path(request_id)
        if not path.exists():
            return None
        _regular_file(path)
        return self._read_path(path)

    def _read_path(self, path: Path) -> AIfordableDurableResult:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise AIfordableResultStoreError(
                "control result is unavailable"
            ) from exc
        if len(raw) > _MAX_RECORD_BYTES:
            raise AIfordableResultStoreError("control result is oversized")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AIfordableResultStoreError("control result is corrupt") from exc
        if not isinstance(payload, dict) or set(payload) != {
            "request_id",
            "fingerprint",
            "relay_version",
            "owner_generation",
            "action",
            "result_code",
            "result_payload",
        }:
            raise AIfordableResultStoreError("control result is invalid")
        try:
            return AIfordableDurableResult(
                request_id=payload["request_id"],
                fingerprint=payload["fingerprint"],
                relay_version=payload["relay_version"],
                owner_generation=payload["owner_generation"],
                action=AIfordableTerminalAction(payload["action"]),
                result_code=payload["result_code"],
                result_payload=payload["result_payload"],
            )
        except (TypeError, ValueError, AIfordableResultStoreError) as exc:
            raise AIfordableResultStoreError("control result is invalid") from exc

    def _write(self, result: AIfordableDurableResult) -> None:
        raw = _json_bytes(
            {
                "request_id": result.request_id,
                "fingerprint": result.fingerprint,
                "relay_version": result.relay_version,
                "owner_generation": result.owner_generation,
                "action": result.action.value,
                "result_code": result.result_code,
                "result_payload": dict(result.result_payload),
            }
        )
        if len(raw) > _MAX_RECORD_BYTES:
            raise AIfordableResultStoreError("control result is oversized")

        target = self._path(result.request_id)
        fd = -1
        temp = Path()
        try:
            fd, name = tempfile.mkstemp(
                prefix=".aifordable-result-",
                dir=self._root,
            )
            temp = Path(name)
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb", closefd=False) as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, target)
            os.chmod(target, 0o600)
            _fsync_directory(self._root)
        except OSError as exc:
            raise AIfordableResultStoreError(
                "cannot persist control result"
            ) from exc
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    @contextmanager
    def _locked(self) -> Iterator[None]:
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self._lock_path, flags, 0o600)
        except OSError as exc:
            raise AIfordableResultStoreError(
                "control result lock is unavailable"
            ) from exc
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise AIfordableResultStoreError(
                    "control result lock is unsafe"
                )
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def _safe_payload(value: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise AIfordableResultStoreError("result payload is invalid")
    payload = dict(value)
    forbidden = {
        "token",
        "secret",
        "credential",
        "password",
        "authorization",
        "private_key",
    }
    stack: list[object] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    raise AIfordableResultStoreError(
                        "result payload is invalid"
                    )
                if any(fragment in key.casefold() for fragment in forbidden):
                    raise AIfordableResultStoreError(
                        "result payload contains a forbidden field"
                    )
                stack.append(item)
        elif isinstance(current, list):
            stack.extend(current)
        elif current is not None and not isinstance(
            current,
            (str, int, float, bool),
        ):
            raise AIfordableResultStoreError("result payload is invalid")
    raw = _json_bytes(payload)
    if len(raw) > 64 * 1024:
        raise AIfordableResultStoreError("result payload is oversized")
    return json.loads(raw)


def _json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AIfordableResultStoreError(
            "control result is not JSON serializable"
        ) from exc


def _private_root(root: Path) -> Path:
    if not isinstance(root, Path) or not root.is_absolute() or root.is_symlink():
        raise AIfordableResultStoreError("control result root is invalid")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise AIfordableResultStoreError(
            "control result root is unavailable"
        ) from exc
    if not resolved.is_dir():
        raise AIfordableResultStoreError("control result root is invalid")
    return resolved


def _regular_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise AIfordableResultStoreError("control result is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise AIfordableResultStoreError("control result is unsafe")


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise AIfordableResultStoreError(
            "cannot sync control result directory"
        ) from exc


def _identifier(value: object) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise AIfordableResultStoreError("request_id is invalid")
    return value


def _positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise AIfordableResultStoreError("fencing value is invalid")
    return value
