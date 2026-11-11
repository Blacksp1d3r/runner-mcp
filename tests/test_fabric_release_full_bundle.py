"""Synthetic in-memory Q7 manifest verification, no filesystem or network."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from runner_mcp.fabric_release_assets import ReleaseAdmission, ReleaseAsset
from runner_mcp.fabric_release_full_bundle import CompleteBundleMismatch, check_complete_q7_bundle
from runner_mcp.fabric_release_independent_roster import PinnedReleaseAsset, PinnedReleaseRoster

COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
TAG = "fabric-q7-bundle-" + COMMIT
PROJECT = "runner_fabric-1.2.3-py3-none-any.whl"
WHEELS = [PROJECT, *(f"dependency_{i:02d}-1.0-py3-none-any.whl" for i in range(28))]


def _manifest(**changes):
    values = {
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": COMMIT,
        "python": "3.12",
        "projectWheel": PROJECT,
        "wheelCount": 29,
        "bootstrapSha256": hashlib.sha256(b"synthetic-bootstrap").hexdigest(),
    }
    values.update(changes)
    return json.dumps(values, sort_keys=True).encode()


def _bodies():
    data = {"BOOTSTRAP.py": b"synthetic-bootstrap"}
    for idx, name in enumerate(WHEELS):
        data[name] = f"synthetic-{idx}".encode()
    data["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(data[name]).hexdigest()}  {name}\n"
        for name in sorted((*WHEELS, "BOOTSTRAP.py"))
    ).encode()
    data["COMMIT_SHA"] = (COMMIT + "\n").encode()
    data["BUNDLE.json"] = _manifest()
    assert len(data) == 33
    return data


def _inputs(bodies):
    pins = PinnedReleaseRoster(
        COMMIT,
        TAG,
        123,
        tuple(
            PinnedReleaseAsset(name, idx + 1, len(value), hashlib.sha256(value).hexdigest())
            for idx, (name, value) in enumerate(sorted(bodies.items()))
        ),
    )
    admission = ReleaseAdmission(
        pins.commit,
        pins.tag,
        pins.release_id,
        tuple(ReleaseAsset(x.asset_id, x.name, x.bytes, x.sha256) for x in pins.files),
        PROJECT,
    )
    return admission, pins


def _assert_rejected(bodies, *, pin_again=True):
    observed, pins = _inputs(bodies if pin_again else _bodies())
    with pytest.raises(CompleteBundleMismatch, match="fabric_release_full_bundle_unqualified"):
        check_complete_q7_bundle(observed, pins, bodies)


def test_all_33_manifest_and_sums_match_only():
    bodies = _bodies()
    result = check_complete_q7_bundle(*_inputs(bodies), bodies)
    assert result == {
        "inspection": "bundle_consistency_only",
        "asset_count": 33,
        "wheel_count": 29,
        "signed_source_verified": False,
        "wheel_metadata_verified": False,
        "local_custody_verified": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }


@pytest.mark.parametrize("field,bad", [
    ("schemaVersion", "wrong"),
    ("commitSha", "f" * 40),
    ("python", "3.11"),
    ("projectWheel", WHEELS[1]),
    ("wheelCount", 28),
    ("wheelCount", True),
    ("bootstrapSha256", "f" * 64),
])
def test_semantically_invalid_manifest_even_if_rehashed_denied(field, bad):
    bodies = _bodies()
    bodies["BUNDLE.json"] = _manifest(**{field: bad})
    _assert_rejected(bodies)


@pytest.mark.parametrize("raw", [
    b"not-json",
    b"\xff",
    b"[]",
    b'{"schemaVersion":1,"schemaVersion":2}',
    b"{" + b" " * (32 * 1024 + 1),
])
def test_malformed_duplicate_or_oversized_manifest_denied(raw):
    bodies = _bodies()
    bodies["BUNDLE.json"] = raw
    _assert_rejected(bodies)


@pytest.mark.parametrize("raw", [
    b"f" * 40,
    b"f" * 40 + b"\n",
    (COMMIT + "\n\n").encode(),
    (COMMIT + " ").encode(),
])
def test_commit_file_mismatch_denied(raw):
    bodies = _bodies()
    bodies["COMMIT_SHA"] = raw
    _assert_rejected(bodies)


@pytest.mark.parametrize("sums", [
    b"missing",
    b"",
    b"\xff",
    b"f" * 64 + b"  ../path.whl\n",
    b"f" * 64 + b"  BOOTSTRAP.py\n" + b"f" * 64 + b"  BOOTSTRAP.py\n",
    b"f" * 64 + b"  unexpected.whl\n",
    b"f" * 64 + b"  ../escape\n",
    b"f" * 64 + b"  BUILD\\manifest\n",
])
def test_bad_or_missing_sums_denied(sums):
    bodies = _bodies()
    bodies["SHA256SUMS"] = sums
    _assert_rejected(bodies)


def test_wrong_digest_even_with_original_pin_custody():
    bodies = _bodies()
    bodies[PROJECT] = b"tampered-synthetic-wheel"
    _assert_rejected(bodies, pin_again=False)


@pytest.mark.parametrize("name", ["BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py", PROJECT])
def test_empty_critical_asset_denied(name):
    bodies = _bodies()
    bodies[name] = b""
    _assert_rejected(bodies)


def test_extra_entry_denied():
    bodies = _bodies()
    bodies["unexpected.whl"] = b"x"
    _assert_rejected(bodies)


def test_missing_entry_denied():
    bodies = _bodies()
    del bodies["dependency_00-1.0-py3-none-any.whl"]
    _assert_rejected(bodies)


def test_non_bytes_asset_denied():
    bodies = _bodies()
    bodies[PROJECT] = bytearray(b"fake")  # type: ignore[assignment]
    observed, pins = _inputs(_bodies())
    with pytest.raises(CompleteBundleMismatch):
        check_complete_q7_bundle(observed, pins, bodies)


def test_wrong_source_pin_denied_before_bundle_parse():
    bodies = _bodies()
    observed, pins = _inputs(bodies)
    with pytest.raises(ValueError):
        check_complete_q7_bundle(
            replace(observed, release_id=222),
            pins,
            bodies,
        )


def test_commit_without_newline_allowed():
    bodies = _bodies()
    bodies["COMMIT_SHA"] = COMMIT.encode()
    assert check_complete_q7_bundle(*_inputs(bodies), bodies)["inspection"] == "bundle_consistency_only"
