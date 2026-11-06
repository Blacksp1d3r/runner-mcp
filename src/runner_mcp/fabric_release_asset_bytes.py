"""Begrensde byte-download uit bestaande vaste Runner-Fabric GitHub Release.

De bestaande individuele downloader controleert de aan een onafhankelijk
rooster gekoppelde SHA-256 en grootte. De nieuwe batch-ingang hergebruikt
die downloader én de al bestaande Ed25519-/ZIP-/manifestverifiers: pas na
volledige bytecontrole levert zij de blobs in geheugen terug.

Een door de aanroeper zelf gekozen signer, bron-pin of GitHub-digest levert
GEEN eigenaarbevoegdheid op. Geen vrij te kiezen URL, filesystempad, opslag,
installer, proces-, service- of rollbackmutatie. De bestaande Q7-casus blijft
afzonderlijk; de toekomstige officiële Fabric-publisher moet zijn eigen
onafhankelijk vertrouwde sleutel en bronbeleid nog leveren.
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

_ROOT = "https://api.github.com/repos/Blacksp1d3r/Runner-Fabric/releases/assets/"
_BLOB_HOST = "release-assets.githubusercontent.com"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ASSET_BYTES = 64 * 1024 * 1024
_CHUNK = 64 * 1024


class AssetBytesUnqualified(ValueError):
    """Opaque failure: never reveal bearer, signed URL or asset bytes."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fail() -> None:
    raise AssetBytesUnqualified("fabric_release_asset_bytes_unqualified")


def _stream_verified(response: Any, expected_size: int, expected_sha256: str) -> bytes:
    if getattr(response, "status", None) != 200:
        _fail()
    headers = getattr(response, "headers", {})
    declared = headers.get("Content-Length")
    if declared is not None and (
        not isinstance(declared, str)
        or re.fullmatch(r"[0-9]{1,9}", declared) is None
        or int(declared) != expected_size
    ):
        _fail()
    output = bytearray()
    digest = hashlib.sha256()
    try:
        while len(output) <= expected_size:
            chunk = response.read(min(_CHUNK, expected_size + 1 - len(output)))
            if not chunk:
                break
            if not isinstance(chunk, bytes):
                _fail()
            if len(output) + len(chunk) > expected_size:
                _fail()
            digest.update(chunk)
            output.extend(chunk)
    except (OSError, http.client.HTTPException, TimeoutError, ValueError):
        _fail()
    if len(output) != expected_size or not hmac.compare_digest(
        digest.hexdigest(), expected_sha256
    ):
        _fail()
    return bytes(output)


def _blob_url_approved(location: object) -> bool:
    if not isinstance(location, str) or len(location) > 8192:
        return False
    try:
        url = urllib.parse.urlsplit(location)
        return (
            url.scheme == "https"
            and url.hostname == _BLOB_HOST
            and url.port in (None, 443)
            and url.username is None
            and url.password is None
            and bool(url.path) and url.path.startswith("/")
            and not url.fragment
        )
    except ValueError:
        return False


def fetch_pinned_asset_bytes(
    *,
    token: str,
    asset_id: int,
    expected_size: int,
    independently_pinned_sha256: str,
    opener: Any | None = None,
) -> bytes:
    """Download ONE verified byte blob into memory without persisting/activating.

    Pins MUST come from independently trusted custody, not simply untrusted
    GitHub metadata. Release identity, the full 33-asset roster and independent
    signer are separate approval gates; the bytes alone confer no authority.
    """
    if (
        type(token) is not str or not 8 <= len(token) <= 512
        or re.fullmatch(r"[\x21-\x7e]+", token) is None
        or type(asset_id) is not int or not 0 < asset_id <= 2**63 - 1
        or type(expected_size) is not int or not 0 < expected_size <= _MAX_ASSET_BYTES
        or not isinstance(independently_pinned_sha256, str)
        or _SHA256.fullmatch(independently_pinned_sha256) is None
    ):
        _fail()

    client = opener if opener is not None else urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect()
    )
    request = urllib.request.Request(
        _ROOT + str(asset_id),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/octet-stream",
            "User-Agent": "runner-mcp-asset-bytes-source-verifier",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        try:
            response = client.open(request, timeout=8)
        except urllib.error.HTTPError as err:
            if err.code != 302:
                _fail()
            headers = getattr(err, "headers", None)
            location = headers.get("Location") if headers is not None else None
            if not _blob_url_approved(location):
                _fail()
            # A fresh GET does not forward bearer, cookies or API headers.
            clean_request = urllib.request.Request(
                location,
                headers={"User-Agent": "runner-mcp-asset-bytes-source-verifier"},
                method="GET",
            )
            response = client.open(clean_request, timeout=8)
        with response:
            return _stream_verified(response, expected_size, independently_pinned_sha256)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        http.client.HTTPException,
        TimeoutError,
        ValueError,
    ):
        raise AssetBytesUnqualified("fabric_release_asset_bytes_unqualified") from None


def fetch_exact_signed_fabric_bundle_bytes(
    *,
    token: str,
    signed_document: bytes,
    signature: bytes,
    public_key: bytes,
    independently_trusted_key_sha256: str,
    expected_commit: str,
    expected_release_id: int,
    observed_metadata: ReleaseAdmission,
    asset_reader: Callable[..., bytes] = fetch_pinned_asset_bytes,
) -> dict[str, bytes]:
    """Lees alle exacte signed-releasebytes; retour enkel na volledige verificatie.

    De eigenaar/Fabric moet de verwachte commit, release-ID en publieke
    sleutelvingerafdruk VOORAF onafhankelijk aan de aanroeper bezorgen. Een
    synthetische of zelf gekozen handtekening geeft nooit autorisatie voor een
    update. `observed_metadata` is het resultaat van de bestaande exacte
    GitHub Release- en tag-ref-controle, geen vertrouwde signer.

    Volgorde: valideer ondertekend rooster + exact waargenomen metadata VOOR
    de eerste asset-GET; hergebruik voor elke asset de bestaande vaste
    `fetch_pinned_asset_bytes`, controleer de geretourneerde bytes ook bij
    een gemockte lezer en controleer tenslotte het volledige manifest,
    SHA256SUMS en alle ZIP/METADATA/RECORD-inhouden met de bestaande parser.

    Bij één fout wordt geen gedeeltelijke dict teruggegeven, en wordt geen
    bestand op de host aangemaakt. Bestaande actieve Fabric/Claude/Qwen-paden
    worden nooit aangeroepen; de functie is GEEN custody of installer.
    """
    # De historische individuele assetlezer wordt ook rechtstreeks als
    # standalone module geladen. Verplaats alleen de NIEUWE batch-afhankelijk-
    # heden naar de batch-aanroep, zodat het bestaande Q7/testcontract blijft.
    from .fabric_release_assets import ReleaseAdmission
    from .fabric_release_signed_roster import (
        SignedFabricRosterUnqualified,
        compare_signed_fabric_roster,
        verify_signed_fabric_roster,
    )
    from .fabric_release_wheelhouse import (
        WheelhouseUnqualified,
        verify_signed_fabric_wheelhouse,
    )

    if (
        type(token) is not str
        or not 8 <= len(token) <= 512
        or re.fullmatch(r"[\x21-\x7e]+", token) is None
        or not callable(asset_reader)
        or type(observed_metadata) is not ReleaseAdmission
    ):
        _fail()

    try:
        signed_pins = verify_signed_fabric_roster(
            signed_document=signed_document,
            signature=signature,
            public_key=public_key,
            independently_trusted_key_sha256=independently_trusted_key_sha256,
            expected_commit=expected_commit,
            expected_release_id=expected_release_id,
        )
        # Geen netwerk, disk of gedeeltelijke downloads vóór deze vergelijking.
        compare_signed_fabric_roster(signed_pins, observed_metadata)
    except (SignedFabricRosterUnqualified, TypeError, ValueError):
        _fail()

    blobs: dict[str, bytes] = {}
    total = 0
    for pin in signed_pins.files:
        try:
            blob = asset_reader(
                token=token,
                asset_id=pin.asset_id,
                expected_size=pin.bytes,
                independently_pinned_sha256=pin.sha256,
            )
        except (OSError, ValueError, TypeError, TimeoutError,
                urllib.error.URLError, http.client.HTTPException):
            _fail()
        if (
            type(blob) is not bytes
            or len(blob) != pin.bytes
            or not hmac.compare_digest(hashlib.sha256(blob).hexdigest(), pin.sha256)
        ):
            _fail()
        total += len(blob)
        if total > 256 * 1024 * 1024:
            _fail()
        blobs[pin.name] = blob

    # De bestaande generieke verifier hergebruikt de historische Q7-wheel-
    # parser. Ook een ZIP-inhoud met een correct gepinde externe SHA kan
    # ongeldig zijn; die mag nooit als complete bundel terugkeren.
    try:
        verify_signed_fabric_wheelhouse(signed_pins, observed_metadata, blobs)
    except (WheelhouseUnqualified, ValueError, TypeError):
        _fail()
    return blobs
