"""Offline verificatie van een ondertekende, exacte Fabric-release-inventaris.

De bestaande vaste GitHub Release-parser valideert assetvorm en begrenzingen.
Deze module koppelt daar een Ed25519-handtekening, een *extern* vertrouwde
publieke-sleutelvingerafdruk, en een onafhankelijk vastgelegde commit/release-ID
aan. Een gebruiker of GitHub-antwoord dat zelf een sleutelvingerafdruk kiest
levert GEEN onafhankelijke autoriteit op. Dit component doet geen I/O, download,
opslag, installatie, proceswissel of rollback.

De historische vastgepinde Q7-import blijft een afzonderlijk, ongewijzigd
contract. Een toekomstige Fabric-uitgever moet het hier vereiste versiecontract
apart publiceren en de beheerde, private trust anchor leveren.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .fabric_release_assets import (
    FabricReleaseAdmissionError,
    ReleaseAdmission,
    ReleaseAsset,
    inspect_exact_release,
)

_SCHEMA = "runner-fabric/signed-release-roster/v1"
_REPOSITORY = "Blacksp1d3r/Runner-Fabric"
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX_SIGNED_DOCUMENT = 64 * 1024


class SignedFabricRosterUnqualified(ValueError):
    """Vaste veilige foutcode: nooit sleutels, ruwe data of providertekst."""


def _deny() -> None:
    raise SignedFabricRosterUnqualified("fabric_signed_release_roster_unqualified")


def _no_duplicate_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Dubbele JSON-velden blokkeren in plaats van een overschreven pin te lezen."""
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            _deny()
        result[name] = value
    return result


def verify_signed_fabric_roster(
    *,
    signed_document: bytes,
    signature: bytes,
    public_key: bytes,
    independently_trusted_key_sha256: str,
    expected_commit: str,
    expected_release_id: int,
) -> ReleaseAdmission:
    """Controleer een exact door een vertrouwde externe autoriteit gepind rooster.

    Alle parameters komen van de aanroeper; vooral `expected_commit`,
    `expected_release_id` en de sleutelvingerafdruk moeten *al buiten deze
    functie* door Fabric/het eigenaarbeleid zijn goedgekeurd. De teruggegeven
    ReleaseAdmission bevat uitsluitend gecontroleerde bron-/assetpins en geeft
    NOOIT installatie- of hostbevoegdheid. Er is geen netwerk- of schijfgebruik.
    """
    if (
        type(signed_document) is not bytes
        or not 0 < len(signed_document) <= _MAX_SIGNED_DOCUMENT
        or type(signature) is not bytes
        or len(signature) != 64
        or type(public_key) is not bytes
        or len(public_key) != 32
        or type(independently_trusted_key_sha256) is not str
        or _DIGEST.fullmatch(independently_trusted_key_sha256) is None
        or type(expected_commit) is not str
        or _COMMIT.fullmatch(expected_commit) is None
        or type(expected_release_id) is not int
        or expected_release_id <= 0
        or not hmac.compare_digest(
            hashlib.sha256(public_key).hexdigest(),
            independently_trusted_key_sha256,
        )
    ):
        _deny()

    # Verifieer de originele bytes vóór JSON-interpretatie; nooit hercoderen
    # of een van GitHub overgenomen publieke sleutel als trust anchor aannemen.
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            signature, signed_document
        )
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SignedFabricRosterUnqualified(
            "fabric_signed_release_roster_unqualified"
        ) from exc

    try:
        data = json.loads(
            signed_document.decode("utf-8"), object_pairs_hook=_no_duplicate_fields
        )
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise SignedFabricRosterUnqualified(
            "fabric_signed_release_roster_unqualified"
        ) from exc

    tag = "fabric-update-bundle-" + expected_commit
    if (
        type(data) is not dict
        or set(data) != {
            "schema_version", "repository", "commit",
            "tag", "release_id", "files",
        }
        or data["schema_version"] != _SCHEMA
        or data["repository"] != _REPOSITORY
        or data["commit"] != expected_commit
        or data["tag"] != tag
        or type(data["release_id"]) is not int
        or data["release_id"] != expected_release_id
        or type(data["files"]) is not list
        or not 5 <= len(data["files"]) <= 160
    ):
        _deny()

    assets: list[dict[str, object]] = []
    for row in data["files"]:
        if type(row) is not dict or set(row) != {
            "name", "asset_id", "bytes", "sha256",
        }:
            _deny()
        # Reconstructie uitsluitend uit exact getypeerde ondertekende velden.
        # Daarna voert de bestaande admission alle regels (grootte, unieke
        # bestanden/IDs, wheelnamen en SHA-vorm) opnieuw fail-closed uit.
        if (
            type(row["name"]) is not str
            or type(row["asset_id"]) is not int
            or type(row["bytes"]) is not int
            or type(row["sha256"]) is not str
            or _DIGEST.fullmatch(row["sha256"]) is None
        ):
            _deny()
        assets.append({
            "name": row["name"],
            "id": row["asset_id"],
            "size": row["bytes"],
            "digest": "sha256:" + row["sha256"],
        })

    synthetic_release = {
        "id": expected_release_id,
        "tag_name": tag,
        "target_commitish": expected_commit,
        "draft": False,
        "prerelease": True,
        "assets": assets,
    }
    synthetic_tag_ref = {
        "ref": "refs/tags/" + tag,
        "object": {"type": "commit", "sha": expected_commit},
    }
    try:
        return inspect_exact_release(
            expected_commit, synthetic_release, synthetic_tag_ref
        )
    except FabricReleaseAdmissionError as exc:
        raise SignedFabricRosterUnqualified(
            "fabric_signed_release_roster_unqualified"
        ) from exc


