from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import ProjectRegistry
from .operational_safety import ActionClass, OperatorSafetyGuard
from .release_operation_lock import (
    ReleaseOperationBusy,
    ReleaseOperationLockError,
    acquire_release_operation_lock,
)
from .retention_preview import (
    RetentionPreviewError,
    RetentionPreviewPlanner,
    _strict_private_json,
)
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_PLAN_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_RELEASE_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}-[0-9a-f]{6}$")
_PLAN_VERSION = 1
_PLAN_KEYS = {
    "version",
    "plan_id",
    "project",
    "environment",
    "candidate_release",
    "current_release",
    "candidate_created_at",
    "candidate_metadata_sha256",
    "retention_policy_sha256",
    "state",
    "created_at",
    "expires_at",
}
_TRANSACTION_KEYS = {
    "version",
    "plan_id",
    "project",
    "release_id",
    "state",
    "created_at",
    "updated_at",
}
_MAX_PLAN_BYTES = 16_384
_MAX_TRANSACTION_BYTES = 8_192


class RetentionPruneError(RuntimeError):
    """Bounded local retention-pruning failure."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise RetentionPruneError(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RetentionPruneError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        raise RetentionPruneError(f"{label} is invalid")
    return parsed.astimezone(UTC)


def _private_directory(path: Path, *, create: bool, label: str) -> Path:
    if not path.is_absolute():
        raise RetentionPruneError(f"{label} is unavailable")
    if path.exists() and path.is_symlink():
        raise RetentionPruneError(f"{label} is unsafe")
    if create:
        try:
            path.mkdir(mode=0o700, parents=False, exist_ok=True)
        except OSError as exc:
            raise RetentionPruneError(f"{label} is unavailable") from exc
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise RetentionPruneError(f"{label} is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise RetentionPruneError(f"{label} is unsafe")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise RetentionPruneError(f"{label} permissions are unsafe")
    if metadata.st_uid != os.getuid():
        raise RetentionPruneError(f"{label} is unsafe")
    return path


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise RetentionPruneError("private retention state could not be synchronized") from exc
    try:
        os.fsync(fd)
    except OSError as exc:
        raise RetentionPruneError("private retention state could not be synchronized") from exc
    finally:
        os.close(fd)


def _strict_json_file(
    path: Path,
    *,
    expected_keys: set[str],
    max_bytes: int,
    label: str,
) -> dict[str, Any]:
    if path.is_symlink():
        raise RetentionPruneError(f"{label} is unsafe")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise RetentionPruneError(f"{label} is unavailable") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise RetentionPruneError(f"{label} is unsafe")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise RetentionPruneError(f"{label} permissions are unsafe")
        if metadata.st_uid != os.getuid():
            raise RetentionPruneError(f"{label} is unsafe")
        if metadata.st_size <= 0 or metadata.st_size > max_bytes:
            raise RetentionPruneError(f"{label} size is unsafe")
        remaining = metadata.st_size
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw_bytes = b"".join(chunks)
        after = os.fstat(fd)
        if remaining or after.st_size != metadata.st_size:
            raise RetentionPruneError(f"{label} changed while being read")
    finally:
        os.close(fd)

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RetentionPruneError(f"{label} contains duplicate keys")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise RetentionPruneError(f"{label} contains non-standard JSON")

    try:
        raw = json.loads(
            raw_bytes.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except RetentionPruneError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RetentionPruneError(f"{label} is invalid") from exc
    if not isinstance(raw, dict) or set(raw) != expected_keys:
        raise RetentionPruneError(f"{label} has an unsupported shape")
    return raw


def _write_private_json(path: Path, payload: dict[str, Any], *, parent: Path) -> None:
    content = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    try:
        atomic_replace_private(path, content)
    except PrivateAtomicWriteError as exc:
        raise RetentionPruneError("private retention state could not be written") from exc
    _fsync_directory(parent)


def _current_from_preview(preview: dict[str, Any]) -> str | None:
    current = [
        row["release_id"]
        for row in preview["releases"]
        if "current" in row["categories"]
    ]
    if len(current) > 1:
        raise RetentionPruneError("retention preview contains multiple current releases")
    return current[0] if current else None


def _candidate_metadata_hash(release_root: Path, release_id: str) -> str:
    if not _RELEASE_ID_RE.fullmatch(release_id):
        raise RetentionPruneError("release identifier is invalid")
    metadata_path = (
        release_root / "releases" / release_id / ".runner-mcp-release.json"
    )
    try:
        metadata = _strict_private_json(
            metadata_path,
            label="Release metadata",
            max_bytes=16_384,
        )
    except RetentionPreviewError as exc:
        raise RetentionPruneError("release metadata is unavailable or unsafe") from exc
    return _canonical_hash(metadata)


def _retention_policy_hash(safety: OperatorSafetyGuard) -> str:
    return _canonical_hash(safety.retention.model_dump(mode="json"))


def _validate_plan(raw: dict[str, Any], *, plan_id: str) -> dict[str, Any]:
    if raw["version"] != _PLAN_VERSION or raw["plan_id"] != plan_id:
        raise RetentionPruneError("prune plan identity mismatch")
    if not _PLAN_ID_RE.fullmatch(plan_id):
        raise RetentionPruneError("invalid prune plan identifier")
    if not isinstance(raw["project"], str) or not raw["project"]:
        raise RetentionPruneError("prune plan project is invalid")
    if raw["environment"] != "staging":
        raise RetentionPruneError("prune plan environment is invalid")
    if not isinstance(raw["candidate_release"], str) or not _RELEASE_ID_RE.fullmatch(
        raw["candidate_release"]
    ):
        raise RetentionPruneError("prune plan candidate is invalid")
    current = raw["current_release"]
    if current is not None and (
        not isinstance(current, str) or not _RELEASE_ID_RE.fullmatch(current)
    ):
        raise RetentionPruneError("prune plan current release is invalid")
    for key in ("candidate_metadata_sha256", "retention_policy_sha256"):
        value = raw[key]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            raise RetentionPruneError("prune plan binding is invalid")
    _parse_time(raw["candidate_created_at"], label="prune plan candidate timestamp")
    _parse_time(raw["created_at"], label="prune plan creation time")
    _parse_time(raw["expires_at"], label="prune plan expiry")
    if raw["state"] not in {"pending", "consumed"}:
        raise RetentionPruneError("prune plan state is invalid")
    return raw


class RetentionPruner:
    def __init__(
        self,
        *,
        config_dir: Path,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        backup_root: Path | None,
        ttl_seconds: int = 600,
    ) -> None:
        if ttl_seconds < 60 or ttl_seconds > 1800:
            raise RetentionPruneError("prune plan TTL must be between 60 and 1800 seconds")
        self.config_dir = _private_directory(
            config_dir,
            create=False,
            label="private configuration directory",
        )
        self.plan_root = self.config_dir / "retention-prune-plans"
        self.registry = registry
        self.safety = safety
        self.backup_root = backup_root
        self.ttl_seconds = ttl_seconds
        self.preview_planner = RetentionPreviewPlanner(
            registry=registry,
            safety=safety,
            backup_root=backup_root,
        )

    def _plan_path(self, plan_id: str) -> Path:
        if not _PLAN_ID_RE.fullmatch(plan_id):
            raise RetentionPruneError("invalid prune plan identifier")
        return self.plan_root / f"{plan_id}.json"

    def _read_plan(self, plan_id: str) -> dict[str, Any]:
        root = _private_directory(
            self.plan_root,
            create=False,
            label="retention prune plan directory",
        )
        raw = _strict_json_file(
            self._plan_path(plan_id),
            expected_keys=_PLAN_KEYS,
            max_bytes=_MAX_PLAN_BYTES,
            label="prune plan",
        )
        return _validate_plan(raw, plan_id=plan_id)

    def _write_plan(self, plan: dict[str, Any]) -> None:
        root = _private_directory(
            self.plan_root,
            create=True,
            label="retention prune plan directory",
        )
        _write_private_json(self._plan_path(plan["plan_id"]), plan, parent=root)

    def inspect_plan(self, plan_id: str) -> dict[str, Any]:
        plan = self._read_plan(plan_id)
        return {
            "plan_id": plan["plan_id"],
            "project": plan["project"],
            "candidate_release": plan["candidate_release"],
            "state": plan["state"],
            "expires_at": plan["expires_at"],
            "single_use": True,
        }

    def plan(
        self,
        project: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        config = self.registry.projects.get(project)
        if config is None or config.deployment is None:
            raise RetentionPruneError("staging deployment is not configured")
        if config.environment != "staging":
            raise RetentionPruneError("release pruning is available only for staging projects")
        status = self.safety.status()
        if not self.safety.retention_confirmed:
            raise RetentionPruneError(
                "retention policy must be confirmed before pruning can be planned"
            )
        if not status.configured:
            raise RetentionPruneError(
                "operator stop must be configured before pruning can be planned"
            )

        current_time = (now or _utc_now()).astimezone(UTC)
        preview = self.preview_planner.preview(project, now=current_time)
        eligible = [row for row in preview["releases"] if row["potentially_eligible"]]
        if not eligible:
            return {
                "planned": False,
                "project": project,
                "candidate_release": None,
                "reason": "no_eligible_release",
            }
        candidate = min(
            eligible,
            key=lambda row: (
                _parse_time(row["created_at"], label="release timestamp"),
                row["release_id"],
            ),
        )
        current_release = _current_from_preview(preview)
        plan_id = uuid4().hex
        expires = current_time + timedelta(seconds=self.ttl_seconds)
        plan = {
            "version": _PLAN_VERSION,
            "plan_id": plan_id,
            "project": project,
            "environment": "staging",
            "candidate_release": candidate["release_id"],
            "current_release": current_release,
            "candidate_created_at": candidate["created_at"],
            "candidate_metadata_sha256": _candidate_metadata_hash(
                config.deployment.release_root,
                candidate["release_id"],
            ),
            "retention_policy_sha256": _retention_policy_hash(self.safety),
            "state": "pending",
            "created_at": current_time.isoformat(),
            "expires_at": expires.isoformat(),
        }
        self._write_plan(plan)
        return {
            "planned": True,
            "plan_id": plan_id,
            "project": project,
            "candidate_release": candidate["release_id"],
            "candidate_created_at": candidate["created_at"],
            "created_at": current_time.isoformat(),
            "expires_at": expires.isoformat(),
            "single_use": True,
            "confirmation": f"PRUNE RELEASE {project} {candidate['release_id']}",
        }

    def _prepare_transaction_dirs(self, release_root: Path) -> tuple[Path, Path]:
        quarantine = _private_directory(
            release_root / ".prune-quarantine",
            create=True,
            label="release prune quarantine",
        )
        transactions = _private_directory(
            release_root / ".prune-transactions",
            create=True,
            label="release prune transaction directory",
        )
        return quarantine, transactions

    @staticmethod
    def _validate_fd_safe_delete() -> None:
        if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
            raise RetentionPruneError("safe recursive release deletion is unavailable")
        if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
            raise RetentionPruneError("safe recursive release deletion is unavailable")

    @staticmethod
    def _delete_quarantined(quarantine: Path, plan_id: str) -> None:
        RetentionPruner._validate_fd_safe_delete()
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            fd = os.open(quarantine, flags)
        except OSError as exc:
            raise RetentionPruneError("release prune quarantine is unsafe") from exc
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
                raise RetentionPruneError("release prune quarantine is unsafe")
            shutil.rmtree(plan_id, dir_fd=fd)
            os.fsync(fd)
        except RetentionPruneError:
            raise
        except OSError as exc:
            raise RetentionPruneError("quarantined release deletion failed") from exc
        finally:
            os.close(fd)

    def execute(
        self,
        project: str,
        plan_id: str,
        *,
        confirmation: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        plan = self._read_plan(plan_id)
        if plan["project"] != project:
            raise RetentionPruneError("prune plan does not match this project")
        current_time = (now or _utc_now()).astimezone(UTC)
        if plan["state"] != "pending":
            raise RetentionPruneError("prune plan is already consumed")
        if current_time >= _parse_time(plan["expires_at"], label="prune plan expiry"):
            raise RetentionPruneError("prune plan has expired")
        expected_confirmation = (
            f"PRUNE RELEASE {project} {plan['candidate_release']}"
        )
        if confirmation != expected_confirmation:
            raise RetentionPruneError("release pruning confirmation did not match")

        config = self.registry.projects.get(project)
        if config is None or config.deployment is None or config.environment != "staging":
            raise RetentionPruneError("staging deployment is not configured")
        self.safety.assert_project_action_allowed(
            ActionClass.RETENTION_PRUNE,
            environment=config.environment,
        )

        release_root = config.deployment.release_root
        try:
            release_lock = acquire_release_operation_lock(release_root)
        except ReleaseOperationBusy as exc:
            raise RetentionPruneError("release_operation_busy") from exc
        except ReleaseOperationLockError as exc:
            raise RetentionPruneError("release operation lock failed") from exc

        with release_lock:
            preview = self.preview_planner.preview(project, now=current_time)
            current_release = _current_from_preview(preview)
            if current_release != plan["current_release"]:
                raise RetentionPruneError("prune plan became stale")
            if _retention_policy_hash(self.safety) != plan["retention_policy_sha256"]:
                raise RetentionPruneError("prune plan became stale")

            candidate = next(
                (
                    row
                    for row in preview["releases"]
                    if row["release_id"] == plan["candidate_release"]
                ),
                None,
            )
            if candidate is None or not candidate["potentially_eligible"]:
                raise RetentionPruneError("prune plan became stale")
            if candidate["created_at"] != plan["candidate_created_at"]:
                raise RetentionPruneError("prune plan became stale")
            if _candidate_metadata_hash(
                release_root,
                plan["candidate_release"],
            ) != plan["candidate_metadata_sha256"]:
                raise RetentionPruneError("prune plan became stale")

            self.safety.assert_project_action_allowed(
                ActionClass.RETENTION_PRUNE,
                environment=config.environment,
            )
            self._validate_fd_safe_delete()
            quarantine, transactions = self._prepare_transaction_dirs(release_root)
            transaction_path = transactions / f"{plan_id}.json"
            if transaction_path.exists() or transaction_path.is_symlink():
                raise RetentionPruneError("prune transaction already exists")
            quarantine_target = quarantine / plan_id
            if quarantine_target.exists() or quarantine_target.is_symlink():
                raise RetentionPruneError("prune quarantine target already exists")

            consumed = dict(plan)
            consumed["state"] = "consumed"
            self._write_plan(consumed)

            transaction = {
                "version": 1,
                "plan_id": plan_id,
                "project": project,
                "release_id": plan["candidate_release"],
                "state": "quarantine_pending",
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
            }
            _write_private_json(transaction_path, transaction, parent=transactions)

            releases = release_root / "releases"
            candidate_path = releases / plan["candidate_release"]
            if (
                candidate_path.is_symlink()
                or not candidate_path.is_dir()
                or candidate_path.parent != releases
            ):
                raise RetentionPruneError("release prune candidate is unsafe")
            moved_to_quarantine = False
            try:
                os.rename(candidate_path, quarantine_target)
                moved_to_quarantine = True
                _fsync_directory(releases)
                _fsync_directory(quarantine)
                transaction["state"] = "quarantined"
                transaction["updated_at"] = _utc_now().isoformat()
                _write_private_json(
                    transaction_path,
                    transaction,
                    parent=transactions,
                )
            except (OSError, RetentionPruneError) as exc:
                if moved_to_quarantine:
                    transaction["state"] = "manual_attention_required"
                    transaction["updated_at"] = _utc_now().isoformat()
                    try:
                        _write_private_json(
                            transaction_path,
                            transaction,
                            parent=transactions,
                        )
                    except RetentionPruneError:
                        pass
                    raise RetentionPruneError(
                        "release pruning requires manual attention"
                    ) from exc
                raise RetentionPruneError("release quarantine failed") from exc

            try:
                self._delete_quarantined(quarantine, plan_id)
            except RetentionPruneError as exc:
                transaction["state"] = "manual_attention_required"
                transaction["updated_at"] = _utc_now().isoformat()
                try:
                    _write_private_json(
                        transaction_path,
                        transaction,
                        parent=transactions,
                    )
                except RetentionPruneError:
                    pass
                raise RetentionPruneError(
                    "release pruning requires manual attention"
                ) from exc

            transaction["state"] = "completed"
            transaction["updated_at"] = _utc_now().isoformat()
            _write_private_json(transaction_path, transaction, parent=transactions)
            return {
                "project": project,
                "plan_id": plan_id,
                "release_id": plan["candidate_release"],
                "state": "completed",
                "single_release": True,
                "backup_mutation_performed": False,
            }
