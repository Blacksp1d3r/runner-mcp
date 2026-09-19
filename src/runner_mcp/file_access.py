from __future__ import annotations

import errno
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .config import ProjectRegistry


class FileAccessError(ValueError):
    """Safe file-access error that never includes a configured project root."""


SECRET_COMPONENTS = {
    ".git",
    ".gnupg",
    ".ssh",
    "credentials",
    "secrets",
}

SECRET_FILENAMES = {
    ".git-credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
}

SECRET_SUFFIXES = {
    ".db",
    ".dump",
    ".kdbx",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}

SAFE_ENV_EXAMPLES = {
    ".env.example",
    ".env.sample",
    ".env.template",
}

PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
)

SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]{20,}"),
)

ASSIGNMENT_SECRET_RE = re.compile(
    r"(?im)([\"']?\b(?:password|passwd|token|secret|api[_-]?key)\b[\"']?"
    r"\s*[:=]\s*)"
    r"([\"']?)([A-Za-z0-9_./+=:@-]{12,})(?:\2)"
    r"(?=\s*(?:[,}]|#.*)?$)"
)


@dataclass(frozen=True)
class FileAccessPolicy:
    max_file_bytes: int = 1_048_576
    max_read_lines: int = 500
    max_list_entries: int = 200
    max_directory_entries: int = 10_000


