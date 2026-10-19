from __future__ import annotations

import hashlib
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.serving_witness_preflight import signed_serving_witness_preflight

_NOW = 2_000_000_000
_SOURCE = "a" * 40
_WHEEL = "b" * 64
_GEN = "c" * 64
_HOST = "d" * 64
_CHALLENGE = "e" * 32
_ROLES = ("server", "watcher", "tunnel")
_EXPECTED = {
    "independently_expected_host_digest": _HOST,
    "independently_expected_roles": _ROLES,
    "independently_expected_challenge": _CHALLENGE,
    "independently_expected_source_revision": _SOURCE,
    "independently_expected_wheel_sha256": _WHEEL,
    "independently_expected_generation_digest": _GEN,
    "trusted_now_epoch": _NOW,
}


def _claims() -> dict[str, object]:
    return {
        "schema_version": "runner-mcp/signed-serving-witness/v1",
        "component_id": "runner-mcp",
        "host_digest": _HOST,
        "challenge": _CHALLENGE,
        "source_revision": _SOURCE,
        "wheel_sha256": _WHEEL,
        "generation_digest": _GEN,
        "observed_at": _NOW - 10,
        "expires_at": _NOW + 60,
        "roles": {
            role: {
                "source_revision": _SOURCE,
                "wheel_sha256": _WHEEL,
                "generation_digest": _GEN,
                "process_instance": f"{i + 1:064x}",
            }
            for i, role in enumerate(_ROLES)
        },
    }


def _check(
    claims: dict[str, object] | None = None,
    *,
    raw: bytes | None = None,
    expected_override: dict[str, object] | None = None,
    signature_tampered: bool = False,
) -> dict[str, object]:
    signer = Ed25519PrivateKey.generate()
    key = signer.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    body = raw if raw is not None else json.dumps(
        _claims() if claims is None else claims,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    signature = signer.sign(body)
    if signature_tampered:
        signature = b"x" * 64
    expected = dict(_EXPECTED)
    expected["independently_authorized_key_sha256"] = hashlib.sha256(key).hexdigest()
    if expected_override is not None:
        expected.update(expected_override)
    return signed_serving_witness_preflight(
        body, signature, key, **expected
    )


def test_signed_statement_match_still_does_not_claim_serving_identity() -> None:
    result = _check()
    assert result == {
        "schema_version": "runner-mcp/serving-witness-preflight/v1",
        "state": "signed_statement_consistent_offline",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("component_id", "runner-fabric"),
        ("host_digest", "f" * 64),
        ("challenge", "f" * 32),
        ("source_revision", "f" * 40),
        ("wheel_sha256", "f" * 64),
        ("generation_digest", "f" * 64),
        ("observed_at", _NOW + 1),
        ("expires_at", _NOW - 1),
        ("expires_at", _NOW + 400),
        ("schema_version", "runner-mcp/signed-serving-witness/v0"),
        ("roles", {}),
        ("roles", {"server": {"process_instance": "a" * 64}}),
    ],
)
def test_wrong_signed_statements_fail_closed(field: str, value: object) -> None:
    claims = _claims()
    claims[field] = value
    assert _check(claims)["state"] == "unverified"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("independently_expected_host_digest", "f" * 64),
        ("independently_expected_source_revision", "f" * 40),
        ("independently_expected_wheel_sha256", "f" * 64),
        ("independently_expected_generation_digest", "f" * 64),
        ("independently_expected_challenge", "f" * 32),
        ("independently_expected_roles", ("server", "watcher", "fourth")),
        ("trusted_now_epoch", _NOW + 400),
        ("trusted_now_epoch", True),
        ("independently_authorized_key_sha256", "f" * 64),
    ],
)
def test_independent_expectation_mismatch_denies(
    field: str, value: object
) -> None:
    assert _check(expected_override={field: value})["state"] == "unverified"


@pytest.mark.parametrize("fault", ["wrong_role_hash", "duplicate_process", "extra_role"])
def test_role_generation_mismatch_is_never_accepted(fault: str) -> None:
    claims = _claims()
    roles = claims["roles"]
    assert isinstance(roles, dict)
    if fault == "wrong_role_hash":
        roles["watcher"]["wheel_sha256"] = "f" * 64
    elif fault == "duplicate_process":
        roles["watcher"]["process_instance"] = roles["server"]["process_instance"]
    else:
        roles["unexpected"] = roles["server"]
    assert _check(claims)["state"] == "unverified"


def test_duplicate_or_noncanonical_signed_json_denied() -> None:
    canonical = json.dumps(_claims(), sort_keys=True, separators=(",", ":"))
    duplicate = canonical.replace(
        '"component_id":"runner-mcp"',
        '"component_id":"runner-mcp","component_id":"runner-mcp"',
    )
    assert _check(raw=duplicate.encode())["state"] == "unverified"
    assert _check(raw=json.dumps(_claims()).encode())["state"] == "unverified"


def test_bad_signature_and_oversized_payload_rejected() -> None:
    assert _check(signature_tampered=True)["state"] == "unverified"
    assert _check(raw=b"x" * (32 * 1024 + 1))["state"] == "unverified"


def test_a_signed_candidate_cannot_reuse_a_foreign_expected_nonce() -> None:
    assert _check(
        expected_override={"independently_expected_challenge": "0" * 32}
    )["active_build_provenance_verified"] is False
