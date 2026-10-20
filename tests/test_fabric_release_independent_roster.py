"""Synthetic security tests for independent 33-asset roster equality (no I/O)."""
from __future__ import annotations

from dataclasses import replace

import pytest

from runner_mcp.fabric_release_assets import ReleaseAdmission, ReleaseAsset
from runner_mcp.fabric_release_independent_roster import (
    IndependentRosterMismatch,
    PinnedReleaseAsset,
    PinnedReleaseRoster,
    compare_exact_pinned_q7_roster,
)

COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
TAG = "fabric-q7-bundle-" + COMMIT
RELEASE_ID = 481
PROJECT = "runner_fabric-1.2.3-py3-none-any.whl"
NAMES = (
    "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py", PROJECT,
    *(f"dependency_{i:02d}-1.0-py3-none-any.whl" for i in range(28)),
)


def _pins() -> PinnedReleaseRoster:
    return PinnedReleaseRoster(
        COMMIT,
        TAG,
        RELEASE_ID,
        tuple(
            PinnedReleaseAsset(name, i + 100, i + 1000, f"{i + 1:064x}")
            for i, name in enumerate(NAMES)
        ),
    )


def _observed(pins: PinnedReleaseRoster) -> ReleaseAdmission:
    return ReleaseAdmission(
        pins.commit,
        pins.tag,
        pins.release_id,
        tuple(
            ReleaseAsset(pin.asset_id, pin.name, pin.bytes, pin.sha256)
            for pin in reversed(pins.files)
        ),
        PROJECT,
    )


def test_exact_33_roster_matches_without_authority():
    pins = _pins()
    result = compare_exact_pinned_q7_roster(_observed(pins), pins)
    assert result == {
        "comparison": "match_only",
        "asset_count": 33,
        "trusted_signer_verified": False,
        "download_performed": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }


def test_order_does_not_confer_or_remove_trust():
    pins = _pins()
    observed = _observed(pins)
    assert compare_exact_pinned_q7_roster(
        replace(observed, files=tuple(reversed(observed.files))), pins
    )["comparison"] == "match_only"


@pytest.mark.parametrize("field,bad", [
    ("commit", "f" * 40),
    ("tag", "fabric-q7-bundle-" + "f" * 40),
    ("release_id", 999),
    ("release_id", True),
    ("project_wheel", "dependency_00-1.0-py3-none-any.whl"),
    ("files", ()),
])
def test_observed_identity_or_roster_divergence_denied(field, bad):
    pins = _pins()
    observed = replace(_observed(pins), **{field: bad})
    with pytest.raises(IndependentRosterMismatch, match="fabric_release_independent_roster_unqualified"):
        compare_exact_pinned_q7_roster(observed, pins)


@pytest.mark.parametrize("field,bad", [
    ("asset_id", 765432),
    ("asset_id", True),
    ("name", "foreign.whl"),
    ("name", "../forged.whl"),
    ("bytes", 123),
    ("bytes", True),
    ("sha256", "0" * 64),
    ("sha256", "A" * 64),
])
def test_observed_asset_tamper_denied(field, bad):
    pins = _pins()
    observed = _observed(pins)
    modified = (replace(observed.files[0], **{field: bad}), *observed.files[1:])
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(replace(observed, files=modified), pins)


def test_malformed_observed_asset_object_denied_without_attribute_error():
    pins = _pins()
    observed = _observed(pins)
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(
            replace(observed, files=(None, *observed.files[1:])), pins
        )


@pytest.mark.parametrize("field,bad", [
    ("commit", "f" * 40),
    ("commit", True),
    ("tag", "fabric-update-bundle-" + COMMIT),
    ("release_id", 0),
    ("release_id", True),
    ("files", ()),
    ("files", []),
])
def test_untrusted_or_incomplete_pin_container_rejected(field, bad):
    pins = replace(_pins(), **{field: bad})
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(_observed(_pins()), pins)


@pytest.mark.parametrize("field,bad", [
    ("asset_id", 0),
    ("asset_id", True),
    ("name", "/bad.whl"),
    ("name", "BUNDLE.json"),
    ("bytes", 0),
    ("bytes", 64 * 1024 * 1024 + 1),
    ("bytes", True),
    ("sha256", "z" * 64),
    ("sha256", "F" * 64),
])
def test_invalid_or_nonunique_pin_rejected(field, bad):
    original = _pins()
    modified = (replace(original.files[1], **{field: bad}), *original.files[2:])
    # Keep the first row, replace the second so duplicate identity is detectable.
    modified = (original.files[0], *modified)
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(_observed(original), replace(original, files=modified))


def test_duplicate_observed_name_or_id_denied():
    pins = _pins()
    observed = _observed(pins)
    dup = replace(observed.files[1], name=observed.files[0].name)
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(
            replace(observed, files=(observed.files[0], dup, *observed.files[2:])),
            pins,
        )


def test_out_of_order_duplicate_pins_denied():
    pins = _pins()
    duplicate = replace(pins.files[1], asset_id=pins.files[0].asset_id)
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(
            _observed(pins),
            replace(pins, files=(pins.files[0], duplicate, *pins.files[2:])),
        )


def test_unhashable_observed_name_fails_closed():
    pins = _pins()
    observed = _observed(pins)
    malformed = replace(observed.files[0], name=["untrusted"])
    with pytest.raises(IndependentRosterMismatch):
        compare_exact_pinned_q7_roster(
            replace(observed, files=(malformed, *observed.files[1:])),
            pins,
        )