class FileAccessService:
    def __init__(
        self,
        registry: ProjectRegistry,
        policy: FileAccessPolicy | None = None,
    ) -> None:
        self.registry = registry
        self.policy = policy or FileAccessPolicy()

    def _project_root(self, project: str) -> Path:
        config = self.registry.projects.get(project)
        if config is None:
            raise FileAccessError("Unknown or disabled project")

        try:
            root = config.root.resolve(strict=True)
        except OSError as exc:
            raise FileAccessError("Project root is unavailable") from exc

        if not root.is_dir():
            raise FileAccessError("Project root is unavailable")
        return root

    @staticmethod
    def _relative_parts(path: str, *, allow_empty: bool = False) -> tuple[str, ...]:
        if "\x00" in path:
            raise FileAccessError("Path contains an invalid character")
        if "\\" in path:
            raise FileAccessError("Backslashes are not accepted in project paths")

        pure = PurePosixPath(path)
        if pure.is_absolute():
            raise FileAccessError("Absolute paths are not allowed")

        parts = pure.parts
        if any(part in {"..", "."} for part in parts):
            raise FileAccessError("Path traversal is not allowed")
        if not parts and not allow_empty:
            raise FileAccessError("A project-relative path is required")
        return parts

    @staticmethod
    def _is_secret_name(parts: tuple[str, ...]) -> bool:
        lowered = tuple(part.lower() for part in parts)
        if any(part in SECRET_COMPONENTS for part in lowered):
            return True

        if not lowered:
            return False

        name = lowered[-1]
        if name in SECRET_FILENAMES:
            return True
        if name == ".env" or (name.startswith(".env.") and name not in SAFE_ENV_EXAMPLES):
            return True
        return any(name.endswith(suffix) for suffix in SECRET_SUFFIXES)

    def _resolve(
        self,
        project: str,
        path: str,
        *,
        allow_empty: bool = False,
    ) -> tuple[Path, PurePosixPath]:
        root = self._project_root(project)
        parts = self._relative_parts(path, allow_empty=allow_empty)

        if self._is_secret_name(parts):
            raise FileAccessError("Access to this path is blocked by policy")

        current = root
        for part in parts:
            current = current / part
            try:
                if current.is_symlink():
                    raise FileAccessError("Symlinks are not allowed")
            except OSError as exc:
                raise FileAccessError("Path is unavailable") from exc

        try:
            resolved = current.resolve(strict=True)
        except FileNotFoundError as exc:
            raise FileAccessError("Path was not found") from exc
        except OSError as exc:
            raise FileAccessError("Path is unavailable") from exc

        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise FileAccessError("Path escapes the configured project root") from exc

        relative = PurePosixPath(*parts)
        return resolved, relative

    @staticmethod
    def _redact_known_secrets(text: str) -> str:
        redacted = text
        for pattern in SECRET_PATTERNS:
            if pattern.pattern.startswith("(?i)(Bearer"):
                redacted = pattern.sub(r"\1[REDACTED]", redacted)
            else:
                redacted = pattern.sub("[REDACTED]", redacted)

        def replace_assignment(match: re.Match[str]) -> str:
            return f"{match.group(1)}[REDACTED]"

        return ASSIGNMENT_SECRET_RE.sub(replace_assignment, redacted)

    def _read_bytes(self, resolved: Path) -> bytes:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        try:
            fd = os.open(resolved, flags)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise FileAccessError("Symlinks are not allowed") from exc
            raise FileAccessError("File could not be opened") from exc

        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise FileAccessError("Path is not a regular file")
            if metadata.st_size > self.policy.max_file_bytes:
                raise FileAccessError("File exceeds the configured read-size limit")

            with os.fdopen(fd, "rb", closefd=True) as handle:
                fd = -1
                data = handle.read(self.policy.max_file_bytes + 1)
        finally:
            if fd >= 0:
                os.close(fd)

        if len(data) > self.policy.max_file_bytes:
            raise FileAccessError("File exceeds the configured read-size limit")
        if b"\x00" in data:
            raise FileAccessError("Binary files are not readable through this tool")
        if any(marker in data for marker in PRIVATE_KEY_MARKERS):
            raise FileAccessError("File content is blocked by secret policy")
        return data

    def read_file(
        self,
        project: str,
        path: str,
        *,
        offset: int = 0,
        length: int = 200,
    ) -> dict[str, Any]:
        if offset < 0:
            raise FileAccessError("Offset must be zero or greater")
        if not 1 <= length <= self.policy.max_read_lines:
            raise FileAccessError(
                f"Length must be between 1 and {self.policy.max_read_lines}"
            )

        resolved, relative = self._resolve(project, path)
        data = self._read_bytes(resolved)

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FileAccessError("Only UTF-8 text files are readable") from exc

        text = self._redact_known_secrets(text)
        lines = text.splitlines(keepends=True)
        selected = lines[offset : offset + length]
        next_offset = offset + len(selected)
        eof = next_offset >= len(lines)

        return {
            "path": relative.as_posix(),
            "offset": offset,
            "next_offset": None if eof else next_offset,
            "eof": eof,
            "line_count": len(selected),
            "content": "".join(selected),
        }

    def file_metadata(self, project: str, path: str) -> dict[str, Any]:
        resolved, relative = self._resolve(project, path)
        try:
            metadata = resolved.lstat()
        except OSError as exc:
            raise FileAccessError("Path is unavailable") from exc

        if stat.S_ISLNK(metadata.st_mode):
            raise FileAccessError("Symlinks are not allowed")
        if stat.S_ISREG(metadata.st_mode):
            kind = "file"
        elif stat.S_ISDIR(metadata.st_mode):
            kind = "directory"
        else:
            raise FileAccessError("Unsupported file type")

        result: dict[str, Any] = {
            "path": relative.as_posix(),
            "type": kind,
        }
        if kind == "file":
            result["size_bytes"] = metadata.st_size
            result["within_read_limit"] = metadata.st_size <= self.policy.max_file_bytes
        return result

    def list_files(
        self,
        project: str,
        path: str = "",
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        if offset < 0:
            raise FileAccessError("Offset must be zero or greater")
        if not 1 <= limit <= self.policy.max_list_entries:
            raise FileAccessError(
                f"Limit must be between 1 and {self.policy.max_list_entries}"
            )

        resolved, relative = self._resolve(project, path, allow_empty=True)
        if not resolved.is_dir():
            raise FileAccessError("Path is not a directory")

        try:
            entries = list(os.scandir(resolved))
        except OSError as exc:
            raise FileAccessError("Directory could not be read") from exc

        if len(entries) > self.policy.max_directory_entries:
            raise FileAccessError("Directory exceeds the configured entry limit")

        visible: list[dict[str, Any]] = []
        for entry in sorted(entries, key=lambda item: item.name.casefold()):
            child_parts = (*relative.parts, entry.name)
            if self._is_secret_name(child_parts):
                continue
            if entry.is_symlink():
                continue

            try:
                if entry.is_dir(follow_symlinks=False):
                    kind = "directory"
                elif entry.is_file(follow_symlinks=False):
                    kind = "file"
                else:
                    continue
            except OSError:
                continue

            child_relative = PurePosixPath(*child_parts).as_posix()
            item: dict[str, Any] = {
                "name": entry.name,
                "path": child_relative,
                "type": kind,
            }
            if kind == "file":
                try:
                    item["size_bytes"] = entry.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
            visible.append(item)

        selected = visible[offset : offset + limit]
        next_offset = offset + len(selected)
        eof = next_offset >= len(visible)

        return {
            "path": relative.as_posix(),
            "offset": offset,
            "next_offset": None if eof else next_offset,
            "eof": eof,
            "entries": selected,
        }
