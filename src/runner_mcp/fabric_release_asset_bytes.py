"""Source-only fixed-repository GitHub Release asset byte integrity verifier.

This is NOT an installer, local custody importer or identity authority. Callers
must hold separate trusted release identity/SHA256 pins. No user-provided URL,
file path, subprocess, authentication enrollment or host mutation is accepted.
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import re
import urllib.error
import urllib.parse
import urllib.request
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
