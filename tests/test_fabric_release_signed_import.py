"""Synthetic signed-Q7 importer orchestration, no live credentials or disk mutation."""
from __future__ import annotations

import hashlib
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.fabric_release_signed_import import (
    SignedQ7ImportUnqualified,
    _private_api_json,
    _signed_pins,
    import_q7_disposable_lab_once,
    import_signed_pinned_q7_once,
    probe_q7_disposable_lab_metadata,
    probe_signed_pinned_q7_metadata,
)

REV = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
TAG = "fabric-q7-bundle-" + REV
FILES = ["BOOTSTRAP.py", "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS"] + [
    "runner_fabric-0.0.1-py3-none-any.whl"
] + [f"synthetic_{n:02d}-1.0-py3-none-any.whl" for n in range(28)]


def _signed():
    private = Ed25519PrivateKey.generate()
    key = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    blobs = {name: f"synthetic-only-{i}".encode() for i, name in enumerate(FILES)}
    entries = [
        {
            "name": name, "asset_id": i + 100,
            "bytes": len(blobs[name]), "sha256": hashlib.sha256(blobs[name]).hexdigest(),
        } for i, name in enumerate(FILES)
    ]
    roster = {
        "schema_version": "runner-fabric/independent-q7-release-roster/v1",
        "commit": REV, "tag": TAG,
        "release_id": 415955374, "files": entries,
    }
    raw = json.dumps(roster, sort_keys=True, separators=(",", ":")).encode()
    return private, key, raw, private.sign(raw), blobs, roster


def _api(roster):
    release = {
        "id": 415955374, "tag_name": TAG, "target_commitish": REV,
        "draft": False, "prerelease": True,
        "assets": [{
            "name": p["name"], "id": p["asset_id"], "size": p["bytes"],
            "digest": "sha256:" + p["sha256"],
        } for p in roster["files"]],
    }
    tagged = {
        "ref": "refs/tags/" + TAG,
        "object": {"type": "commit", "sha": REV},
    }
    return lambda token, suffix: tagged if suffix.startswith("git/ref") else release


def _execute(*, corrupt=None, wrong_api=None, wrong_asset=None, wrong_signer=None):
    private, key, raw, signature, blobs, roster = _signed()
    api = _api(roster) if wrong_api is None else wrong_api
    calls = []

    def asset_reader(*, token, asset_id, expected_size, independently_pinned_sha256):
        calls.append(("asset", asset_id))
        name = roster["files"][asset_id - 100]["name"]
        return b"tampered" if wrong_asset == name else blobs[name]

    def stage(admission, signed_roster, downloaded):
        calls.append(("stage", len(downloaded)))
        return {"state": "owner_private_bytes_custodied"}

    args = {
        "token": "synthetic-token-contents-read",
        "signed_roster": raw, "signature": signature,
        "public_key": key,
        "independently_trusted_key_sha256": hashlib.sha256(key).hexdigest(),
        "api_reader": api, "asset_reader": asset_reader,
        "stage": stage,
    }
    if wrong_signer == "signature":
        args["signature"] = b"x" * 64
    if wrong_signer == "digest":
        args["independently_trusted_key_sha256"] = "0" * 64
    if corrupt == "duplicate":
        args["signed_roster"] = raw.replace(b'"commit":', b'"commit":"evil","commit":', 1)
        args["signature"] = private.sign(args["signed_roster"])
    if corrupt == "wrong_id":
        roster["release_id"] = 415955375
        args["signed_roster"] = json.dumps(roster).encode()
        args["signature"] = private.sign(args["signed_roster"])
    return args, calls


def test_signed_exact_q7_release_fetches_33_then_invokes_existing_custody_once():
    args, calls = _execute()
    assert import_signed_pinned_q7_once(**args) == {
        "state": "q7_signed_bytes_custodied_only",
        "asset_count": 33,
        "roster_signature_valid_for_supplied_key": True,
        "operator_signer_authority_attested": False,
        "install_authorized": False,
        "original_client_ack": False,
    }
    assert calls.count(("stage", 33)) == 1
    assert len([c for c in calls if c[0] == "asset"]) == 33


@pytest.mark.parametrize("invalid", ["signature", "digest"])
def test_invalid_signer_rejected_before_network_or_stage(invalid):
    args, calls = _execute(wrong_signer=invalid)
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert calls == []


@pytest.mark.parametrize("invalid", ["duplicate", "wrong_id"])
def test_malformed_or_wrong_release_signed_roster_denied_before_network(invalid):
    args, calls = _execute(corrupt=invalid)
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert calls == []


def test_wrong_metadata_release_id_denied_before_asset_fetch():
    args, calls = _execute()
    actual_api = args["api_reader"]

    def wrong_api(token, suffix):
        data = actual_api(token, suffix)
        if suffix.startswith("releases/"):
            return {**data, "id": 222}
        return data

    args["api_reader"] = wrong_api
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert calls == []


def test_wrong_tag_ref_denied_before_asset_fetch():
    args, calls = _execute()
    actual_api = args["api_reader"]

    def wrong_api(token, suffix):
        data = actual_api(token, suffix)
        if suffix.startswith("git/"):
            return {**data, "object": {"type": "commit", "sha": "f" * 40}}
        return data

    args["api_reader"] = wrong_api
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert calls == []


def test_changed_rehashed_api_asset_rejected_before_stage():
    args, calls = _execute()
    actual_api = args["api_reader"]

    def wrong_api(token, suffix):
        data = actual_api(token, suffix)
        if suffix.startswith("releases/"):
            assets = [dict(x) for x in data["assets"]]
            assets[0]["digest"] = "sha256:" + "1" * 64
            return {**data, "assets": assets}
        return data

    args["api_reader"] = wrong_api
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert calls == []


def test_modified_asset_bytes_denied_without_stage():
    args, calls = _execute()
    raw_reader = args["asset_reader"]

    def corrupt_reader(**kwargs):
        value = raw_reader(**kwargs)
        return b"tampered" if kwargs["asset_id"] == 100 else value

    args["asset_reader"] = corrupt_reader
    with pytest.raises(SignedQ7ImportUnqualified):
        import_signed_pinned_q7_once(**args)
    assert not any(c[0] == "stage" for c in calls)


@pytest.mark.parametrize("value", ["bad", "evil", "https://unexpected.invalid"])
def test_api_suffix_rejects_other_paths_before_network(value):
    with pytest.raises(SignedQ7ImportUnqualified):
        _private_api_json("synthetic-token", value)


def test_invalid_key_digest_denied_in_separate_signature_preflight():
    private, key, raw, signature, _, _ = _signed()
    del private
    with pytest.raises(SignedQ7ImportUnqualified):
        _signed_pins(raw, signature, key, "not-a-sha256")



def test_probe_metadata_exact_roster_reuses_private_api_without_asset_fetch():
    args, calls = _execute()
    received = []

    def api_reader(token, suffix):
        received.append(suffix)
        return args["api_reader"](token, suffix)

    outcome = probe_signed_pinned_q7_metadata(
        token=args["token"],
        signed_roster=args["signed_roster"],
        signature=args["signature"],
        public_key=args["public_key"],
        independently_trusted_key_sha256=args["independently_trusted_key_sha256"],
        api_reader=api_reader,
    )
    assert outcome == {
        "state": "q7_release_metadata_exact_under_supplied_key",
        "asset_count": 33,
        "download_performed": False,
        "custody_performed": False,
        "operator_signer_authority_attested": False,
        "install_authorized": False,
        "original_client_ack": False,
    }
    assert received == [
        "releases/tags/" + TAG,
        "git/ref/tags/" + TAG,
    ]
    assert calls == []


@pytest.mark.parametrize("bad", ["signature", "digest"])
def test_probe_wrong_signer_denied_without_api_or_asset_fetch(bad):
    args, calls = _execute(wrong_signer=bad)
    received = []
    def spy(token, suffix):
        received.append(suffix)
        return args["api_reader"](token, suffix)
    with pytest.raises(SignedQ7ImportUnqualified):
        probe_signed_pinned_q7_metadata(
            token=args["token"], signed_roster=args["signed_roster"],
            signature=args["signature"], public_key=args["public_key"],
            independently_trusted_key_sha256=args["independently_trusted_key_sha256"],
            api_reader=spy,
        )
    assert received == []
    assert calls == []


def test_probe_changed_release_digest_refuses_exact_signed_roster():
    args, calls = _execute()
    original = args["api_reader"]
    def tampered(token, suffix):
        data = original(token, suffix)
        if suffix.startswith("releases/"):
            assets = [dict(x) for x in data["assets"]]
            assets[-1]["digest"] = "sha256:" + "e" * 64
            return {**data, "assets": assets}
        return data
    with pytest.raises(SignedQ7ImportUnqualified):
        probe_signed_pinned_q7_metadata(
            token=args["token"], signed_roster=args["signed_roster"],
            signature=args["signature"], public_key=args["public_key"],
            independently_trusted_key_sha256=args["independently_trusted_key_sha256"],
            api_reader=tampered,
        )
    assert calls == []


def test_disposable_lab_probe_no_key_no_asset_fetch_no_authority():
    args, calls = _execute()
    result = probe_q7_disposable_lab_metadata(
        token=args["token"], api_reader=args["api_reader"],
    )
    assert result == {
        "state": "q7_lab_metadata_only_untrusted_publisher",
        "asset_count": 33, "publisher_authenticated": False,
        "download_performed": False, "install_authorized": False,
        "original_client_ack": False,
    }
    assert calls == []


def test_disposable_lab_keyless_import_reuses_all_33_hash_and_private_stage():
    args, calls = _execute()
    result = import_q7_disposable_lab_once(
        token=args["token"], api_reader=args["api_reader"],
        asset_reader=args["asset_reader"], stage=args["stage"],
    )
    assert result == {
        "state": "q7_lab_bytes_custodied_only",
        "asset_count": 33, "publisher_authenticated": False,
        "install_authorized": False, "original_client_ack": False,
    }
    assert len([call for call in calls if call[0] == "asset"]) == 33
    assert calls.count(("stage", 33)) == 1


def test_disposable_lab_tampered_asset_denied_without_storage():
    args, calls = _execute(wrong_asset=FILES[0])
    with pytest.raises(SignedQ7ImportUnqualified):
        import_q7_disposable_lab_once(
            token=args["token"], api_reader=args["api_reader"],
            asset_reader=args["asset_reader"], stage=args["stage"],
        )
    assert not any(call[0] == "stage" for call in calls)


def test_disposable_lab_wrong_fixed_release_denied_before_asset_fetch():
    args, calls = _execute()
    original = args["api_reader"]
    def mismatched_release(token, suffix):
        data = original(token, suffix)
        if suffix.startswith("releases/"):
            return {**data, "id": 99999999}
        return data
    with pytest.raises(SignedQ7ImportUnqualified):
        import_q7_disposable_lab_once(
            token=args["token"], api_reader=mismatched_release,
            asset_reader=args["asset_reader"], stage=args["stage"],
        )
    assert calls == []


def test_disposable_lab_rejects_modified_metadata_digest_by_byte_hash():
    args, calls = _execute()
    original = args["api_reader"]
    def changed_digest(token, suffix):
        data = original(token, suffix)
        if suffix.startswith("releases/"):
            assets = [dict(x) for x in data["assets"]]
            assets[0]["digest"] = "sha256:" + "f" * 64
            return {**data, "assets": assets}
        return data
    with pytest.raises(SignedQ7ImportUnqualified):
        import_q7_disposable_lab_once(
            token=args["token"], api_reader=changed_digest,
            asset_reader=args["asset_reader"], stage=args["stage"],
        )
    assert not any(call[0] == "stage" for call in calls)
