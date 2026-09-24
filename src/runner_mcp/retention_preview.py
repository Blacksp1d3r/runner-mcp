from __future__ import annotations

import json
import os
import re
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import ProjectRegistry
from .database_manager import BACKUP_ID_RE
from .operational_safety import OperatorSafetyGuard

_RELEASE_ID_RE = re.compile(
    r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}-[0-9a-f]{6}$"
)
_RELEASE_METADATA_KEYS = {
    "release_id",
    "commit",
    "created_at",
    "previous_release",
    "environment",
    "migrations_applied",
    "pre_migration_backup_id",
}
_BACKUP_METADATA_KEYS = {
    "backup_id",
    "project",
    "kind",
    "created_at",
    "size_bytes",
    "engine",
}
_MAX_RELEASE_METADATA_BYTES = 16_384
_MAX_BACKUP_METADATA_BYTES = 8_192


class RetentionPreviewError(RuntimeError):
    pass


def _strict_directory(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    absolute = expanded if expanded.is_absolute() else Path.cwd() / expanded
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise RetentionPreviewError(f"{label} is unsafe")
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise RetentionPreviewError(f"{label} is unavailable") from exc
    if not resolved.is_dir():
        raise RetentionPreviewError(f"{label} is unavailable")
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise RetentionPreviewError(f"{label} permissions are unsafe")
    return resolved


def _strict_private_json(
    path: Path,
    *,
    label: str,
    max_bytes: int,
) -> dict[str, Any]:
    if path.is_symlink():
        raise RetentionPreviewError(f"{label} is unsafe")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise RetentionPreviewError(f"{label} is unavailable") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise RetentionPreviewError(f"{label} must be a regular file")
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise RetentionPreviewError(f"{label} permissions are unsafe")
        if before.st_size <= 0 or before.st_size > max_bytes:
            raise RetentionPreviewError(f"{label} size is unsafe")

        remaining = before.st_size
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)

        after = os.fstat(fd)
        if (
            remaining
            or after.st_size != before.st_size
            or stat.S_IMODE(after.st_mode) != 0o600
        ):
            raise RetentionPreviewError(f"{label} changed while being read")
    finally:
        os.close(fd)

    try:
        text = b"".join(chunks).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RetentionPreviewError(f"{label} must be UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RetentionPreviewError(f"{label} contains duplicate keys")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise RetentionPreviewError(f"{label} contains non-standard JSON")

    try:
        raw = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except RetentionPreviewError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RetentionPreviewError(f"{label} is invalid") from exc
    if not isinstance(raw, dict):
        raise RetentionPreviewError(f"{label} is invalid")
    return raw


def _timestamp(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise RetentionPreviewError(f"{label} timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RetentionPreviewError(f"{label} timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise RetentionPreviewError(f"{label} timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _scan_release_metadata(
    releases: Path,
    entry: Path,
) -> dict[str, Any]:
    release_id = entry.name
    if not _RELEASE_ID_RE.fullmatch(release_id):
        raise RetentionPreviewError("Release identifier is invalid")
    if (
        entry.is_symlink()
        or not entry.is_dir()
        or stat.S_IMODE(entry.stat().st_mode) != 0o700
    ):
        raise RetentionPreviewError("Release directory is unsafe")
    try:
        resolved = entry.resolve(strict=True)
        resolved.relative_to(releases)
    except (OSError, ValueError) as exc:
        raise RetentionPreviewError("Release directory is unsafe") from exc
    if resolved.parent != releases:
        raise RetentionPreviewError("Release directory is unsafe")

    raw = _strict_private_json(
        entry / ".runner-mcp-release.json",
        label="Release metadata",
        max_bytes=_MAX_RELEASE_METADATA_BYTES,
    )
    if set(raw) != _RELEASE_METADATA_KEYS:
        raise RetentionPreviewError("Release metadata has an unsupported shape")
    if raw["release_id"] != release_id:
        raise RetentionPreviewError("Release metadata identity mismatch")

    commit = raw["commit"]
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(char not in "0123456789abcdefABCDEF" for char in commit)
    ):
        raise RetentionPreviewError("Release metadata commit is invalid")
    created_at = _timestamp(raw["created_at"], label="Release metadata")
    if raw["environment"] != "staging":
        raise RetentionPreviewError("Release metadata environment is invalid")

    previous = raw["previous_release"]
    if previous is not None and (
        not isinstance(previous, str) or not _RELEASE_ID_RE.fullmatch(previous)
    ):
        raise RetentionPreviewError("Release metadata previous release is invalid")
    if previous == release_id:
        raise RetentionPreviewError("Release history contains a self reference")

    migrated = raw["migrations_applied"]
    if not isinstance(migrated, bool):
        raise RetentionPreviewError("Release metadata migration state is invalid")
    backup_id = raw["pre_migration_backup_id"]
    if backup_id is not None and (
        not isinstance(backup_id, str) or not BACKUP_ID_RE.fullmatch(backup_id)
    ):
        raise RetentionPreviewError("Release metadata backup reference is invalid")
    if migrated != (backup_id is not None):
        raise RetentionPreviewError(
            "Release migration recovery reference is inconsistent"
        )

    return {
        "release_id": release_id,
        "created_at": created_at,
        "previous_release": previous,
        "migrations_applied": migrated,
        "pre_migration_backup_id": backup_id,
    }


def _current_release_id(release_root: Path, releases: Path) -> str | None:
    current = release_root / "current"
    if not current.exists() and not current.is_symlink():
        return None
    if not current.is_symlink():
        raise RetentionPreviewError("Current release pointer is unsafe")

    target = Path(os.readlink(current))
    try:
        resolved = (
            target.resolve(strict=True)
            if target.is_absolute()
            else (release_root / target).resolve(strict=True)
        )
        resolved.relative_to(releases)
    except (OSError, ValueError) as exc:
        raise RetentionPreviewError("Current release pointer is unsafe") from exc
    if resolved.parent != releases:
        raise RetentionPreviewError("Current release pointer is unsafe")
    return resolved.name


def _scan_releases(
    release_root: Path,
) -> tuple[list[dict[str, Any]], str | None]:
    root = _strict_directory(release_root, label="Deployment release root")
    releases = _strict_directory(
        root / "releases",
        label="Deployment releases directory",
    )
    records: dict[str, dict[str, Any]] = {}
    for entry in releases.iterdir():
        item = _scan_release_metadata(releases, entry)
        if item["release_id"] in records:
            raise RetentionPreviewError("Release storage contains duplicate identities")
        records[item["release_id"]] = item

    for item in records.values():
        previous = item["previous_release"]
        if previous is not None and previous not in records:
            raise RetentionPreviewError("Release history contains a missing reference")

    for start in records:
        seen: set[str] = set()
        cursor: str | None = start
        while cursor is not None:
            if cursor in seen:
                raise RetentionPreviewError("Release history contains a cycle")
            seen.add(cursor)
            cursor = records[cursor]["previous_release"]

    current = _current_release_id(root, releases)
    if current is not None and current not in records:
        raise RetentionPreviewError("Current release metadata is unavailable")

    ordered = sorted(
        records.values(),
        key=lambda item: (item["created_at"], item["release_id"]),
        reverse=True,
    )
    return ordered, current


def _validate_backup_dump(path: Path, *, expected_size: int) -> None:
    if path.is_symlink():
        raise RetentionPreviewError("Backup dump is unsafe")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise RetentionPreviewError("Backup dump is unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RetentionPreviewError("Backup dump must be a regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise RetentionPreviewError("Backup dump permissions are unsafe")
        if info.st_size <= 0 or info.st_size != expected_size:
            raise RetentionPreviewError("Backup dump size does not match metadata")
    finally:
        os.close(fd)


def _scan_backups(
    backup_root: Path | None,
    *,
    project: str,
) -> list[dict[str, Any]]:
    if backup_root is None:
        return []
    root = _strict_directory(backup_root, label="Database backup storage")
    project_dir = root / project
    if not project_dir.exists() and not project_dir.is_symlink():
        return []
    project_dir = _strict_directory(
        project_dir,
        label="Database backup project directory",
    )

    metadata: dict[str, Path] = {}
    dumps: dict[str, Path] = {}
    for entry in project_dir.iterdir():
        if entry.is_symlink():
            raise RetentionPreviewError("Backup storage contains an unsafe entry")
        if entry.suffix == ".json" and BACKUP_ID_RE.fullmatch(entry.stem):
            metadata[entry.stem] = entry
        elif entry.suffix == ".dump" and BACKUP_ID_RE.fullmatch(entry.stem):
            dumps[entry.stem] = entry
        else:
            raise RetentionPreviewError(
                "Backup storage contains an unexpected entry"
            )
    if set(metadata) != set(dumps):
        raise RetentionPreviewError("Backup storage contains an incomplete backup pair")

    rows: list[dict[str, Any]] = []
    for backup_id in sorted(metadata, reverse=True):
        raw = _strict_private_json(
            metadata[backup_id],
            label="Backup metadata",
            max_bytes=_MAX_BACKUP_METADATA_BYTES,
        )
        if set(raw) != _BACKUP_METADATA_KEYS:
            raise RetentionPreviewError("Backup metadata has an unsupported shape")
        if raw["backup_id"] != backup_id or raw["project"] != project:
            raise RetentionPreviewError("Backup metadata identity mismatch")
        if raw["kind"] not in {"manual", "pre_migration"}:
            raise RetentionPreviewError("Backup metadata kind is invalid")
        if raw["engine"] != "postgresql":
            raise RetentionPreviewError("Backup metadata engine is invalid")
        size = raw["size_bytes"]
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise RetentionPreviewError("Backup metadata size is invalid")
        created_at = _timestamp(raw["created_at"], label="Backup metadata")
        _validate_backup_dump(dumps[backup_id], expected_size=size)
        rows.append(
            {
                "backup_id": backup_id,
                "kind": raw["kind"],
                "created_at": created_at,
            }
        )
    return rows


class RetentionPreviewPlanner:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        backup_root: Path | None,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.backup_root = backup_root

    def preview(
        self,
        project: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        config = self.registry.projects.get(project)
        if config is None:
            raise RetentionPreviewError("Unknown or disabled project")
        current_time = (now or datetime.now(UTC)).astimezone(UTC)

        releases: list[dict[str, Any]] = []
        current: str | None = None
        if config.deployment is not None:
            releases, current = _scan_releases(config.deployment.release_root)

        backups = (
            _scan_backups(self.backup_root, project=project)
            if config.database is not None
            else []
        )
        release_by_id = {item["release_id"]: item for item in releases}
        direct_target = (
            release_by_id[current]["previous_release"]
            if current is not None
            else None
        )

        policy_protected: set[str] = set()
        retained: set[str] = set()
        migration_boundaries: set[str] = set()
        for rank, item in enumerate(releases):
            release_id = item["release_id"]
            if not self.safety.retention.release_is_deletable(
                release_rank_from_newest=rank,
                deployed_at=item["created_at"],
                now=current_time,
            ):
                policy_protected.add(release_id)
            if item["pre_migration_backup_id"] is not None:
                migration_boundaries.add(release_id)

        retained.update(policy_protected)
        retained.update(migration_boundaries)
        if current is not None:
            retained.add(current)
        if direct_target is not None:
            retained.add(direct_target)

        referenced: set[str] = set()
        changed = True
        while changed:
            changed = False
            for release_id in tuple(retained):
                previous = release_by_id[release_id]["previous_release"]
                if previous is not None and previous not in retained:
                    retained.add(previous)
                    referenced.add(previous)
                    changed = True

        environment_read_only = config.environment != "staging"
        release_rows: list[dict[str, Any]] = []
        for item in releases:
            release_id = item["release_id"]
            categories: list[str] = []
            if release_id == current:
                categories.append("current")
            if release_id == direct_target:
                categories.append("rollback_target")
            if release_id in policy_protected:
                categories.append("retention_count_or_age")
            if release_id in referenced:
                categories.append("referenced_by_retained_release")
            if release_id in migration_boundaries:
                categories.append("migration_recovery_reference")
            if environment_read_only:
                categories.append("environment_read_only")
            eligible = release_id not in retained and not environment_read_only
            if eligible:
                categories.append("potentially_eligible")
            release_rows.append(
                {
                    "release_id": release_id,
                    "created_at": item["created_at"].isoformat(),
                    "categories": categories,
                    "potentially_eligible": eligible,
                }
            )

        backup_by_id = {item["backup_id"]: item for item in backups}
        retained_backup_refs: set[str] = set()
        for item in releases:
            backup_id = item["pre_migration_backup_id"]
            if backup_id is None:
                continue
            backup = backup_by_id.get(backup_id)
            if backup is None or backup["kind"] != "pre_migration":
                raise RetentionPreviewError(
                    "Release history references an unavailable recovery backup"
                )
            if item["release_id"] in retained:
                retained_backup_refs.add(backup_id)

        backup_rows: list[dict[str, Any]] = []
        for item in backups:
            categories: list[str] = []
            age_eligible = False
            if item["kind"] == "manual":
                categories.append("manual_policy_missing")
            else:
                age_eligible = (
                    self.safety.retention.pre_migration_backup_is_deletable(
                        created_at=item["created_at"],
                        now=current_time,
                    )
                )
                if not age_eligible:
                    categories.append("pre_migration_age_protected")
                if item["backup_id"] in retained_backup_refs:
                    categories.append("referenced_by_retained_release")
            if environment_read_only:
                categories.append("environment_read_only")

            eligible = (
                item["kind"] == "pre_migration"
                and age_eligible
                and item["backup_id"] not in retained_backup_refs
                and not environment_read_only
            )
            if eligible:
                categories.append("potentially_eligible")
            backup_rows.append(
                {
                    "backup_id": item["backup_id"],
                    "kind": item["kind"],
                    "created_at": item["created_at"].isoformat(),
                    "categories": categories,
                    "potentially_eligible": eligible,
                }
            )

        return {
            "project": project,
            "environment": config.environment,
            "advisory_only": True,
            "deletion_authorized": False,
            "releases": release_rows,
            "backups": backup_rows,
        }
