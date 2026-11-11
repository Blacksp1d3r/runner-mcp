"""Offline synthetic security tests for the standalone Release metadata access probe."""
from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fabric_release_access_probe.py"
SPEC = importlib.util.spec_from_file_location("fabric_release_access_probe", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

SECRET = "ghu_TEST_PRIVATE_TOKEN_SAMPLE_123456"


def _release():
    return {
        "id": 123,
        "tag_name": probe._TAG,
        "target_commitish": probe._COMMIT,
        "draft": False,
        "prerelease": True,
        "assets": [{"id": n} for n in range(1, 34)],
    }


class FakeResponse:
    status = 200

    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.payload[:size]


class FakeOpener:
    def __init__(self, response=None, *, error=None):
        self.response = response or FakeResponse(json.dumps(_release()).encode())
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


def test_fixed_readonly_endpoint_no_asset_or_path_args():
    client = FakeOpener()
    assert probe.probe_metadata_access(SECRET, opener=client) == "PASS_METADATA_READ"
    [(req, timeout)] = client.requests
    assert req.full_url == probe._URL
    assert req.get_method() == "GET"
    assert "/releases/tags/" in req.full_url and "/assets/" not in req.full_url
    assert req.get_header("Authorization") == "Bearer " + SECRET
    assert timeout == 8


@pytest.mark.parametrize("bad", ["", "bad token", "\n", "x" * 513, None, True])
def test_bad_token_never_reaches_transport(bad):
    client = FakeOpener()
    assert probe.probe_metadata_access(bad, opener=client) == "WAIT_TOKEN_INVALID"
    assert client.requests == []


@pytest.mark.parametrize("code,expected", [
    (301, "WAIT_HTTP_UNAVAILABLE"), (302, "WAIT_HTTP_UNAVAILABLE"),
    (307, "WAIT_HTTP_UNAVAILABLE"), (308, "WAIT_HTTP_UNAVAILABLE"),
    (401, "WAIT_AUTHENTICATION"), (403, "WAIT_AUTHORIZATION_OR_RATE_LIMIT"),
    (404, "WAIT_RELEASE_NOT_ACCESSIBLE"), (429, "WAIT_HTTP_UNAVAILABLE"),
])
def test_no_redirect_or_remote_details_leak(code, expected):
    error = urllib.error.HTTPError(
        probe._URL, code, SECRET,
        {"Location": "https://malicious.example.invalid/?token=" + SECRET}, None,
    )
    client = FakeOpener(error=error)
    response = probe.probe_metadata_access(SECRET, opener=client)
    assert response == expected
    assert SECRET not in response and "malicious" not in response
    assert len(client.requests) == 1


def test_default_transport_disables_proxy_and_redirect(monkeypatch):
    calls = []

    class DummyOpener:
        def open(self, req, timeout):
            return FakeResponse(json.dumps(_release()).encode())

    def fake_build(*handlers):
        calls.extend(handlers)
        return DummyOpener()

    monkeypatch.setattr(probe.urllib.request, "build_opener", fake_build)
    assert probe.probe_metadata_access(SECRET) == "PASS_METADATA_READ"
    assert len(calls) == 2
    assert isinstance(calls[0], probe.urllib.request.ProxyHandler)
    assert calls[0].proxies == {}
    assert calls[1].redirect_request(None, None, 302, None, {}, "https://example.invalid") is None


@pytest.mark.parametrize("changes", [
    {"target_commitish": "f" * 40},
    {"tag_name": "fabric-q7-bundle-" + "f" * 40},
    {"draft": True}, {"prerelease": False}, {"id": True}, {"id": 0},
    {"assets": []}, {"assets": [{}] * 34},
])
def test_metadata_mismatch_does_not_pass(changes):
    payload = {**_release(), **changes}
    client = FakeOpener(response=FakeResponse(json.dumps(payload).encode()))
    assert probe.probe_metadata_access(SECRET, opener=client) == "WAIT_RESPONSE_UNQUALIFIED"


@pytest.mark.parametrize("payload", [
    b"{" + b" " * (256 * 1024),
    b'{"id":1,"id":2}',
    b"not json",
    b"\xff",
    b"[]",
])
def test_invalid_or_overlarge_response_denied(payload):
    client = FakeOpener(response=FakeResponse(payload))
    assert probe.probe_metadata_access(SECRET, opener=client) == "WAIT_RESPONSE_UNQUALIFIED"


def test_interactive_entrypoint_never_prints_token(monkeypatch, capsys):
    monkeypatch.setattr(probe, "_can_prompt", lambda: True)
    monkeypatch.setattr(probe.sys, "argv", ["fabric_release_access_probe.py"])
    monkeypatch.setattr(probe.getpass, "getpass", lambda _prompt: SECRET)
    monkeypatch.setattr(probe, "probe_metadata_access", lambda _token: "PASS_METADATA_READ")
    assert probe.main() == 0
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    assert "PASS_METADATA_READ" in captured.out
    assert "NO_DOWNLOAD_NO_INSTALL_NO_ACTIVATION" in captured.out


def test_no_credential_on_failed_interactive_probe(monkeypatch, capsys):
    monkeypatch.setattr(probe, "_can_prompt", lambda: True)
    monkeypatch.setattr(probe.sys, "argv", ["fabric_release_access_probe.py"])
    monkeypatch.setattr(probe.getpass, "getpass", lambda _prompt: SECRET)
    monkeypatch.setattr(probe, "probe_metadata_access", lambda _token: "WAIT_AUTHENTICATION")
    assert probe.main() == 1
    assert SECRET not in capsys.readouterr().out


def test_argv_token_attempt_denied_before_prompt(monkeypatch, capsys):
    monkeypatch.setattr(probe.sys, "argv", ["probe.py", "--token", SECRET])
    monkeypatch.setattr(probe.getpass, "getpass", lambda _: pytest.fail("prompt must not run"))
    assert probe.main() == 1
    assert capsys.readouterr().out.strip() == "WAIT_ARGUMENTS_UNSUPPORTED"


def test_noninteractive_terminal_denied_before_prompt(monkeypatch, capsys):
    monkeypatch.setattr(probe.sys, "argv", ["probe.py"])
    monkeypatch.setattr(probe, "_can_prompt", lambda: False)
    monkeypatch.setattr(probe.getpass, "getpass", lambda _: pytest.fail("prompt must not run"))
    assert probe.main() == 1
    assert capsys.readouterr().out.strip() == "WAIT_INTERACTIVE_TERMINAL_REQUIRED"


@pytest.mark.parametrize("declared", ["0", "-1", "999999999", "abc", "0010"])
def test_invalid_or_mismatched_content_length_denied(declared):
    body = json.dumps(_release()).encode()
    client = FakeOpener(response=FakeResponse(body, headers={"Content-Length": declared}))
    assert probe.probe_metadata_access(SECRET, opener=client) == "WAIT_RESPONSE_UNQUALIFIED"


def test_exact_content_length_passes():
    body = json.dumps(_release()).encode()
    client = FakeOpener(response=FakeResponse(body, headers={"Content-Length": str(len(body))}))
    assert probe.probe_metadata_access(SECRET, opener=client) == "PASS_METADATA_READ"
