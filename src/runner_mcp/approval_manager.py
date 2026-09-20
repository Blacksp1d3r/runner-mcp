from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4


class ApprovalError(RuntimeError):
    pass


APPROVAL_ID_RE = re.compile(r"^[0-9a-f]{32}$")
ALLOWED_ACTIONS = {"migration", "deploy", "code_rollback"}


def utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: Any, *, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ApprovalError(f"Approval {label} is invalid") from exc
    if parsed.tzinfo is None:
        raise ApprovalError(f"Approval {label} must include a timezone")
    return parsed.astimezone(UTC)


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class ApprovalPlan:
    approval_id: str
    action: str
    project: str
    binding_fingerprint: str
    summary: dict[str, Any]
    state: str
    created_at: datetime
    expires_at: datetime
    approved_at: datetime | None = None
    consumed_at: datetime | None = None

    def public_dict(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or utc_now()
        state = self.state
        if state in {"pending", "approved"} and current >= self.expires_at:
            state = "expired"
        return {
            "approval_id": self.approval_id,
            "action": self.action,
            "project": self.project,
            "state": state,
            "created_at": _iso(self.created_at),
            "expires_at": _iso(self.expires_at),
            "approved_at": _iso(self.approved_at),
            "consumed_at": _iso(self.consumed_at),
            "summary": self.summary,
            "single_use": True,
        }

    def persisted_dict(self) -> dict[str, Any]:
        return {
            **self.public_dict(now=self.created_at),
            "state": self.state,
            "binding_fingerprint": self.binding_fingerprint,
        }


class ApprovalManager:
    def __init__(
        self,
        *,
        root: Path,
        ttl_seconds: int = 600,
    ) -> None:
        if ttl_seconds < 60 or ttl_seconds > 1800:
            raise ApprovalError("Approval TTL must be between 60 and 1800 seconds")
        if not root.is_absolute():
            raise ApprovalError("Approval root must be absolute")
        if root.exists() and root.is_symlink():
            raise ApprovalError("Approval root must not be a symlink")
        root.mkdir(parents=True, exist_ok=True)
        os.chmod(root, 0o700)
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ApprovalError("Approval root is unavailable")
        self.ttl_seconds = ttl_seconds

    @contextmanager
    def _lock(self) -> Iterator[None]:
        path = self.root / ".approval.lock"
        if path.exists() and path.is_symlink():
            raise ApprovalError("Approval lock path is unsafe")
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
        except OSError as exc:
            raise ApprovalError("Could not acquire approval lock") from exc
        try:
            os.chmod(path, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _path(self, approval_id: str) -> Path:
        if not APPROVAL_ID_RE.fullmatch(approval_id):
            raise ApprovalError("Invalid approval identifier")
        return self.root / f"{approval_id}.json"

    def _read_locked(self, approval_id: str) -> ApprovalPlan:
        path = self._path(approval_id)
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise ApprovalError("Unknown approval")
        if (path.stat().st_mode & 0o777) != 0o600:
            raise ApprovalError("Approval file permissions are unsafe")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ApprovalError("Approval file is invalid") from exc

        if raw.get("approval_id") != approval_id:
            raise ApprovalError("Approval identity mismatch")
        action = raw.get("action")
        if action not in ALLOWED_ACTIONS:
            raise ApprovalError("Approval action is invalid")
        project = raw.get("project")
        if not isinstance(project, str) or not project:
            raise ApprovalError("Approval project is invalid")
        fingerprint = raw.get("binding_fingerprint")
        if (
            not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(char not in "0123456789abcdef" for char in fingerprint)
        ):
            raise ApprovalError("Approval binding fingerprint is invalid")
        summary = raw.get("summary")
        if not isinstance(summary, dict):
            raise ApprovalError("Approval summary is invalid")
        state = raw.get("state")
        if state not in {"pending", "approved", "consumed"}:
            raise ApprovalError("Approval state is invalid")

        approved_raw = raw.get("approved_at")
        consumed_raw = raw.get("consumed_at")
        return ApprovalPlan(
            approval_id=approval_id,
            action=action,
            project=project,
            binding_fingerprint=fingerprint,
            summary=summary,
            state=state,
            created_at=_parse_datetime(raw.get("created_at"), label="created_at"),
            expires_at=_parse_datetime(raw.get("expires_at"), label="expires_at"),
            approved_at=(
                _parse_datetime(approved_raw, label="approved_at")
                if approved_raw is not None
                else None
            ),
            consumed_at=(
                _parse_datetime(consumed_raw, label="consumed_at")
                if consumed_raw is not None
                else None
            ),
        )

    def _write_locked(self, plan: ApprovalPlan) -> None:
        path = self._path(plan.approval_id)
        if path.exists() and path.is_symlink():
            raise ApprovalError("Approval file path is unsafe")
        content = json.dumps(
            plan.persisted_dict(),
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        fd, temp_name = tempfile.mkstemp(
            prefix=".approval-",
            suffix=".tmp",
            dir=self.root,
            text=True,
        )
        temp = Path(temp_name)
        try:
            os.chmod(temp, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
                fd = -1
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
            os.chmod(path, 0o600)
        finally:
            if fd >= 0:
                os.close(fd)
            temp.unlink(missing_ok=True)

    def request(
        self,
        *,
        action: str,
        project: str,
        binding: Any,
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        if action not in ALLOWED_ACTIONS:
            raise ApprovalError("Unsupported approval action")
        if not project:
            raise ApprovalError("Approval project is required")
        if not isinstance(summary, dict):
            raise ApprovalError("Approval summary must be an object")

        now = utc_now()
        plan = ApprovalPlan(
            approval_id=uuid4().hex,
            action=action,
            project=project,
            binding_fingerprint=_fingerprint(binding),
            summary=summary,
            state="pending",
            created_at=now,
            expires_at=now + timedelta(seconds=self.ttl_seconds),
        )
        with self._lock():
            self._write_locked(plan)
        return plan.public_dict(now=now)

    def status(self, approval_id: str) -> dict[str, Any]:
        with self._lock():
            plan = self._read_locked(approval_id)
            return plan.public_dict()

    def list_recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if limit < 1 or limit > 200:
            raise ApprovalError("Approval list limit must be between 1 and 200")
        results: list[ApprovalPlan] = []
        with self._lock():
            for path in self.root.glob("*.json"):
                if path.is_symlink() or not APPROVAL_ID_RE.fullmatch(path.stem):
                    continue
                try:
                    results.append(self._read_locked(path.stem))
                except ApprovalError:
                    continue
        results.sort(key=lambda item: item.created_at, reverse=True)
        return [item.public_dict() for item in results[:limit]]

    def approve(self, approval_id: str) -> dict[str, Any]:
        with self._lock():
            plan = self._read_locked(approval_id)
            now = utc_now()
            if now >= plan.expires_at:
                raise ApprovalError("Approval has expired")
            if plan.state != "pending":
                raise ApprovalError("Approval is not pending")
            plan.state = "approved"
            plan.approved_at = now
            self._write_locked(plan)
            return plan.public_dict(now=now)

    def consume(
        self,
        approval_id: str,
        *,
        action: str,
        project: str,
        binding: Any,
    ) -> dict[str, Any]:
        with self._lock():
            plan = self._read_locked(approval_id)
            now = utc_now()
            if now >= plan.expires_at:
                raise ApprovalError("Approval has expired")
            if plan.state != "approved":
                raise ApprovalError("Approval is not approved")
            if plan.action != action or plan.project != project:
                raise ApprovalError("Approval does not match this action")
            if plan.binding_fingerprint != _fingerprint(binding):
                raise ApprovalError("Approval plan changed after approval")
            plan.state = "consumed"
            plan.consumed_at = now
            self._write_locked(plan)
            return plan.public_dict(now=now)
