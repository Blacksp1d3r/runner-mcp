"""Offline-only complete Q7 bundle consistency checks against separate asset pins.

Not a signer verifier, binary wheel inspector, host importer, installer or
authorization grant. The caller must independently authenticate release pins.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re

from .fabric_release_assets import ReleaseAdmission, ReleaseAsset
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
_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.+\\-]{0,150}\\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\\Z")


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


def _verify_complete_contents(
    admission: ReleaseAdmission,
    asset_bodies: dict[str, bytes],
) -> int:
    """Hergebruik dezelfde byte-/manifestcontrole voor Q7 én toekomstige Fabric.

    Deze routine heeft GEEN teken-/signer-autoriteit: de aanroeper kwalificeert
    het onafhankelijke rooster vooraf. Geen netwerk, filesystem of uitvoering.
    Retourneert uitsluitend het aantal inhoudelijk overeenkomstige wheels.
    """
    if (
        type(admission) is not ReleaseAdmission
        or type(admission.files) is not tuple
        or not 5 <= len(admission.files) <= 160
        or type(admission.project_wheel) is not str
        or type(admission.commit) is not str
        or type(asset_bodies) is not dict
        or len(asset_bodies) != len(admission.files)
    ):
        _deny()

    pins: dict[str, ReleaseAsset] = {}
    ids: set[int] = set()
    total = 0
    for asset in admission.files:
        if (
            type(asset) is not ReleaseAsset
            or type(asset.name) is not str
            or _NAME.fullmatch(asset.name) is None
            or asset.name in pins
            or type(asset.asset_id) is not int
            or asset.asset_id <= 0 or asset.asset_id in ids
            or type(asset.bytes) is not int
            or not 0 < asset.bytes <= _MAX_FILE
            or type(asset.sha256) is not str
            or _SHA256.fullmatch(asset.sha256) is None
            or not (asset.name in _REQUIRED or asset.name.endswith(".whl"))
        ):
            _deny()
        pins[asset.name] = asset
        ids.add(asset.asset_id)

    if set(asset_bodies) != set(pins) or any(
        type(name) is not str for name in asset_bodies
    ):
        _deny()
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
    if (
        not _REQUIRED.issubset(pins)
        or not expected_wheels
        or any(not name.endswith(".whl") for name in expected_wheels)
        or admission.project_wheel not in expected_wheels
        or sum(name.startswith("runner_fabric-") for name in expected_wheels) != 1
        or manifest.get("schemaVersion") != _SCHEMA
        or manifest.get("commitSha") != admission.commit
        or manifest.get("python") != "3.12"
        or type(manifest.get("projectWheel")) is not str
        or manifest["projectWheel"] != admission.project_wheel
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
    return len(expected_wheels)


def check_complete_q7_bundle(
    admission: ReleaseAdmission,
    independently_held: PinnedReleaseRoster,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Behoud de historische exacte Q7-roostergrens, met gedeelde bytecontrole.

    De aparte Q7-pins blijven strikt 33/33 en historische commit/tag.
    Geen uitbreiding van de bestaande ondertekenings- of importbevoegdheid.
    """
    try:
        compare_exact_pinned_q7_roster(admission, independently_held)
    except IndependentRosterMismatch:
        _deny()
    if type(asset_bodies) is not dict or len(asset_bodies) != 33:
        _deny()
    wheels = _verify_complete_contents(admission, asset_bodies)
    return {
        "inspection": "bundle_consistency_only",
        "asset_count": 33,
        "wheel_count": wheels,
        "signed_source_verified": False,
        "wheel_metadata_verified": False,
        "local_custody_verified": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }


def check_complete_signed_fabric_bundle(
    signed_pins: ReleaseAdmission,
    observed_metadata: ReleaseAdmission,
    asset_bodies: dict[str, bytes],
) -> dict[str, object]:
    """Controleer volledig de ingeheugende exacte Fabric Release-bundel.

    Het ondertekende rooster moet vooraf met de aparte Ed25519-functie zijn
    toegelaten op een onafhankelijke door Fabric beheerde sleutel en bronpin.
    De cryptografische signatuurautoriteit wordt hier NIET afgeleid uit het
    resultaat; geen filesystem, installer, stage, rollback of service-effect.
    """
    from .fabric_release_signed_roster import (
        SignedFabricRosterUnqualified,
        compare_signed_fabric_roster,
    )

    try:
        compare_signed_fabric_roster(signed_pins, observed_metadata)
    except SignedFabricRosterUnqualified:
        _deny()
    wheel_count = _verify_complete_contents(signed_pins, asset_bodies)
    return {
        "inspection": "bundle_consistency_only",
        "asset_count": len(signed_pins.files),
        "wheel_count": wheel_count,
        "operator_signer_authority_attested": False,
        "wheel_metadata_verified": False,
        "local_custody_verified": False,
        "download_performed": False,
        "mutation_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }
