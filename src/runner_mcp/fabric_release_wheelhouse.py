"""Offline ZIP, METADATA and RECORD qualification for a pinned Q7 wheelhouse.

Validates 29 independently pinned in-memory wheel assets after the existing
33-asset manifest/byte comparator. This never downloads, writes, installs,
executes package code, authenticates a pin signer or authorizes activation.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import stat
import zipfile
from email.parser import Parser

from .fabric_release_assets import ReleaseAdmission
from .fabric_release_full_bundle import check_complete_q7_bundle
from .fabric_release_independent_roster import PinnedReleaseRoster

_WHEEL_FILENAME = re.compile(
    r"(?P<name>[A-Za-z0-9_]+)-(?P<version>[A-Za-z0-9][A-Za-z0-9_.!]*)"
    r"(?:-[0-9][A-Za-z0-9_]*)?-[A-Za-z0-9_.]+-[A-Za-z0-9_.]+"
    r"-[A-Za-z0-9_.]+\\.whl\\Z"
)
_MAX_ZIP_MEMBERS = 8192
_MAX_EXPANDED_WHEEL = 128 * 1024 * 1024
_MAX_EXPANDED_TOTAL = 384 * 1024 * 1024
_MAX_METADATA_BYTES = 2 * 1024 * 1024
_CHUNK = 65536


class WheelhouseUnqualified(ValueError):
    """Fixed-denial category; never echo package bytes or paths."""


def _deny() -> None:
    raise WheelhouseUnqualified("fabric_q7_wheelhouse_unqualified")


def _canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _safe_member(name: str) -> bool:
    if not name or len(name) > 512 or name.startswith("/") or "\\" in name:
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        return False
    components = name.rstrip("/").split("/")
    return bool(components) and all(part not in ("", ".", "..") for part in components)


def _headers(raw: bytes):
    try:
        headers = Parser().parsestr(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        _deny()
    if headers.defects:
        _deny()
    return headers


def _wheel_record_check(filename: str, body: bytes) -> int:
    match = _WHEEL_FILENAME.fullmatch(filename)
    if match is None:
        _deny()
    dist_name = match.group("name")
    version = match.group("version")
    dist_info = f"{dist_name}-{version}.dist-info/"
    metadata = dist_info + "METADATA"
    wheel_file = dist_info + "WHEEL"
    record = dist_info + "RECORD"

    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            infos = archive.infolist()
            if not 3 <= len(infos) <= _MAX_ZIP_MEMBERS:
                _deny()
            seen: set[str] = set()
            hashes: dict[str, str] = {}
            sizes: dict[str, int] = {}
            headers_data: dict[str, bytes] = {}
            expanded = 0
            for info in infos:
                name = info.filename
                if not _safe_member(name) or name in seen:
                    _deny()
                seen.add(name)
                mode = (info.external_attr >> 16) & 0xFFFF
                kind = stat.S_IFMT(mode)
                if (
                    info.flag_bits & 0x1
                    or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or (info.is_dir() and kind == stat.S_IFREG)
                    or (not info.is_dir() and kind == stat.S_IFDIR)
                ):
                    _deny()
                if info.is_dir():
                    continue
                if info.file_size < 0 or info.file_size > _MAX_EXPANDED_WHEEL:
                    _deny()
                expanded += info.file_size
                if expanded > _MAX_EXPANDED_WHEEL:
                    _deny()
                if name in (metadata, wheel_file, record) and (
                    info.file_size > _MAX_METADATA_BYTES
                ):
                    _deny()
                digest = hashlib.sha256()
                size = 0
                captured = bytearray() if name in (metadata, wheel_file, record) else None
                with archive.open(info) as stream:
                    while True:
                        chunk = stream.read(_CHUNK)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > info.file_size:
                            _deny()
                        digest.update(chunk)
                        if captured is not None:
                            captured.extend(chunk)
                if size != info.file_size:
                    _deny()
                sizes[name] = size
                hashes[name] = base64.urlsafe_b64encode(digest.digest()).rstrip(
                    b"="
                ).decode("ascii")
                if captured is not None:
                    headers_data[name] = bytes(captured)

            if not {metadata, wheel_file, record}.issubset(hashes):
                _deny()
            wheel_headers = _headers(headers_data[wheel_file])
            if wheel_headers.get_all("Wheel-Version") != ["1.0"]:
                _deny()
            package_headers = _headers(headers_data[metadata])
            names = package_headers.get_all("Name")
            versions = package_headers.get_all("Version")
            if (
                names is None or len(names) != 1
                or versions != [version]
                or _canonical(names[0]) != _canonical(dist_name)
            ):
                _deny()

            try:
                rows = list(csv.reader(io.StringIO(
                    headers_data[record].decode("utf-8"), newline=""
                )))
            except (UnicodeError, csv.Error):
                _deny()
            recorded: set[str] = set()
            for row in rows:
                if len(row) != 3:
                    _deny()
                name, digest, size = row
                if name not in hashes or name in recorded:
                    _deny()
                recorded.add(name)
                if name == record:
                    if digest or size:
                        _deny()
                elif (
                    digest != "sha256=" + hashes[name]
                    or size != str(sizes[name])
                ):
                    _deny()
            if recorded != set(hashes):
                _deny()
            return expanded
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, EOFError,
            RuntimeError, UnicodeError, ValueError, OverflowError, TypeError):
        _deny()


def verify_pinned_q7_wheelhouse(
    admission: ReleaseAdmission,
    independent_pins: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Perform *content-only* qualification, after the existing exact 33/33 gate.

    The caller must independently authenticate the roster/signature and the
    original GitHub release. Passing these checks does not qualify a host.
    """
    try:
        check_complete_q7_bundle(admission, independent_pins, asset_bodies)
    except ValueError:
        _deny()
    wheel_names = sorted(name for name in asset_bodies if name.endswith(".whl"))
    if len(wheel_names) != 29:
        _deny()
    expanded = 0
    for name in wheel_names:
        expanded += _wheel_record_check(name, asset_bodies[name])
        if expanded > _MAX_EXPANDED_TOTAL:
            _deny()
    return {
        "inspection": "wheel_metadata_record_only",
        "asset_count": 33,
        "wheel_count": 29,
        "wheel_metadata_verified": True,
        "independent_signer_verified": False,
        "local_custody_verified": False,
        "host_qualified": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }
