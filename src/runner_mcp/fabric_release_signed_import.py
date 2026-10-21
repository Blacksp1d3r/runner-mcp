"""Bounded source-only Q7 private Release importer with separate signed roster.

No untrusted release metadata can establish its own SHA pins. The Ed25519
trust-key *digest* must be known through an independent owner-controlled
channel. This module checks possession of that key, not key authorization,
freshness, independent custody, serving identity or install permission.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .fabric_release_asset_bytes import fetch_pinned_asset_bytes
from .fabric_release_assets import (
    FabricReleaseAdmissionError,
    ReleaseAdmission,
    inspect_exact_release,
)
from .fabric_release_independent_roster import (
    PinnedReleaseAsset,
    PinnedReleaseRoster,
    compare_exact_pinned_q7_roster,
)
from .fabric_release_private_custody import stage_pinned_q7_bundle_once

_Q7_COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
_Q7_TAG = "fabric-q7-bundle-" + _Q7_COMMIT
_Q7_RELEASE_ID = 415955374
_API = "https://api.github.com/repos/Blacksp1d3r/Runner-Fabric/"
_MAX_JSON = 256 * 1024
_MAX_SIGNED = 32 * 1024
_MAX_ALL_ASSETS = 256 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_HEX_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.+\-]{0,150}\Z")
_USER_AGENT = "runner-mcp-pinned-q7-import"


class SignedQ7ImportUnqualified(ValueError):
    """Never include bearer, signed payload, local path or GitHub response."""


def _deny() -> None:
    raise SignedQ7ImportUnqualified("fabric_q7_signed_import_unqualified")


def _json_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _deny()
        result[key] = value
    return result


def _load_json(raw: bytes) -> Any:
    if type(raw) is not bytes or not 0 < len(raw) <= _MAX_JSON:
        _deny()
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_json_no_duplicates)
    except (UnicodeError, ValueError, RecursionError, TypeError):
        _deny()


def _signed_pins(
    signed_document: bytes,
    signature: bytes,
    public_key: bytes,
    independently_trusted_key_sha256: str,
) -> PinnedReleaseRoster:
    """Verify one fixed binary signed v1 roster, no API-provided trust root."""
    if (
        type(signed_document) is not bytes
        or not 0 < len(signed_document) <= _MAX_SIGNED
        or type(signature) is not bytes or len(signature) != 64
        or type(public_key) is not bytes or len(public_key) != 32
        or type(independently_trusted_key_sha256) is not str
        or _SHA256.fullmatch(independently_trusted_key_sha256) is None
        or not hmac.compare_digest(
            hashlib.sha256(public_key).hexdigest(), independently_trusted_key_sha256
        )
    ):
        _deny()
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, signed_document)
    except (ValueError, TypeError, InvalidSignature):
        _deny()
    data = _load_json(signed_document)
    if type(data) is not dict or set(data) != {
        "schema_version", "commit", "tag", "release_id", "files",
    } or data["schema_version"] != "runner-fabric/independent-q7-release-roster/v1":
        _deny()
    if (
        data["commit"] != _Q7_COMMIT or data["tag"] != _Q7_TAG
        or type(data["release_id"]) is not int or data["release_id"] != _Q7_RELEASE_ID
        or type(data["files"]) is not list or len(data["files"]) != 33
    ):
        _deny()
    pins = []
    total = 0
    seen_names: set[str] = set()
    seen_ids: set[int] = set()
    for row in data["files"]:
        if type(row) is not dict or set(row) != {"name", "asset_id", "bytes", "sha256"}:
            _deny()
        name, ident, size, digest = (
            row["name"], row["asset_id"], row["bytes"], row["sha256"]
        )
        if (
            type(name) is not str or _HEX_NAME.fullmatch(name) is None
            or name in seen_names
            or type(ident) is not int or ident <= 0 or ident in seen_ids
            or type(size) is not int or not 0 < size <= 64 * 1024 * 1024
            or type(digest) is not str or _SHA256.fullmatch(digest) is None
        ):
            _deny()
        seen_names.add(name)
        seen_ids.add(ident)
        total += size
        if total > _MAX_ALL_ASSETS:
            _deny()
        pins.append(PinnedReleaseAsset(name, ident, size, digest))
    return PinnedReleaseRoster(
        _Q7_COMMIT, _Q7_TAG, _Q7_RELEASE_ID, tuple(pins)
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _private_api_json(token: str, suffix: str) -> Any:
    """Exact hardcoded REST GET with proxy/redirect disabled and bounded size."""
    if type(token) is not str or not 8 <= len(token) <= 512 or not token.isascii() or (
        any(ord(char) <= 32 or ord(char) == 127 for char in token)
    ):
        _deny()
    if suffix not in {
        "releases/tags/" + _Q7_TAG, "git/ref/tags/" + _Q7_TAG,
    }:
        _deny()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    request = urllib.request.Request(
        _API + suffix,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=8) as reply:
            if reply.status != 200:
                _deny()
            size = reply.headers.get("Content-Length")
            if size is not None and (
                not size.isascii() or not size.isdecimal()
                or not 0 < int(size) <= _MAX_JSON
            ):
                _deny()
            data = reply.read(_MAX_JSON + 1)
            if len(data) > _MAX_JSON or size is not None and len(data) != int(size):
                _deny()
            return _load_json(data)
    except (OSError, ValueError, TypeError, urllib.error.URLError):
        _deny()


def read_pinned_q7_release(
    token: str,
    pins: PinnedReleaseRoster,
    *,
    api_reader: Callable[[str, str], object] = _private_api_json,
) -> ReleaseAdmission:
    """The Release tag and API roster must equal an independently signed set."""
    if type(pins) is not PinnedReleaseRoster or pins.commit != _Q7_COMMIT:
        _deny()
    release = api_reader(token, "releases/tags/" + _Q7_TAG)
    tag = api_reader(token, "git/ref/tags/" + _Q7_TAG)
    try:
        observed = inspect_exact_release(_Q7_COMMIT, release, tag)
        compare_exact_pinned_q7_roster(observed, pins)
    except (FabricReleaseAdmissionError, ValueError, TypeError, KeyError):
        _deny()
    if observed.release_id != _Q7_RELEASE_ID:
        _deny()
    return observed


def import_signed_pinned_q7_once(
    *,
    token: str,
    signed_roster: bytes,
    signature: bytes,
    public_key: bytes,
    independently_trusted_key_sha256: str,
    api_reader: Callable[[str, str], object] = _private_api_json,
    asset_reader: Callable[..., bytes] = fetch_pinned_asset_bytes,
    stage: Callable[..., dict[str, object]] = stage_pinned_q7_bundle_once,
) -> dict[str, object]:
    """Fetch all fixed signed 33/33 assets then validate+stage; NEVER install.

    The trusted key fingerprint is an independent operator input, not learned
    from GitHub. Real Black install additionally requires signed publishing
    authority, owner-local CLI custody and an explicit BOOTSTRAP preflight.
    """
    pins = _signed_pins(
        signed_roster, signature, public_key, independently_trusted_key_sha256
    )
    observed = read_pinned_q7_release(token, pins, api_reader=api_reader)
    blobs: dict[str, bytes] = {}
    total = 0
    for pin in sorted(pins.files, key=lambda p: p.name):
        try:
            blob = asset_reader(
                token=token,
                asset_id=pin.asset_id,
                expected_size=pin.bytes,
                independently_pinned_sha256=pin.sha256,
            )
        except (OSError, ValueError, TypeError):
            _deny()
        if type(blob) is not bytes or len(blob) != pin.bytes or not hmac.compare_digest(
            hashlib.sha256(blob).hexdigest(), pin.sha256
        ):
            _deny()
        total += len(blob)
        if total > _MAX_ALL_ASSETS:
            _deny()
        blobs[pin.name] = blob
    try:
        result = stage(observed, pins, blobs)
    except (ValueError, TypeError, OSError):
        _deny()
    if type(result) is not dict or result.get("state") != "owner_private_bytes_custodied":
        _deny()
    return {
        "state": "q7_signed_bytes_custodied_only",
        "asset_count": 33,
        "roster_signature_valid_for_supplied_key": True,
        "operator_signer_authority_attested": False,
        "install_authorized": False,
        "original_client_ack": False,
    }
