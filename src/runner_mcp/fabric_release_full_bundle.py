"""Offline-only complete Q7 bundle consistency checks against separate asset pins.

Not a signer verifier, binary wheel inspector, host importer, installer or
authorization grant. The caller must independently authenticate release pins.
"""
from __future__ import annotations

import hashlib
import hmac
import json

from .fabric_release_assets import ReleaseAdmission
from .fabric_release_independent_roster import (
    IndependentRosterMismatch,
    PinnedReleaseRoster,
    compare_exact_pinned_q7_roster,
)

_REQUIRED = frozenset({"BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py"})
_SCHEMA = "runner.fabric/control-plane-update-bundle/v1"
_MAX_TOTAL = 256 * 1024 * 1024
_MAX_FILE = 64 * 1024 * 1024
_MANIFEST_MAX = 32 * 1024
_SUMS_MAX = 128 * 1024
_COMMIT_MAX = 128
_BOOTSTRAP_MAX = 512 * 1024


class CompleteBundleMismatch(ValueError):
    """Fixed failure category; no untrusted content in exception text."""


def _deny() -> None:
    raise CompleteBundleMismatch("fabric_release_full_bundle_unqualified")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if key in parsed:
            _deny()
        parsed[key] = value
    return parsed


def _sums(data: bytes) -> dict[str, str]:
    if not 0 < len(data) <= _SUMS_MAX:
        _deny()
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError:
        _deny()
    values: dict[str, str] = {}
    for line in lines:
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            _deny()
        digest, name = fields
        if (
            len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
            or not name
            or "/" in name
            or "\\" in name
            or name in values
        ):
            _deny()
        values[name] = digest
    if not values:
        _deny()
    return values


def check_complete_q7_bundle(
    admission: ReleaseAdmission,
    independently_held: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Check all 33 pinned asset bodies and manifest relations with ZERO I/O."""
    try:
        compare_exact_pinned_q7_roster(admission, independently_held)
    except IndependentRosterMismatch:
        _deny()
    if type(asset_bodies) is not dict or len(asset_bodies) != 33:
        _deny()
    pins = {p.name: p for p in independently_held.files}
    if set(asset_bodies) != set(pins):
        _deny()
    total = 0
    for name, pin in pins.items():
        data = asset_bodies[name]
        if type(data) is not bytes or not 0 < len(data) <= _MAX_FILE:
            _deny()
        total += len(data)
        if total > _MAX_TOTAL or len(data) != pin.bytes:
            _deny()
        if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), pin.sha256):
            _deny()

    manifest_raw = asset_bodies["BUNDLE.json"]
    commit_raw = asset_bodies["COMMIT_SHA"]
    sums_raw = asset_bodies["SHA256SUMS"]
    bootstrap_raw = asset_bodies["BOOTSTRAP.py"]
    if (
        not 0 < len(manifest_raw) <= _MANIFEST_MAX
        or not 0 < len(commit_raw) <= _COMMIT_MAX
        or not 0 < len(bootstrap_raw) <= _BOOTSTRAP_MAX
    ):
        _deny()

    try:
        manifest = json.loads(
            manifest_raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys
        )
    except (UnicodeError, ValueError, RecursionError):
        _deny()
    if type(manifest) is not dict:
        _deny()
    expected_wheels = set(pins) - _REQUIRED
    project_wheel = admission.project_wheel
    if (
        manifest.get("schemaVersion") != _SCHEMA
        or manifest.get("commitSha") != admission.commit
        or manifest.get("python") != "3.12"
        or type(manifest.get("projectWheel")) is not str
        or manifest["projectWheel"] != project_wheel
        or type(manifest.get("wheelCount")) is not int
        or manifest["wheelCount"] != len(expected_wheels)
        or type(manifest.get("bootstrapSha256")) is not str
        or manifest["bootstrapSha256"] != hashlib.sha256(bootstrap_raw).hexdigest()
    ):
        _deny()
    if commit_raw not in {
        admission.commit.encode("ascii"),
        (admission.commit + "\n").encode("ascii"),
    }:
        _deny()

    summed = _sums(sums_raw)
    if set(summed) != expected_wheels | {"BOOTSTRAP.py"}:
        _deny()
    for name, digest in summed.items():
        if not hmac.compare_digest(hashlib.sha256(asset_bodies[name]).hexdigest(), digest):
            _deny()
    return {
        "inspection": "bundle_consistency_only",
        "asset_count": 33,
        "wheel_count": len(expected_wheels),
        "signed_source_verified": False,
        "wheel_metadata_verified": False,
        "local_custody_verified": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }
