"""F30 Release-foutcategorieën: offline beveiligingstests zonder download.

De bestaande FabricUpdateManager gebruikt uitsluitend twee vaste GitHub-
metadata-endpoints. Een 404 is geen host- of installatiebevoegdheid; deze tests
tonen alleen het onderscheid tussen afwezige, defecte en onbereikbare metadata.
"""

from __future__ import annotations

import json
import urllib.error

import pytest

from runner_mcp.fabric_update import (
    FabricUpdateError,
    FabricUpdateManager,
    bounded_fabric_readiness_failure,
)

COMMIT = "a" * 40
TAG = "fabric-update-bundle-" + COMMIT
SECRET = "synthetic-sensitive-token"
DIGEST = "b" * 64


def _release(digest: str | None = "sha256:" + DIGEST) -> dict:
    names = [
        "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py",
        "runner_fabric-0.0.1-py3-none-any.whl",
    ]
    return {
        "id": 19, "tag_name": TAG, "target_commitish": COMMIT,
        "draft": False, "prerelease": True,
        "assets": [
            {"id": index, "name": name, "size": 44, "digest": digest}
            for index, name in enumerate(names, 1)
        ],
    }


def _tag() -> dict:
    return {
        "ref": "refs/tags/" + TAG,
        "object": {"type": "commit", "sha": COMMIT},
    }


class _Response:
    def __init__(self, value: object):
        self.payload = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class _Opener:
    def __init__(self, release: object, ref: object):
        self.release = release
        self.ref = ref
        self.paths: list[str] = []

    def open(self, request, timeout):
        assert timeout == 60
        assert request.get_method() == "GET"
        assert request.get_header("Authorization") == "Bearer " + SECRET
        self.paths.append(request.full_url)
        assert request.full_url.startswith(
            "https://api.github.com/repos/Blacksp1d3r/Runner-Fabric/"
        )
        assert "/assets/" not in request.full_url
        assert "/actions/" not in request.full_url
        if request.full_url.endswith("/releases/tags/" + TAG):
            outcome = self.release
        elif request.full_url.endswith("/git/ref/tags/" + TAG):
            outcome = self.ref
        else:
            pytest.fail("unknown or mutable endpoint")
        if isinstance(outcome, Exception):
            raise outcome
        return _Response(outcome)


def _http_error(status: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.github.com/hidden", status,
        "secret-hidden-provider-message", {}, None,
    )


def _manager(monkeypatch, release=None, ref=None):
    """Skip constructors (no filesystem), retain the actual HTTP JSON parser."""
    manager = object.__new__(FabricUpdateManager)
    opener = _Opener(_release() if release is None else release,
                     _tag() if ref is None else ref)
    monkeypatch.setattr(manager, "_opener", opener)
    monkeypatch.setattr(manager, "_require_safe_runtime", lambda: None)
    monkeypatch.setattr(manager, "_assert_managed_launcher", lambda: None)
    monkeypatch.setattr(manager, "_github_token", lambda: SECRET)
    for method in ("_download_artifact", "_activate_bundle", "_start",
                   "stage_local_bundle", "start", "start_local", "rollback"):
        monkeypatch.setattr(
            manager, method,
            lambda *_args, **_kwargs: pytest.fail("mutation forbidden"),
        )
    return manager, opener


def _reason(manager: FabricUpdateManager) -> str:
    with pytest.raises(FabricUpdateError) as error:
        manager.release_assets_readiness(COMMIT)
    reason = str(error.value)
    response = bounded_fabric_readiness_failure(error.value, source="github-release")
    assert response == {
        "state": "blocked",
        "reasonCode": reason,
        "artifact_ready": False,
        "source": "github-release",
    }
    assert SECRET not in repr(response)
    assert "secret-hidden-provider-message" not in repr(response)
    return reason


def test_valid_metadata_remains_read_only_and_does_not_install(monkeypatch):
    manager, opener = _manager(monkeypatch)
    result = manager.release_assets_readiness(COMMIT)
    assert result["state"] == "ready"
    assert result["mutation_authorized"] is False
    assert result["download_performed"] is False
    assert result["project_wheel_sha256"] == DIGEST
    assert len(opener.paths) == 2


def test_release_not_published_only_when_both_exact_refs_are_404(monkeypatch):
    manager, opener = _manager(
        monkeypatch, release=_http_error(404), ref=_http_error(404),
    )
    assert _reason(manager) == "release_not_published"
    assert len(opener.paths) == 2


@pytest.mark.parametrize(("release", "ref"), [
    (_http_error(404), _tag()),
    (_release(), _http_error(404)),
])
def test_dangling_tag_or_release_must_not_look_unpublished(monkeypatch, release, ref):
    manager, _ = _manager(monkeypatch, release=release, ref=ref)
    assert _reason(manager) == "fabric_release_assets_unqualified"


@pytest.mark.parametrize("error", [
    _http_error(401), _http_error(403), _http_error(429),
    urllib.error.URLError("private-provider-failure"),
])
def test_provider_failures_are_not_release_absence(monkeypatch, error):
    manager, _ = _manager(monkeypatch, release=error)
    assert _reason(manager) == "release_provider_unavailable"


@pytest.mark.parametrize("digest", [None, "sha256:" + "b" * 63,
                                   "sha256:" + "z" * 64, ""] )
def test_invalid_digest_has_specific_bounded_denial(monkeypatch, digest):
    manager, _ = _manager(monkeypatch, release=_release(digest))
    assert _reason(manager) == "release_digest_invalid"


def test_forged_http_200_not_found_json_is_not_absent(monkeypatch):
    manager, _ = _manager(
        monkeypatch, release={"message": "Not Found"},
        ref={"message": "Not Found"},
    )
    assert _reason(manager) == "fabric_release_assets_unqualified"


def test_preflight_errors_never_override_runtime_gate(monkeypatch):
    manager, opener = _manager(monkeypatch)
    def reject_runtime():
        raise FabricUpdateError("runner_mcp_state_unavailable")
    monkeypatch.setattr(manager, "_require_safe_runtime", reject_runtime)
    assert _reason(manager) == "runner_mcp_state_unavailable"
    assert opener.paths == []
