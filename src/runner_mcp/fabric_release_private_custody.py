"""One-time owner-private custody for an independently pinned Q7 bundle.

SOURCE-ONLY / NOT AN INSTALLER. The caller must have separately approved source
pins and independent signer authority. This component verifies in-memory wheel
contents, then stores exactly 33 bounded files under ONE fixed per-user Fabric
update root. No network, token, subprocess, service, rollback or activation.
"""
from __future__ import annotations

import ctypes
import fcntl
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from .fabric_release_assets import ReleaseAdmission
from .fabric_release_independent_roster import PinnedReleaseRoster
from .fabric_release_wheelhouse import verify_pinned_q7_wheelhouse

_Q7_COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
_Q7_RELEASE_ID = 415955374
_STAGE = ".q7-bundle-inflight"
_FINAL = "bundle"
_LAB_STAGE = ".q7-lab-unsigned-inflight"
_LAB_FINAL = "lab-unsigned-bundle"
_LAB_RECEIPT = ".lab-custody-receipt.json"
_LAB_RECEIPT_SCHEMA = "runner-mcp/q7-unsigned-lab-custody/v1"
_MAX_LAB_RECEIPT = 32 * 1024
_MAX_LAB_BYTES = 256 * 1024 * 1024
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,150}\Z")


class Q7CustodyUnqualified(ValueError):
    """Constant category: no host path, asset contents or secrets included."""


def _deny() -> None:
    raise Q7CustodyUnqualified("fabric_q7_private_custody_unqualified")


def _fixed_root() -> Path:
    return Path.home() / ".local/state/runner-fabric/control-plane-update"


def _private_root_fd(root: Path) -> int:
    """Pin the existing owner-only root inode and refuse redirecting ancestors."""
    try:
        if not root.is_absolute() or ".." in root.parts:
            _deny()
        for parent in (root, *root.parents):
            if parent.is_symlink():
                _deny()
        entry = root.lstat()
        if (not stat.S_ISDIR(entry.st_mode)
                or entry.st_uid != os.geteuid()
                or stat.S_IMODE(entry.st_mode) != 0o700):
            _deny()
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        observed = os.fstat(fd)
        if (observed.st_dev, observed.st_ino) != (entry.st_dev, entry.st_ino):
            os.close(fd)
            _deny()
        return fd
    except OSError:
        _deny()


def _absent(fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=fd, follow_symlinks=False)
        return False
    except FileNotFoundError:
        return True



def _promote_noreplace(
    root_fd: int, stage_name: str = _STAGE, final_name: str = _FINAL
) -> None:
    """Atomic Linux directory promotion; never replace a racing final bundle."""
    try:
        operation = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError:
        _deny()
    operation.argtypes = (
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
        ctypes.c_uint,
    )
    operation.restype = ctypes.c_int
    if operation(root_fd, stage_name.encode("ascii"),
                 root_fd, final_name.encode("ascii"), 1) != 0:
        raise OSError(ctypes.get_errno(), "no-replace promotion denied")


def _stage_verified_bytes(
    root: Path, pins: PinnedReleaseRoster, asset_bodies: dict[str, bytes],
    *, lab: bool = False,
) -> dict[str, object]:
    """Private post-verification storage implementation; test root is injectable.

    Called ONLY after verify_pinned_q7_wheelhouse. Root must already exist with
    mode 0700; no arbitrary caller-selected destination is exposed publicly.
    """
    if type(lab) is not bool:
        _deny()
    stage_name, final_name = (_LAB_STAGE, _LAB_FINAL) if lab else (_STAGE, _FINAL)
    if (
        type(asset_bodies) is not dict
        or len(asset_bodies) != 33
        or len(pins.files) != 33
    ):
        _deny()
    names = [entry.name for entry in pins.files]
    if (len(set(names)) != 33 or set(names) != set(asset_bodies)
            or any(not _NAME.fullmatch(name) for name in names)
            or any(type(asset_bodies[name]) is not bytes for name in names)):
        _deny()
    root_fd = _private_root_fd(root)
    stage_fd = -1
    try:
        # Nonblocking lock serializes same-root cooperative importers. This
        # never deletes old custody and never treats a partial stage as ready.
        try:
            fcntl.flock(root_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            _deny()
        if not _absent(root_fd, final_name) or not _absent(root_fd, stage_name):
            _deny()
        os.mkdir(stage_name, mode=0o700, dir_fd=root_fd)
        os.fsync(root_fd)
        stage_fd = os.open(
            stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        st = os.fstat(stage_fd)
        if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
            _deny()
        digest = hashlib.sha256()
        lab_entries: list[dict[str, object]] = []
        for name in sorted(names):
            content = asset_bodies[name]
            handle = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=stage_fd,
            )
            try:
                data = memoryview(content)
                offset = 0
                while offset < len(data):
                    written = os.write(handle, data[offset:offset + 65536])
                    if written <= 0:
                        _deny()
                    offset += written
                os.fsync(handle)
                if os.fstat(handle).st_size != len(content):
                    _deny()
            finally:
                os.close(handle)
            digest.update(name.encode("ascii") + b"\0")
            digest.update(hashlib.sha256(content).digest())
            if lab:
                lab_entries.append({
                    "name": name, "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                })
        if lab:
            # Durable marker lives IN the atomically promoted unsigned leaf.
            # It proves local persistence against accidental corruption, NOT
            # trusted publisher origin or same-UID malicious rewriting.
            marker = json.dumps({
                "schema": _LAB_RECEIPT_SCHEMA,
                "commit": _Q7_COMMIT, "release_id": _Q7_RELEASE_ID,
                "publisher_authenticated": False, "files": lab_entries,
            }, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if len(marker) > _MAX_LAB_RECEIPT:
                _deny()
            receipt_fd = os.open(
                _LAB_RECEIPT,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=stage_fd,
            )
            try:
                remaining = memoryview(marker)
                while remaining:
                    written = os.write(receipt_fd, remaining)
                    if written <= 0:
                        _deny()
                    remaining = remaining[written:]
                os.fsync(receipt_fd)
            finally:
                os.close(receipt_fd)
        os.fsync(stage_fd)
        # Require the fixed destination still absent. Locking alone is not an
        # adversarial same-UID filesystem integrity guarantee, so callers must
        # preserve this private root and retain any incomplete stage for review.
        if not _absent(root_fd, final_name):
            _deny()
        if lab:
            _promote_noreplace(root_fd, _LAB_STAGE, _LAB_FINAL)
        else:
            _promote_noreplace(root_fd)
        os.fsync(root_fd)
        receipt = {
            "state": "owner_private_bytes_custodied",
            "asset_count": 33,
            "content_fingerprint": digest.hexdigest(),
            "independent_signer_verified": False,
            "host_qualified": False,
            "install_authorized": False,
            "original_client_ack": False,
        }
        if lab:
            receipt["unsigned_lab_custody"] = True
        return receipt
    except (OSError, ValueError, TypeError):
        # Do NOT clean a partial stage: preserve forensic evidence, fail closed,
        # never overwrite a preexisting prior generation or auto-retry.
        _deny()
    finally:
        if stage_fd >= 0:
            os.close(stage_fd)
        os.close(root_fd)


def _stage_pinned_q7_validated(
    admission: ReleaseAdmission,
    independent_pins: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
    *, lab: bool,
) -> dict[str, object]:
    if (
        type(admission) is not ReleaseAdmission
        or type(independent_pins) is not PinnedReleaseRoster
        or admission.commit != _Q7_COMMIT
        or independent_pins.commit != _Q7_COMMIT
        or admission.release_id != _Q7_RELEASE_ID
        or independent_pins.release_id != _Q7_RELEASE_ID
    ):
        _deny()
    verify_pinned_q7_wheelhouse(admission, independent_pins, asset_bodies)
    return _stage_verified_bytes(
        _fixed_root(), independent_pins, asset_bodies, lab=lab
    )


def stage_pinned_q7_bundle_once(
    admission: ReleaseAdmission,
    independent_pins: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Existing signed-route fixed bundle directory; never lab bytes."""
    return _stage_pinned_q7_validated(
        admission, independent_pins, asset_bodies, lab=False
    )


def stage_pinned_q7_lab_bundle_once(
    admission: ReleaseAdmission,
    independent_pins: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Explicit unsigned lab evidence: separate leaf, NEVER signed bundle."""
    return _stage_pinned_q7_validated(
        admission, independent_pins, asset_bodies, lab=True
    )



def _read_lab_private_file(directory_fd: int, name: str, max_bytes: int) -> bytes:
    """Read one private existing file through an already-pinned directory."""
    fd = -1
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory_fd)
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
            or not 0 < info.st_size <= max_bytes
        ):
            _deny()
        data = bytearray()
        while len(data) <= max_bytes:
            chunk = os.read(fd, min(65536, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) != info.st_size:
            _deny()
        return bytes(data)
    except OSError:
        _deny()
    finally:
        if fd >= 0:
            os.close(fd)


def _read_lab_digest(
    directory_fd: int, name: str, expected_size: int
) -> str:
    """Constant-memory digest of existing single-link private file."""
    fd = -1
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory_fd)
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
            or info.st_size != expected_size
        ):
            _deny()
        digest = hashlib.sha256()
        remaining = expected_size
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                _deny()
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            _deny()
        return digest.hexdigest()
    except OSError:
        _deny()
    finally:
        if fd >= 0:
            os.close(fd)


def read_q7_lab_custody_offline(
    root: Path | None = None,
) -> dict[str, object]:
    """Reopen 33 exact unsigned test files after restart; NO network/mutation.

    The optional root is internal to isolated tests. The ZIPAPP CLI always
    uses its one fixed private Black location, without path parameters.
    A matching self-held local receipt does NOT prove the publisher, the A6
    physical failure domain, an installed runtime or any agent ACK.
    """
    root_fd = -1
    bundle_fd = -1
    try:
        root_fd = _private_root_fd(_fixed_root() if root is None else root)
        bundle_fd = os.open(
            _LAB_FINAL, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        folder = os.fstat(bundle_fd)
        if (
            not stat.S_ISDIR(folder.st_mode)
            or folder.st_uid != os.geteuid()
            or stat.S_IMODE(folder.st_mode) != 0o700
        ):
            _deny()
        marker_raw = _read_lab_private_file(
            bundle_fd, _LAB_RECEIPT, _MAX_LAB_RECEIPT
        )
        def no_duplicate_keys(pairs):
            outcome = {}
            for key, value in pairs:
                if key in outcome:
                    _deny()
                outcome[key] = value
            return outcome
        data = json.loads(
            marker_raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys
        )
        if (
            type(data) is not dict
            or set(data) != {
                "schema", "commit", "release_id", "publisher_authenticated", "files"
            }
            or data["schema"] != _LAB_RECEIPT_SCHEMA
            or data["commit"] != _Q7_COMMIT
            or type(data["release_id"]) is not int
            or data["release_id"] != _Q7_RELEASE_ID
            or data["publisher_authenticated"] is not False
            or type(data["files"]) is not list
            or len(data["files"]) != 33
        ):
            _deny()
        names: set[str] = set()
        total = 0
        for entry in data["files"]:
            if type(entry) is not dict or set(entry) != {"name", "bytes", "sha256"}:
                _deny()
            name, size, fingerprint = (
                entry["name"], entry["bytes"], entry["sha256"]
            )
            if (
                type(name) is not str or _NAME.fullmatch(name) is None
                or name in names or name == _LAB_RECEIPT
                or type(size) is not int or not 0 < size <= 64 * 1024 * 1024
                or type(fingerprint) is not str or len(fingerprint) != 64
                or any(c not in "0123456789abcdef" for c in fingerprint)
            ):
                _deny()
            names.add(name)
            total += size
            if total > _MAX_LAB_BYTES:
                _deny()
        if (
            not {"BOOTSTRAP.py", "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS"}.issubset(names)
            or sum(n.endswith(".whl") for n in names) != 29
            or sum(n.startswith("runner_fabric-") and n.endswith(".whl") for n in names) != 1
            or set(os.listdir(bundle_fd)) != names | {_LAB_RECEIPT}
        ):
            _deny()
        for entry in data["files"]:
            if _read_lab_digest(bundle_fd, entry["name"], entry["bytes"]) != entry["sha256"]:
                _deny()
        return {
            "state": "q7_lab_local_readback_verified_only",
            "asset_count": 33,
            "publisher_authenticated": False,
            "independent_off_target_verified": False,
            "install_authorized": False,
            "original_client_ack": False,
        }
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        _deny()
    finally:
        if bundle_fd >= 0:
            os.close(bundle_fd)
        if root_fd >= 0:
            os.close(root_fd)
