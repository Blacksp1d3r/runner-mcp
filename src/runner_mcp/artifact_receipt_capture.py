"""#669: retain original wheel-to-installed-module receipt before first activation.

This is a fixed INSTALLER-SIDE helper, NOT an MCP arbitrary file operation,
publisher trust, loaded-code proof, or update/rollback authorization.
The existing offline_artifact_receipt_preflight checks the resulting bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from pathlib import Path

from .artifact_receipt_preflight import (
    _canonical_offline_input,
    _safe_regular,
    _sha256,
    offline_artifact_receipt_preflight,
)

_REVISION = re.compile(r"^[0-9a-f]{40}$")
_MODULE_LIMIT = 4096
_TOTAL_BYTES = 100 * 1024 * 1024
_MODULE_MAX = 16 * 1024 * 1024
_RECEIPT_LIMIT = 64 * 1024
_SCHEMA = "runner-mcp/offline-artifact-receipt/v1"


class WheelReceiptCaptureError(RuntimeError):
    """Bounded local receipt failure; no private paths or source bytes."""


def capture_candidate_wheel_receipt(
    *,
    wheel: Path,
    installed_package: Path,
    receipt: Path,
    source_revision: str,
) -> dict[str, object]:
    """Record source-commit claim and actual original wheel bytes exactly once.

    Call ONLY after a separately authorized installer has an owner-private,
    retained original wheel and an installed package copied from that wheel.
    A self-provided commit string is a CLAIM until the independent authority
    connects original source, build, wheel, loaded process and issuer receipt.
    """

    unavailable = {
        "schema_version": "runner-mcp/wheel-capture-candidate/v1",
        "state": "wait",
        "reason_code": "candidate_not_captured",
        "source_revision_verified": False,
        "wheel_digest_verified_as_serving": False,
        "active_build_provenance_verified": False,
        "original_client_ack_proven": False,
        "update_authorized": False,
    }
    if (
        not isinstance(wheel, Path)
        or not isinstance(installed_package, Path)
        or not isinstance(receipt, Path)
        or not isinstance(source_revision, str)
        or _REVISION.fullmatch(source_revision) is None
        or len({str(wheel), str(installed_package), str(receipt)}) != 3
        or not all(
            _canonical_offline_input(path)
            for path in (wheel, installed_package, receipt)
        )
    ):
        raise WheelReceiptCaptureError("invalid fixed wheel receipt inputs")
    if not _safe_regular(wheel):
        raise WheelReceiptCaptureError("original wheel is unavailable or unsafe")
    try:
        info = wheel.lstat()
        root_info = receipt.parent.lstat()
        if (
            info.st_uid != os.geteuid()
            or info.st_size > _TOTAL_BYTES
            or info.st_size < 100
            or not stat.S_ISDIR(root_info.st_mode)
            or root_info.st_uid != os.geteuid()
            or stat.S_IMODE(root_info.st_mode) != 0o700
            or not installed_package.is_dir()
            or installed_package.is_symlink()
            or receipt.exists()
            or receipt.is_symlink()
        ):
            raise WheelReceiptCaptureError("original wheel receipt path is unsafe")

        modules: dict[str, str] = {}
        total = 0
        with zipfile.ZipFile(wheel, "r") as archive:
            for member in archive.infolist():
                name = member.filename
                path = Path(name)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or "\\" in name
                    or member.is_dir()
                ):
                    if member.is_dir():
                        continue
                    raise WheelReceiptCaptureError("original wheel contains unsafe paths")
                if member.external_attr >> 16 & stat.S_IFMT(0o170000) == stat.S_IFLNK:
                    raise WheelReceiptCaptureError("original wheel contains a linked file")
                if not name.startswith("runner_mcp/") or not name.endswith(".py"):
                    # Reject native code: a Python-only receipt cannot cover it.
                    if name.endswith((".so", ".pyd", ".dll", ".dylib")):
                        raise WheelReceiptCaptureError("native wheel code is not covered")
                    continue
                relative = name[len("runner_mcp/"):]
                if (
                    not relative
                    or len(relative) > 240
                    or relative in modules
                    or member.file_size > _MODULE_MAX
                    or len(modules) >= _MODULE_LIMIT
                ):
                    raise WheelReceiptCaptureError("original wheel module manifest invalid")
                total += member.file_size
                if total > _TOTAL_BYTES:
                    raise WheelReceiptCaptureError("original wheel module bytes too large")
                content = archive.read(member)
                if len(content) != member.file_size:
                    raise WheelReceiptCaptureError("original wheel module bytes incomplete")
                modules[relative] = hashlib.sha256(content).hexdigest()
        if "__init__.py" not in modules:
            raise WheelReceiptCaptureError("original wheel is not a Runner-MCP package")

        record = {
            "schema_version": _SCHEMA,
            "source_revision": source_revision,
            "wheel_sha256": _sha256(wheel),
            "modules": dict(sorted(modules.items())),
        }
        data = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        if len(data) > _RECEIPT_LIMIT:
            raise WheelReceiptCaptureError("original wheel receipt exceeds bound")

        # Never replace an earlier generation's receipt. Unsuccessful writes
        # are removed only if this call created the exclusive destination.
        fd = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if offline_artifact_receipt_preflight(
                receipt, wheel, installed_package
            )["state"] != "offline_bytes_match":
                raise WheelReceiptCaptureError("installed modules differ from original wheel")
            parent_fd = os.open(receipt.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        except BaseException:
            receipt.unlink(missing_ok=True)
            raise
        return {
            **unavailable,
            "state": "retained_original_wheel_modules_match",
            "reason_code": "offline_bytes_only_original_client_and_process_unknown",
        }
    except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise WheelReceiptCaptureError(
            "original wheel receipt capture is unavailable"
        ) from exc