def compare_signed_fabric_roster(
    signed_pins: ReleaseAdmission,
    observed_metadata: ReleaseAdmission,
) -> dict[str, object]:
    """Vergelijk exact het ondertekende rooster met echte GitHub-metadatarijen.

    `signed_pins` moet uit `verify_signed_fabric_roster` komen; dit is
    slechts een zuivere vergelijking en géén bewijs waar de trusted key
    vandaan kwam. Retourneer alleen niet-autoriserende, veilige statusvelden.
    """
    if (
        type(signed_pins) is not ReleaseAdmission
        or type(observed_metadata) is not ReleaseAdmission
        or signed_pins.commit != observed_metadata.commit
        or signed_pins.tag != observed_metadata.tag
        or signed_pins.tag != "fabric-update-bundle-" + signed_pins.commit
        or type(signed_pins.release_id) is not int
        or signed_pins.release_id != observed_metadata.release_id
        or signed_pins.project_wheel != observed_metadata.project_wheel
        or type(signed_pins.files) is not tuple
        or type(observed_metadata.files) is not tuple
        or not 5 <= len(signed_pins.files) == len(observed_metadata.files) <= 160
    ):
        _deny()

    expected = {row.name: row for row in signed_pins.files if type(row) is ReleaseAsset}
    if len(expected) != len(signed_pins.files):
        _deny()
    seen: set[str] = set()
    for actual in observed_metadata.files:
        if type(actual) is not ReleaseAsset or type(actual.name) is not str:
            _deny()
        wanted = expected.get(actual.name)
        if (
            wanted is None
            or actual.name in seen
            or type(actual.asset_id) is not int
            or actual.asset_id != wanted.asset_id
            or type(actual.bytes) is not int
            or actual.bytes != wanted.bytes
            or type(actual.sha256) is not str
            or type(wanted.sha256) is not str
            or _DIGEST.fullmatch(actual.sha256) is None
            or _DIGEST.fullmatch(wanted.sha256) is None
            or not hmac.compare_digest(actual.sha256, wanted.sha256)
        ):
            _deny()
        seen.add(actual.name)
    if seen != set(expected):
        _deny()
    return {
        "comparison": "match_only",
        "asset_count": len(signed_pins.files),
        "operator_signer_authority_attested": False,
        "download_performed": False,
        "install_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }
