from __future__ import annotations

import codecs
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import DatabaseConfig, MigrationConfig, ProjectRegistry
from .operational_safety import ActionClass, OperatorSafetyGuard


class DatabaseManagerError(RuntimeError):
    pass


BACKUP_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")
MAX_BACKUP_METADATA_BYTES = 8_192
RESTORE_PREFLIGHT_TIMEOUT_SECONDS = 60
SAFE_ENV = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PGCONNECT_TIMEOUT": "10",
}
GENERIC_SECRET_RE = re.compile(
    r"(?im)(\b(?:password|passwd|token|secret|api[_-]?key)\b\s*[:=]\s*)([^\s,;]{8,})"
)


@dataclass(frozen=True)
class CommandResult:
    exit_code: int | None
    timed_out: bool
    truncated: bool
    output: str


def utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12]


def _known_executable(names: tuple[str, ...]) -> Path:
    for directory in (Path("/usr/bin"), Path("/bin"), Path("/usr/local/bin")):
        for name in names:
            candidate = directory / name
            if (
                candidate.exists()
                and candidate.is_file()
                and not candidate.is_symlink()
                and os.access(candidate, os.X_OK)
            ):
                return candidate
    raise DatabaseManagerError(f"Required executable is unavailable: {names[0]}")


def _path_without_symlinks(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    absolute = expanded if expanded.is_absolute() else Path.cwd() / expanded
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise DatabaseManagerError(f"{label} must not contain symlinks")
    try:
        return absolute.resolve(strict=True)
    except OSError as exc:
        raise DatabaseManagerError(f"{label} is unavailable") from exc


class DatabaseManager:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        safety: OperatorSafetyGuard,
        backup_root: Path | None,
        secret_values: dict[str, str] | Any,
        pg_dump_path: Path | None = None,
        pg_restore_path: Path | None = None,
        prepare_storage: bool = True,
        poll_interval_seconds: float = 0.1,
        terminate_grace_seconds: float = 2.0,
    ) -> None:
        self.registry = registry
        self.safety = safety
        self.secret_values = secret_values
        self.pg_dump_path = pg_dump_path
        self.pg_restore_path = pg_restore_path
        self.poll_interval_seconds = poll_interval_seconds
        self.terminate_grace_seconds = terminate_grace_seconds
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

        self.backup_root: Path | None = None
        if backup_root is not None:
            if not backup_root.is_absolute():
                raise DatabaseManagerError("Database backup root must be absolute")
            if backup_root.exists() and backup_root.is_symlink():
                raise DatabaseManagerError("Database backup root must not be a symlink")
            if prepare_storage:
                backup_root.mkdir(parents=True, exist_ok=True)
                os.chmod(backup_root, 0o700)
            elif not backup_root.exists() or not backup_root.is_dir():
                raise DatabaseManagerError("Database backup storage is unavailable")
            self.backup_root = backup_root.resolve(strict=True)
            if stat.S_IMODE(self.backup_root.stat().st_mode) != 0o700:
                raise DatabaseManagerError("Database backup root must use mode 0700")

            home = self.backup_root / ".runtime-home"
            if prepare_storage:
                if home.exists() and home.is_symlink():
                    raise DatabaseManagerError("Database runtime home must not be a symlink")
                home.mkdir(mode=0o700, exist_ok=True)
                os.chmod(home, 0o700)

    def _lock_for(self, project: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._locks.get(project)
            if lock is None:
                lock = threading.Lock()
                self._locks[project] = lock
            return lock

    def _database(self, project: str) -> tuple[Path, DatabaseConfig]:
        config = self.registry.projects.get(project)
        if config is None:
            raise DatabaseManagerError("Unknown or disabled project")
        if config.database is None:
            raise DatabaseManagerError("Project database is not configured")

        try:
            root = config.root.resolve(strict=True)
        except OSError as exc:
            raise DatabaseManagerError("Project root is unavailable") from exc
        if not root.is_dir():
            raise DatabaseManagerError("Project root is unavailable")
        return root, config.database

    def _dsn(self, database: DatabaseConfig) -> str:
        value = self.secret_values.get(database.dsn_env)
        if not isinstance(value, str) or not value:
            raise DatabaseManagerError("Database credential is unavailable")
        if len(value) > 32768 or "\x00" in value or "\n" in value or "\r" in value:
            raise DatabaseManagerError("Database credential has an invalid format")
        return value

    def _backup_project_dir(self, project: str) -> Path:
        if self.backup_root is None:
            raise DatabaseManagerError("Database backup storage is not configured")
        path = self.backup_root / project
        if path.exists() and path.is_symlink():
            raise DatabaseManagerError("Database backup project directory is unsafe")
        path.mkdir(mode=0o700, exist_ok=True)
        os.chmod(path, 0o700)
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(self.backup_root)
        except ValueError as exc:
            raise DatabaseManagerError("Database backup path escaped the configured root") from exc
        return resolved

    def _pg_dump(self) -> Path:
        if self.pg_dump_path is None:
            self.pg_dump_path = _known_executable(("pg_dump",))
        path = _path_without_symlinks(self.pg_dump_path, label="pg_dump")
        if not path.is_file() or not os.access(path, os.X_OK):
            raise DatabaseManagerError("pg_dump is unavailable")
        return path

    def _pg_restore(self) -> Path:
        if self.pg_restore_path is None:
            self.pg_restore_path = _known_executable(("pg_restore",))
        path = _path_without_symlinks(self.pg_restore_path, label="pg_restore")
        if not path.is_file() or not os.access(path, os.X_OK):
            raise DatabaseManagerError("pg_restore is unavailable")
        return path

    def _base_env(self) -> dict[str, str]:
        env = dict(SAFE_ENV)
        if self.backup_root is not None:
            env["HOME"] = str(self.backup_root / ".runtime-home")
            env["TMPDIR"] = str(self.backup_root)
        return env

    @staticmethod
    def _public_backup_metadata(raw: dict[str, Any], *, available: bool) -> dict[str, Any]:
        return {
            "backup_id": raw["backup_id"],
            "project": raw["project"],
            "kind": raw["kind"],
            "created_at": raw["created_at"],
            "size_bytes": raw["size_bytes"],
            "engine": raw["engine"],
            "available": available,
        }

    def _write_metadata(self, path: Path, payload: dict[str, Any]) -> None:
        temp = path.with_suffix(".json.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(temp, flags, 0o600)
        except OSError as exc:
            raise DatabaseManagerError("Could not create backup metadata") from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as handle:
                fd = -1
                json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
            os.chmod(path, 0o600)
        finally:
            if fd >= 0:
                os.close(fd)
            temp.unlink(missing_ok=True)

    def _backup_database_locked(
        self,
        project: str,
        *,
        kind: str,
    ) -> dict[str, Any]:
        if kind not in {"manual", "pre_migration"}:
            raise DatabaseManagerError("Unsupported backup kind")

        _, database = self._database(project)
        dsn = self._dsn(database)
        project_dir = self._backup_project_dir(project)
        backup_id = _timestamp_id()
        dump_path = project_dir / f"{backup_id}.dump"
        metadata_path = project_dir / f"{backup_id}.json"

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(dump_path, flags, 0o600)
        except OSError as exc:
            raise DatabaseManagerError("Could not create backup file") from exc

        env = self._base_env()
        env["PGDATABASE"] = dsn
        try:
            with os.fdopen(fd, "wb", closefd=True) as handle:
                fd = -1
                try:
                    completed = subprocess.run(
                        [
                            str(self._pg_dump()),
                            "--format=custom",
                            "--no-owner",
                            "--no-privileges",
                            "--no-password",
                        ],
                        stdin=subprocess.DEVNULL,
                        stdout=handle,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        timeout=600,
                        shell=False,
                        env=env,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise DatabaseManagerError("Database backup command failed") from exc
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            dump_path.unlink(missing_ok=True)
            raise
        finally:
            if fd >= 0:
                os.close(fd)

        if completed.returncode != 0:
            dump_path.unlink(missing_ok=True)
            raise DatabaseManagerError("Database backup command failed")

        os.chmod(dump_path, 0o600)
        size = dump_path.stat().st_size
        if size <= 0:
            dump_path.unlink(missing_ok=True)
            raise DatabaseManagerError("Database backup is empty")

        payload = {
            "backup_id": backup_id,
            "project": project,
            "kind": kind,
            "created_at": utc_now().isoformat(),
            "size_bytes": size,
            "engine": database.engine,
        }
        self._write_metadata(metadata_path, payload)
        return self._public_backup_metadata(payload, available=True)

    def backup_database(self, project: str) -> dict[str, Any]:
        project_config = self.registry.projects.get(project)
        if project_config is None:
            raise DatabaseManagerError("Unknown or disabled project")
        self.safety.assert_project_action_allowed(
            ActionClass.BACKUP,
            environment=project_config.environment,
        )
        lock = self._lock_for(project)
        if not lock.acquire(blocking=False):
            raise DatabaseManagerError("Another database operation is already in progress")
        try:
            self.safety.assert_project_action_allowed(
                ActionClass.BACKUP,
                environment=project_config.environment,
            )
            return self._backup_database_locked(project, kind="manual")
        finally:
            lock.release()

    def list_backups(
        self,
        project: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise DatabaseManagerError("Backup list limit must be between 1 and 500")
        self._database(project)
        if self.backup_root is None:
            return []

        project_dir = self.backup_root / project
        if not project_dir.exists():
            return []
        if project_dir.is_symlink() or not project_dir.is_dir():
            raise DatabaseManagerError("Database backup project directory is unsafe")

        results: list[dict[str, Any]] = []
        for path in sorted(project_dir.glob("*.json"), reverse=True):
            backup_id = path.stem
            if not BACKUP_ID_RE.fullmatch(backup_id) or path.is_symlink():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if (
                    raw.get("backup_id") != backup_id
                    or raw.get("project") != project
                    or raw.get("kind") not in {"manual", "pre_migration"}
                    or raw.get("engine") != "postgresql"
                    or not isinstance(raw.get("size_bytes"), int)
                ):
                    continue
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue

            dump_path = project_dir / f"{backup_id}.dump"
            available = (
                dump_path.exists()
                and dump_path.is_file()
                and not dump_path.is_symlink()
                and stat.S_IMODE(dump_path.stat().st_mode) == 0o600
            )
            results.append(self._public_backup_metadata(raw, available=available))
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _strict_backup_metadata(text: str) -> dict[str, Any]:
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise DatabaseManagerError("Backup metadata contains duplicate keys")
                result[key] = value
            return result

        def reject_constant(_value: str) -> None:
            raise DatabaseManagerError("Backup metadata contains non-standard JSON")

        try:
            raw = json.loads(
                text,
                object_pairs_hook=reject_duplicates,
                parse_constant=reject_constant,
            )
        except DatabaseManagerError:
            raise
        except (json.JSONDecodeError, TypeError) as exc:
            raise DatabaseManagerError("Backup metadata is invalid") from exc
        if not isinstance(raw, dict):
            raise DatabaseManagerError("Backup metadata is invalid")
        return raw

    @staticmethod
    def _read_private_file(path: Path, *, max_bytes: int | None = None) -> bytes:
        if path.is_symlink():
            raise DatabaseManagerError("Backup file path is unsafe")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise DatabaseManagerError("Backup file is unavailable") from exc
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise DatabaseManagerError("Backup file must be a regular file")
            if stat.S_IMODE(metadata.st_mode) != 0o600:
                raise DatabaseManagerError("Backup file permissions are unsafe")
            if max_bytes is not None and metadata.st_size > max_bytes:
                raise DatabaseManagerError("Backup metadata exceeds size limit")
            chunks: list[bytes] = []
            remaining = metadata.st_size
            while remaining > 0:
                chunk = os.read(fd, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)

    @staticmethod
    def _hash_private_backup_dump(path: Path, *, expected_size: int) -> str:
        if path.is_symlink():
            raise DatabaseManagerError("Backup file path is unsafe")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise DatabaseManagerError("Backup file is unavailable") from exc
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise DatabaseManagerError("Backup file must be a regular file")
            if stat.S_IMODE(metadata.st_mode) != 0o600:
                raise DatabaseManagerError("Backup file permissions are unsafe")
            if metadata.st_size <= 0 or metadata.st_size != expected_size:
                raise DatabaseManagerError("Backup dump size does not match metadata")
            digest = hashlib.sha256()
            total = 0
            while True:
                chunk = os.read(fd, 1_048_576)
                if not chunk:
                    break
                digest.update(chunk)
                total += len(chunk)
            if total != expected_size:
                raise DatabaseManagerError("Backup dump size changed during preflight")
            return digest.hexdigest()
        finally:
            os.close(fd)

    def _restore_project_dir(self, project: str) -> Path:
        if self.backup_root is None:
            raise DatabaseManagerError("Database backup storage is not configured")
        if (
            self.backup_root.is_symlink()
            or not self.backup_root.is_dir()
            or stat.S_IMODE(self.backup_root.stat().st_mode) != 0o700
        ):
            raise DatabaseManagerError("Database backup storage is unsafe")
        project_dir = self.backup_root / project
        if project_dir.is_symlink() or not project_dir.is_dir():
            raise DatabaseManagerError("Database backup project directory is unavailable")
        try:
            resolved = project_dir.resolve(strict=True)
            resolved.relative_to(self.backup_root)
        except (OSError, ValueError) as exc:
            raise DatabaseManagerError("Database backup project directory is unsafe") from exc
        if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
            raise DatabaseManagerError("Database backup project directory permissions are unsafe")
        return resolved

    def _restore_preflight_locked(
        self,
        project: str,
        backup_id: str,
    ) -> tuple[dict[str, Any], str]:
        config = self.registry.projects.get(project)
        if config is None:
            raise DatabaseManagerError("Unknown or disabled project")
        _, database = self._database(project)
        if database.engine != "postgresql":
            raise DatabaseManagerError("Only PostgreSQL restore preflight is supported")
        if self.backup_root is None:
            raise DatabaseManagerError("Database backup storage is not configured")
        if not BACKUP_ID_RE.fullmatch(backup_id):
            raise DatabaseManagerError("Invalid backup identifier")
        if config.environment != "staging":
            return (
                {
                    "project": project,
                    "backup_id": backup_id,
                    "eligible": False,
                    "preflight_state": "ineligible_environment",
                },
                "",
            )

        project_dir = self._restore_project_dir(project)
        metadata_path = project_dir / f"{backup_id}.json"
        dump_path = project_dir / f"{backup_id}.dump"
        metadata_bytes = self._read_private_file(
            metadata_path,
            max_bytes=MAX_BACKUP_METADATA_BYTES,
        )
        try:
            metadata_text = metadata_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DatabaseManagerError("Backup metadata must be UTF-8") from exc
        raw = self._strict_backup_metadata(metadata_text)
        if set(raw) != {
            "backup_id",
            "project",
            "kind",
            "created_at",
            "size_bytes",
            "engine",
        }:
            raise DatabaseManagerError("Backup metadata has an unsupported shape")
        if raw["backup_id"] != backup_id or raw["project"] != project:
            raise DatabaseManagerError("Backup metadata identity mismatch")
        if raw["kind"] not in {"manual", "pre_migration"}:
            raise DatabaseManagerError("Backup metadata kind is invalid")
        if raw["engine"] != "postgresql":
            raise DatabaseManagerError("Backup metadata engine is invalid")
        if (
            not isinstance(raw["size_bytes"], int)
            or isinstance(raw["size_bytes"], bool)
            or raw["size_bytes"] <= 0
        ):
            raise DatabaseManagerError("Backup metadata size is invalid")
        if not isinstance(raw["created_at"], str):
            raise DatabaseManagerError("Backup metadata timestamp is invalid")
        try:
            created_at = datetime.fromisoformat(raw["created_at"])
        except ValueError as exc:
            raise DatabaseManagerError("Backup metadata timestamp is invalid") from exc
        if created_at.tzinfo is None:
            raise DatabaseManagerError("Backup metadata timestamp must include a timezone")

        archive_sha256 = self._hash_private_backup_dump(
            dump_path,
            expected_size=raw["size_bytes"],
        )
        binding_payload = (
            f"runner-mcp-restore-preflight:v1:{project}:{backup_id}:"
            f"{raw['size_bytes']}:{archive_sha256}"
        ).encode("utf-8")
        binding_fingerprint = hashlib.sha256(binding_payload).hexdigest()

        executable = self._pg_restore()
        try:
            completed = subprocess.run(
                [str(executable), "--list", str(dump_path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=RESTORE_PREFLIGHT_TIMEOUT_SECONDS,
                shell=False,
                env=dict(SAFE_ENV),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DatabaseManagerError("Database restore preflight command failed") from exc
        if completed.returncode != 0:
            raise DatabaseManagerError("Database restore preflight archive is invalid")

        return (
            {
                "project": project,
                "backup_id": backup_id,
                "kind": raw["kind"],
                "created_at": created_at.astimezone(UTC).isoformat(),
                "size_bytes": raw["size_bytes"],
                "engine": "postgresql",
                "available": True,
                "eligible": True,
                "preflight_state": "eligible",
            },
            binding_fingerprint,
        )

    def restore_preflight(self, project: str, backup_id: str) -> dict[str, Any]:
        if not BACKUP_ID_RE.fullmatch(backup_id):
            raise DatabaseManagerError("Invalid backup identifier")
        lock = self._lock_for(project)
        if not lock.acquire(blocking=False):
            raise DatabaseManagerError("Another database operation is already in progress")
        try:
            public, _binding_fingerprint = self._restore_preflight_locked(
                project,
                backup_id,
            )
            return public
        finally:
            lock.release()

    def _safe_cwd(self, root: Path, relative: str) -> Path:
        current = root
        for part in Path(relative).parts:
            if part in {"", "."}:
                continue
            current = current / part
            if current.is_symlink():
                raise DatabaseManagerError("Migration working directory must not contain symlinks")
        try:
            resolved = current.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise DatabaseManagerError("Migration working directory is unavailable") from exc
        if not resolved.is_dir():
            raise DatabaseManagerError("Migration working directory is unavailable")
        return resolved

    def _migration_executable(self, argv: list[str]) -> Path:
        executable = _path_without_symlinks(Path(argv[0]), label="Migration executable")
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise DatabaseManagerError("Migration executable is unavailable")
        return executable

    def _terminate_group(self, process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=self.terminate_grace_seconds)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=self.terminate_grace_seconds)
        except subprocess.TimeoutExpired:
            pass

    @staticmethod
    def _scrub_output(
        text: str,
        *,
        dsn: str,
        private_paths: list[str],
    ) -> str:
        result = text.replace(dsn, "[REDACTED]")
        for value in sorted((item for item in private_paths if item), key=len, reverse=True):
            result = result.replace(value, "[PRIVATE_PATH]")
        return GENERIC_SECRET_RE.sub(r"\1[REDACTED]", result)

    def _run_migration_command(
        self,
        *,
        root: Path,
        database: DatabaseConfig,
        profile: MigrationConfig,
        argv: list[str],
    ) -> CommandResult:
        dsn = self._dsn(database)
        executable = self._migration_executable(argv)
        cwd = self._safe_cwd(root, profile.cwd)

        env = self._base_env()
        if profile.dsn_target_env is not None:
            env[profile.dsn_target_env] = dsn

        process: subprocess.Popen[bytes] | None = None
        selector: selectors.BaseSelector | None = None
        captured = bytearray()
        truncated = False
        capture_limit = profile.max_output_bytes + len(dsn.encode("utf-8")) + 4096
        timed_out = False
        started = time.monotonic()

        try:
            process = subprocess.Popen(
                [str(executable), *argv[1:]],
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                start_new_session=True,
                close_fds=True,
            )
            if process.stdout is None:
                raise DatabaseManagerError("Migration output pipe is unavailable")

            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)

            while True:
                for key, _ in selector.select(timeout=self.poll_interval_seconds):
                    try:
                        chunk = os.read(key.fileobj.fileno(), 4096)
                    except OSError:
                        chunk = b""
                    if not chunk:
                        try:
                            selector.unregister(key.fileobj)
                        except KeyError:
                            pass
                        continue

                    remaining = capture_limit - len(captured)
                    if remaining > 0:
                        captured.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated = True

                if process.poll() is None and (
                    time.monotonic() - started >= profile.timeout_seconds
                ):
                    timed_out = True
                    self._terminate_group(process)

                if process.poll() is not None and not selector.get_map():
                    break

            exit_code = process.wait()
        except OSError as exc:
            if process is not None and process.poll() is None:
                self._terminate_group(process)
            raise DatabaseManagerError("Migration command failed") from exc
        finally:
            if selector is not None:
                selector.close()

        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        output = decoder.decode(bytes(captured), final=True)
        output = self._scrub_output(
            output,
            dsn=dsn,
            private_paths=[
                str(root),
                str(cwd),
                str(executable),
                str(executable.parent),
                str(self.backup_root) if self.backup_root else "",
            ],
        )
        encoded_output = output.encode("utf-8", errors="replace")
        if len(encoded_output) > profile.max_output_bytes:
            output = encoded_output[: profile.max_output_bytes].decode(
                "utf-8",
                errors="ignore",
            )
            truncated = True
        if truncated:
            output += "\n[OUTPUT TRUNCATED BY RUNNER MCP]\n"

        return CommandResult(
            exit_code=exit_code,
            timed_out=timed_out,
            truncated=truncated,
            output=output,
        )

    def migration_status(self, project: str) -> dict[str, Any]:
        root, database = self._database(project)
        profile = database.migrations
        if profile is None:
            raise DatabaseManagerError("Migration profile is not configured")

        result = self._run_migration_command(
            root=root,
            database=database,
            profile=profile,
            argv=profile.status_argv,
        )
        return {
            "project": project,
            "status": (
                "timed_out"
                if result.timed_out
                else "ok"
                if result.exit_code == 0
                else "failed"
            ),
            "exit_code": result.exit_code,
            "output": result.output,
            "output_truncated": result.truncated,
        }

    def apply_migrations(self, project: str) -> dict[str, Any]:
        project_config = self.registry.projects.get(project)
        if project_config is None:
            raise DatabaseManagerError("Unknown or disabled project")
        self.safety.assert_project_action_allowed(
            ActionClass.MIGRATION,
            environment=project_config.environment,
        )
        lock = self._lock_for(project)
        if not lock.acquire(blocking=False):
            raise DatabaseManagerError("Another database operation is already in progress")
        try:
            root, database = self._database(project)
            profile = database.migrations
            if profile is None:
                raise DatabaseManagerError("Migration profile is not configured")

            self.safety.assert_project_action_allowed(
                ActionClass.MIGRATION,
                environment=project_config.environment,
            )
            backup = self._backup_database_locked(project, kind="pre_migration")

            # A stop may have been activated while the backup was running.
            self.safety.assert_project_action_allowed(
                ActionClass.MIGRATION,
                environment=project_config.environment,
            )
            result = self._run_migration_command(
                root=root,
                database=database,
                profile=profile,
                argv=profile.apply_argv,
            )

            return {
                "project": project,
                "status": (
                    "timed_out"
                    if result.timed_out
                    else "applied"
                    if result.exit_code == 0
                    else "failed"
                ),
                "exit_code": result.exit_code,
                "pre_migration_backup": backup,
                "output": result.output,
                "output_truncated": result.truncated,
                "database_restore_performed": False,
            }
        finally:
            lock.release()
