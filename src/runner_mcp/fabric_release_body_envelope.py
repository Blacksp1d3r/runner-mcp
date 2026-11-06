"""F30: controleer de eigenaarsondertekende Fabric-releasebeschrijving.

De GitHub Release-beschrijving is een ONVERTROUWDE transportdrager.
De publieke sleutel uit dit tekstblok wordt nooit zelfstandig vertrouwd:
een onafhankelijke eigenaar/Fabric-policy moet commit, Release-ID én de
publieke-sleutelvingerafdruk vooraf als vaste pins leveren.

Deze private bronmodule hergebruikt het bestaande Ed25519-v1-rooster en de
exacte getypeerde GitHub ReleaseAdmission. Geen GET, opslag, installatie,
launcherwissel, server-tool, service of rollback.
"""
from __future__ import annotations

import base64
import binascii

from .fabric_release_assets import ReleaseAdmission
from .fabric_release_signed_roster import (
    SignedFabricRosterUnqualified,
    compare_signed_fabric_roster,
    verify_signed_fabric_roster,
)

_BEGIN = "\n\n-----BEGIN RUNNER-FABRIC SIGNED-RELEASE-ROSTER V1-----\n"
_END = "-----END RUNNER-FABRIC SIGNED-RELEASE-ROSTER V1-----\n"
_LABELS = ("document=", "signature=", "public_key=")
_MAX_BODY = 100 * 1024
_MAX_NOTES = 8 * 1024
_MAX_DOCUMENT = 64 * 1024


class SignedBodyEnvelopeUnqualified(ValueError):
    """Eén vaste foutcode; nooit ruwe GitHub-tekst of credentialinhoud."""


def _deny() -> None:
    raise SignedBodyEnvelopeUnqualified("fabric_signed_release_body_unqualified")


def _canonical_decode(value: str, *, cap: int) -> bytes:
    """Geen alternatieve Base64-spelling, witruimte of extra padding toestaan."""
    if type(value) is not str or len(value) > ((cap + 2) // 3) * 4:
        _deny()
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, ValueError, binascii.Error):
        _deny()
    if not 0 < len(raw) <= cap or base64.b64encode(raw).decode("ascii") != value:
        _deny()
    return raw


def verify_signed_release_body(
    *,
    body: str,
    independently_trusted_key_sha256: str,
    expected_commit: str,
    expected_release_id: int,
    observed_metadata: ReleaseAdmission,
) -> tuple[bytes, bytes, bytes]:
    """Parseer en verifieer een exact, als laatste toegevoegd tekstblok.

    Let op: alle drie de onafhankelijke pins moeten al door eigenaar/Fabric
    zijn vastgelegd. Een `public_key` regel in GitHub is enkel bewijsmateriaal,
    geen bron van vertrouwen of installatiemacht.
    """
    if type(body) is not str or type(observed_metadata) is not ReleaseAdmission:
        _deny()
    try:
        body_bytes = body.encode("utf-8")
    except (UnicodeError, ValueError):
        _deny()
    if (
        not 0 < len(body_bytes) <= _MAX_BODY
        or body.count(_BEGIN) != 1
        or body.count(_END) != 1
        or not body.endswith(_END)
    ):
        _deny()

    notes, payload = body.split(_BEGIN)
    if (
        len(notes.encode("utf-8")) > _MAX_NOTES
        or notes.endswith("\n")
        or "\r" in notes
        or "\x00" in notes
        or "-----BEGIN RUNNER-FABRIC SIGNED-RELEASE-ROSTER" in notes
        or "-----END RUNNER-FABRIC SIGNED-RELEASE-ROSTER" in notes
    ):
        _deny()
    encoded = payload[: -len(_END)]
    lines = encoded.splitlines(keepends=True)
    if len(lines) != 3:
        _deny()

    decoded: list[bytes] = []
    for index, label in enumerate(_LABELS):
        line = lines[index]
        if not line.startswith(label) or not line.endswith("\n"):
            _deny()
        limit = _MAX_DOCUMENT if index == 0 else (64 if index == 1 else 32)
        decoded.append(_canonical_decode(line[len(label):-1], cap=limit))
    signed_document, signature, public_key = decoded
    if len(signature) != 64 or len(public_key) != 32:
        _deny()

    try:
        pins = verify_signed_fabric_roster(
            signed_document=signed_document,
            signature=signature,
            public_key=public_key,
            independently_trusted_key_sha256=independently_trusted_key_sha256,
            expected_commit=expected_commit,
            expected_release_id=expected_release_id,
        )
        compare_signed_fabric_roster(pins, observed_metadata)
    except (SignedFabricRosterUnqualified, ValueError, TypeError):
        _deny()

    return signed_document, signature, public_key
