"""Synthetic-only release asset byte verification, with no network or disk writes."""
from __future__ import annotations

import hashlib
import importlib.util
import urllib.error
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "src/runner_mcp/fabric_release_asset_bytes.py"
SPEC = importlib.util.spec_from_file_location("fabric_release_asset_bytes", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

TOKEN = "ghu_SYNTHETIC_PRIVATE_DO_NOT_USE_123456"
ASSET = b"verified synthetic asset payload"
ASSET_SIZE = len(ASSET)
DIGEST = hashlib.sha256(ASSET).hexdigest()


class Response:
    status = 200

    def __init__(self, body=ASSET, headers=None):
        self.body = body
        self.headers = headers or {}
        self.index = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        p = self.body[self.index : self.index + n]
        self.index += len(p)
        return p


class Opener:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req, timeout))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def request(client, *, digest=DIGEST, size=ASSET_SIZE, asset_id=123):
    return mod.fetch_pinned_asset_bytes(
        token=TOKEN,
        asset_id=asset_id,
        expected_size=size,
        independently_pinned_sha256=digest,
        opener=client,
    )


def redirect(location, code=302):
    return urllib.error.HTTPError(
        mod._ROOT + "123", code, TOKEN, {"Location": location}, None
    )


def test_direct_200_pin_and_no_replay():
    client = Opener([Response(headers={"Content-Length": str(len(ASSET))})])
    assert request(client) == ASSET
    assert len(client.requests) == 1
    req, timeout = client.requests[0]
    assert req.get_method() == "GET" and req.full_url == mod._ROOT + "123"
    assert req.get_header("Authorization") == "Bearer " + TOKEN
    assert req.get_header("Accept") == "application/octet-stream"
    assert timeout == 8


def test_302_follows_only_approved_https_and_strips_bearer():
    location = "https://release-assets.githubusercontent.com/download?id=1&X-Amz-Signature=synthetic"
    client = Opener([redirect(location), Response()])
    assert request(client) == ASSET
    assert len(client.requests) == 2
    first, _ = client.requests[0]
    second, _ = client.requests[1]
    assert first.get_header("Authorization") == "Bearer " + TOKEN
    assert second.full_url == location
    assert second.get_header("Authorization") is None
    assert second.get_header("Cookie") is None
    assert second.get_header("X-GitHub-Api-Version") is None


@pytest.mark.parametrize("url", [
    "https://evil.example.invalid/blob",
    "https://release-assets.githubusercontent.com.evil.invalid/blob",
    "http://release-assets.githubusercontent.com/blob",
    "https://127.0.0.1/blob",
    "https://user:pass@release-assets.githubusercontent.com/blob",
    "https://release-assets.githubusercontent.com:123/blob",
    "https://release-assets.githubusercontent.com/blob#secret",
    "//release-assets.githubusercontent.com/blob",
    "file:///etc/passwd",
    "https://RELEASE-ASSETS.GITHUBUSERCONTENT.COM.evil.invalid/a",
    "x" * 8193,
])
def test_external_or_malformed_redirect_denied_with_one_request(url):
    client = Opener([redirect(url)])
    with pytest.raises(mod.AssetBytesUnqualified, match="fabric_release_asset_bytes_unqualified"):
        request(client)
    assert len(client.requests) == 1


@pytest.mark.parametrize("code", [301, 303, 307, 308, 401, 403, 404, 429])
def test_other_http_status_never_follows(code):
    client = Opener([redirect("https://release-assets.githubusercontent.com/blob", code)])
    with pytest.raises(mod.AssetBytesUnqualified):
        request(client)
    assert len(client.requests) == 1


@pytest.mark.parametrize("bad", [
    ("f" * 64, len(ASSET)),
    (DIGEST, len(ASSET) - 1),
    (DIGEST, len(ASSET) + 1),
    (DIGEST.upper(), len(ASSET)),
])
def test_wrong_digest_or_length_fail_closed(bad):
    client = Opener([Response()])
    with pytest.raises(mod.AssetBytesUnqualified):
        request(client, digest=bad[0], size=bad[1])


def test_content_length_mismatch_denied():
    client = Opener([Response(headers={"Content-Length": str(len(ASSET) + 1)})])
    with pytest.raises(mod.AssetBytesUnqualified):
        request(client)


@pytest.mark.parametrize("bad", [0, -1, True, "123", 2**63])
def test_asset_id_invalid_before_transport(bad):
    client = Opener([])
    with pytest.raises(mod.AssetBytesUnqualified):
        request(client, asset_id=bad)
    assert not client.requests


def test_no_auto_proxy_or_redirect(monkeypatch):
    got = []

    def build(*handlers):
        got.extend(handlers)
        return Opener([Response()])

    monkeypatch.setattr(mod.urllib.request, "build_opener", build)
    assert mod.fetch_pinned_asset_bytes(
        token=TOKEN, asset_id=123, expected_size=len(ASSET), independently_pinned_sha256=DIGEST
    ) == ASSET
    assert len(got) == 2
    assert got[0].proxies == {}
    assert got[1].redirect_request(None, None, 302, None, {}, "https://bad") is None


def test_redirect_without_location_denied():
    client = Opener([
        urllib.error.HTTPError(mod._ROOT + "123", 302, TOKEN, {}, None)
    ])
    with pytest.raises(mod.AssetBytesUnqualified):
        request(client)
    assert len(client.requests) == 1
