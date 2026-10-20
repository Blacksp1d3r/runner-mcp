"""Offline signed serving-generation witness statement comparator (#669).

The trusted authority must separately validate actual host/process observation,
key custody, rollback role completeness, and one-time challenge issuance.
A signature checked here proves only integrity/consistency of that statement.
Never expose source revision, wheel SHA or active provenance from this preflight.
"""

from __future__ import annotations

import hashlib
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_SHA = re.compile(r"^[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_NONCE = re.compile(r"^[0-9a-f]{32}$")
_ROLE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_SCHEMA = "runner-mcp/signed-serving-witness/v1"
_MAX_BODY = 32 * 1024
_MAX_ROLES = 16
_MAX_TTL = 300


def _unverified() -> dict[str, object]:
    return {
        "schema_version": "runner-mcp/serving-witness-preflight/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate signed witness field")
        result[key] = value
    return result


def signed_serving_witness_preflight(
    body: bytes,
    signature: bytes,
    public_key: bytes,
    *,
    independently_authorized_key_sha256: str,
    independently_expected_host_digest: str,
    independently_expected_roles: tuple[str, ...],
    independently_expected_challenge: str,
    independently_expected_source_revision: str,
    independently_expected_loaded_version: str,
    independently_expected_wheel_sha256: str,
    independently_expected_generation_digest: str,
    trusted_now_epoch: int,
) -> dict[str, object]:
    """Compare a signed claim against independent expected values, without trust issuance.

    Even on a successful signed match, the caller must independently establish
    that the signer observed the currently loaded process on the intended
    physical host, that the nonce was actually issued once to this observer,
    and that the observed generation remains current through client ACK.
    """
    unavailable = _unverified()
    try:
        if (
            not isinstance(body, bytes)
            or not 0 < len(body) <= _MAX_BODY
            or not isinstance(signature, bytes)
            or len(signature) != 64
            or not isinstance(public_key, bytes)
            or len(public_key) != 32
            or not isinstance(independently_authorized_key_sha256, str)
            or _SHA.fullmatch(independently_authorized_key_sha256) is None
            or not isinstance(independently_expected_host_digest, str)
            or _SHA.fullmatch(independently_expected_host_digest) is None
            or not isinstance(independently_expected_source_revision, str)
            or _REV.fullmatch(independently_expected_source_revision) is None
            or not isinstance(independently_expected_loaded_version, str)
            or _VERSION.fullmatch(independently_expected_loaded_version) is None
            or not isinstance(independently_expected_wheel_sha256, str)
            or _SHA.fullmatch(independently_expected_wheel_sha256) is None
            or not isinstance(independently_expected_generation_digest, str)
            or _SHA.fullmatch(independently_expected_generation_digest) is None
            or not isinstance(independently_expected_challenge, str)
            or _NONCE.fullmatch(independently_expected_challenge) is None
            or not isinstance(independently_expected_roles, tuple)
            or not 1 <= len(independently_expected_roles) <= _MAX_ROLES
            or not all(
                isinstance(role, str) and _ROLE.fullmatch(role) is not None
                for role in independently_expected_roles
            )
            or len(set(independently_expected_roles)) != len(independently_expected_roles)
            or type(trusted_now_epoch) is not int
            or trusted_now_epoch < 0
        ):
            return unavailable
        if hashlib.sha256(public_key).hexdigest() != independently_authorized_key_sha256:
            return unavailable
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, body)
        parsed = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_keys)
        if not isinstance(parsed, dict) or set(parsed) != {
            "schema_version",
            "component_id",
            "host_digest",
            "challenge",
            "source_revision",
            "loaded_version",
            "wheel_sha256",
            "generation_digest",
            "observed_at",
            "expires_at",
            "roles",
        }:
            return unavailable
        # Require canonical serialized input: reject alternate spellings,
        # non-ASCII text, ambiguous Unicode and non-standard JSON numbers.
        if json.dumps(
            parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii") != body:
            return unavailable
        if (
            parsed["schema_version"] != _SCHEMA
            or parsed["component_id"] != "runner-mcp"
            or parsed["host_digest"] != independently_expected_host_digest
            or parsed["challenge"] != independently_expected_challenge
            or parsed["source_revision"] != independently_expected_source_revision
            or parsed["loaded_version"] != independently_expected_loaded_version
            or parsed["wheel_sha256"] != independently_expected_wheel_sha256
            or parsed["generation_digest"] != independently_expected_generation_digest
        ):
            return unavailable
        observed, expires = parsed["observed_at"], parsed["expires_at"]
        if (
            type(observed) is not int
            or type(expires) is not int
            or not 0 <= observed <= trusted_now_epoch <= expires
            or expires <= observed
            or expires - observed > _MAX_TTL
        ):
            return unavailable
        roles = parsed["roles"]
        if not isinstance(roles, dict) or set(roles) != set(independently_expected_roles):
            return unavailable
        process_instances: set[str] = set()
        for role in independently_expected_roles:
            item = roles[role]
            if not isinstance(item, dict) or set(item) != {
                "source_revision",
                "loaded_version",
                "wheel_sha256",
                "generation_digest",
                "process_instance",
            }:
                return unavailable
            process = item["process_instance"]
            if (
                item["source_revision"] != independently_expected_source_revision
                or item["loaded_version"] != independently_expected_loaded_version
                or item["wheel_sha256"] != independently_expected_wheel_sha256
                or item["generation_digest"] != independently_expected_generation_digest
                or not isinstance(process, str)
                or _SHA.fullmatch(process) is None
                or process in process_instances
            ):
                return unavailable
            process_instances.add(process)
    except (InvalidSignature, UnicodeError, TypeError, ValueError, RecursionError):
        return unavailable
    # This is an independently pinned *signed statement match*, NOT live
    # process observation and not evidence of an unrevoked authorized observer.
    return {**unavailable, "state": "signed_statement_consistent_offline"}


def signed_six_role_process_pin_preflight(
    body: bytes,
    signature: bytes,
    public_key: bytes,
    *,
    independently_expected_process_instances: dict[str, str],
    independently_authorized_key_sha256: str,
    independently_expected_host_digest: str,
    independently_expected_roles: tuple[str, ...],
    independently_expected_challenge: str,
    independently_expected_source_revision: str,
    independently_expected_loaded_version: str,
    independently_expected_wheel_sha256: str,
    independently_expected_generation_digest: str,
    trusted_now_epoch: int,
) -> dict[str, object]:
    """Strict offline six-role statement match against independent process pins.

    Caller-supplied role and process hashes MUST come from an independent
    correct-host identity authority, not from the same signed statement. This
    function issues no trust, proves no loaded code and never enables update.
    The generic statement comparator retains its original test contract.
    """
    unavailable = {
        **_unverified(),
        "schema_version": "runner-mcp/six-role-process-pin-preflight/v1",
    }
    if (
        not isinstance(independently_expected_roles, tuple)
        or len(independently_expected_roles) != 6
        or type(independently_expected_process_instances) is not dict
        or not all(
            type(role) is str and _ROLE.fullmatch(role) is not None
            for role in independently_expected_roles
        )
    ):
        return unavailable
    expected_names = set(independently_expected_roles)
    if (
        len(expected_names) != 6
        or set(independently_expected_process_instances) != expected_names
        or not all(
            type(independently_expected_process_instances[name]) is str
            and _SHA.fullmatch(independently_expected_process_instances[name]) is not None
            for name in expected_names
        )
        or len(set(independently_expected_process_instances.values())) != 6
    ):
        return unavailable
    compared = signed_serving_witness_preflight(
        body,
        signature,
        public_key,
        independently_authorized_key_sha256=independently_authorized_key_sha256,
        independently_expected_host_digest=independently_expected_host_digest,
        independently_expected_roles=independently_expected_roles,
        independently_expected_challenge=independently_expected_challenge,
        independently_expected_source_revision=independently_expected_source_revision,
        independently_expected_loaded_version=independently_expected_loaded_version,
        independently_expected_wheel_sha256=independently_expected_wheel_sha256,
        independently_expected_generation_digest=independently_expected_generation_digest,
        trusted_now_epoch=trusted_now_epoch,
    )
    if compared["state"] != "signed_statement_consistent_offline":
        return unavailable
    try:
        # Only parse a statement after signature, canonical JSON, six exact role
        # names, independent signer/source/wheel pins, freshness and unique
        # source-supplied process IDs were already checked above.
        claims = json.loads(body.decode("ascii"), object_pairs_hook=_unique_keys)
        roles = claims["roles"]
        if not isinstance(roles, dict) or any(
            roles[name]["process_instance"] != independently_expected_process_instances[name]
            for name in expected_names
        ):
            return unavailable
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return unavailable
    return {
        **unavailable,
        "state": "six_role_process_pins_consistent_offline",
    }
