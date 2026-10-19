"""Bounded offline wheel-to-installed-RECORD comparison for #669.

This supplements the existing signed manifest and artifact receipt checks.
Wheel/RECORD consistency is NOT an attestation of live imported Python code.
The wheel digest pin MUST come from independent authorized trust custody.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import os
import re
import stat
import zipfile
from pathlib import Path

_SHA = re.compile(r"^[0-9a-f]{64}$")
_HASH = re.compile(r"^[A-Za-z0-9_-]{43}$")
_MAX_ENTRIES = 8192
_MAX_FILE_BYTES = 128 * 1024 * 1024
_MAX_TOTAL_BYTES = 256 * 1024 * 1024
_MAX_RECORD_BYTES = 1024 * 1024


def _unverified() -> dict[str, object]:
    return {
        "schema_version": "runner-mcp/offline-installed-record/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }


def _safe_name(value: str) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 240
        and not value.startswith("/")
        and "\\" not in value
        and "\x00" not in value
        and all(part not in ("", ".", "..") for part in value.split("/"))
    )


def _safe_file(path: Path) -> bool:
    info = path.lstat()
    return (
        stat.S_ISREG(info.st_mode)
        and info.st_nlink == 1
        and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    )


def _safe_tree(path: Path) -> bool:
    if not path.is_absolute():
        return False
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        if not stat.S_ISDIR(info.st_mode):
            return False
        if ancestor == path and (
            info.st_uid != os.geteuid()
            or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            return False
    return True


def _read_record(
    data: bytes,
    *,
    record_name: str,
    wheel_files: set[str] | None = None,
) -> dict[str, tuple[str, int]] | None:
    if not data or len(data) > _MAX_RECORD_BYTES:
        return None
    try:
        rows = csv.reader(io.StringIO(data.decode("utf-8"), newline=""))
        result: dict[str, tuple[str, int]] = {}
        for row in rows:
            if len(row) != 3:
                return None
            name, digest, size_text = row
            # pip may add executable-script entries outside site-packages to its
            # installed RECORD. They are not candidates for file reads here.
            if wheel_files is not None and name not in wheel_files:
                if (
                    not isinstance(name, str)
                    or not 1 <= len(name) <= 240
                    or "\x00" in name
                    or name.startswith("runner_mcp/")
                ):
                    return None
                continue
            if not _safe_name(name) or name in result or len(result) >= _MAX_ENTRIES:
                return None
            if name == record_name:
                if digest or size_text:
                    return None
                result[name] = ("", -1)
                continue
            if not digest.startswith("sha256=") or not _HASH.fullmatch(digest[7:]):
                return None
            raw = base64.urlsafe_b64decode(digest[7:] + "=")
            if len(raw) != 32 or not size_text.isascii() or not size_text.isdecimal():
                return None
            if len(size_text) > 1 and size_text.startswith("0"):
                return None
            size = int(size_text)
            if size > _MAX_FILE_BYTES:
                return None
            result[name] = (digest[7:], size)
        if record_name not in result:
            return None
        return result
    except (UnicodeError, ValueError, TypeError, csv.Error, base64.binascii.Error):
        return None


def _content_matches(blob: bytes, digest: str, size: int) -> bool:
    if len(blob) != size:
        return False
    original = base64.urlsafe_b64decode(digest + "=") if digest else b""
    return hashlib.sha256(blob).digest() == original


def offline_installed_record_preflight(
    wheel: Path,
    installed_package: Path,
    expected_wheel_sha256: str,
) -> dict[str, object]:
    """Compare candidate wheel RECORD and installed files, never live process state.

    This is a supplementary offline check, not a trust anchor or public MCP
    tool. The expected wheel digest must be independently authenticated.
    """
    result = _unverified()
    if (
        not isinstance(wheel, Path)
        or not isinstance(installed_package, Path)
        or not isinstance(expected_wheel_sha256, str)
        or _SHA.fullmatch(expected_wheel_sha256) is None
        or installed_package.name != "runner_mcp"
        or not wheel.is_absolute()
    ):
        return result
    try:
        if (
            not _safe_file(wheel)
            or wheel.lstat().st_size > _MAX_TOTAL_BYTES
            or not _safe_tree(installed_package.parent)
        ):
            return result
        if not _safe_tree(installed_package):
            return result
        if hashlib.sha256(wheel.read_bytes()).hexdigest() != expected_wheel_sha256:
            return result
        with zipfile.ZipFile(wheel) as archive:
            infos = archive.infolist()
            if not 2 <= len(infos) <= _MAX_ENTRIES:
                return result
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                return result
            if any(
                not _safe_name(name)
                or info.is_dir()
                or info.file_size > _MAX_FILE_BYTES
                or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
                for name, info in zip(names, infos, strict=True)
            ):
                return result
            if sum(info.file_size for info in infos) > _MAX_TOTAL_BYTES:
                return result
            records = [name for name in names if name.endswith(".dist-info/RECORD")]
            if len(records) != 1:
                return result
            record_name = records[0]
            if record_name.count("/") != 1 or record_name not in names:
                return result
            wheel_record = _read_record(archive.read(record_name), record_name=record_name)
            if wheel_record is None or set(wheel_record) != set(names):
                return result
            root = installed_package.parent
            installed_record = root / record_name
            if not _safe_file(installed_record) or installed_record.lstat().st_uid != os.geteuid():
                return result
            pip_record = _read_record(
                installed_record.read_bytes(), record_name=record_name, wheel_files=set(names)
            )
            if pip_record is None:
                return result
            for name in names:
                if name == record_name:
                    continue
                wanted = wheel_record[name]
                if pip_record.get(name) != wanted:
                    return result
                candidate = root.joinpath(*name.split("/"))
                if any(part.is_symlink() for part in (candidate, *candidate.parents)):
                    return result
                if not _safe_file(candidate) or candidate.lstat().st_size != wanted[1]:
                    return result
                content = candidate.read_bytes()
                if not _content_matches(content, wanted[0], wanted[1]):
                    return result
                if not _content_matches(archive.read(name), wanted[0], wanted[1]):
                    return result
            # Reject unaccounted source/native modules; metadata may legitimately
            # gain installer-specific entries outside the application package.
            observed: set[str] = set()
            for current, directories, files in os.walk(installed_package, followlinks=False):
                for directory in directories:
                    if (Path(current) / directory).is_symlink():
                        return result
                for name in files:
                    candidate = Path(current) / name
                    if not _safe_file(candidate):
                        return result
                    # pip may compile .pyc files after installation. They
                    # cannot be treated as serving-code proof, but do not
                    # invalidate an offline SOURCE/wheel comparison either.
                    if name.endswith((".py", ".so", ".pyd", ".dll", ".dylib")):
                        observed.add(candidate.relative_to(root).as_posix())
            declared = {
                name for name in names
                if name.startswith("runner_mcp/")
                and name.endswith((".py", ".so", ".pyd", ".dll", ".dylib"))
            }
            if observed != declared:
                return result
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeError,
        RuntimeError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ):
        return result
    return {**result, "state": "offline_installed_record_match"}
