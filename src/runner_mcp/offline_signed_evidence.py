"""Source-only offline signed evidence consistency preflight.

Caller MUST independently obtain and authorize both builder manifest SHA pin and
signer key fingerprint. A caller-supplied hash and key is NOT independent trust.
Even perfect signatures and matching candidate bytes cannot prove loaded code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runner_mcp.detached_builder_signature import detached_builder_signature_preflight
from runner_mcp.offline_evidence_chain import offline_evidence_chain_preflight
from runner_mcp.offline_installed_record_preflight import offline_installed_record_preflight


def offline_signed_evidence_preflight(
    manifest: Path,
    receipt: Path,
    wheel: Path,
    installed_package: Path,
    generation: Path,
    manifest_sha256_pin: str,
    signer_public_key: Path,
    detached_signature: Path,
    signer_key_sha256_pin: str,
) -> dict[str, object]:
    """Fail closed when either the signature or the offline candidate chain fails."""
    result: dict[str, object] = {
        "schema_version": "runner-mcp/offline-signed-evidence/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    signed = detached_builder_signature_preflight(
        manifest, signer_public_key, detached_signature, signer_key_sha256_pin
    )
    if signed["state"] != "offline_signature_match":
        return result
    chain = offline_evidence_chain_preflight(
        manifest, receipt, wheel, installed_package, generation, manifest_sha256_pin
    )
    if chain["state"] != "offline_candidate_chain_match":
        return result
    # No publisher custody, file sealing, process import witness, or operator
    # signer's approval is established here. Never expose source or digest.
    return {**result, "state": "offline_signed_candidate_match"}



def offline_signed_installed_record_preflight(
    manifest: Path,
    receipt: Path,
    wheel: Path,
    installed_package: Path,
    generation: Path,
    manifest_sha256_pin: str,
    signer_public_key: Path,
    detached_signature: Path,
    signer_key_sha256_pin: str,
) -> dict[str, object]:
    """Compose existing signature/chain checks with the installed wheel RECORD.

    Even full offline agreement is candidate evidence ONLY. This function
    cannot independently authenticate pin custody or loaded processes.
    """
    unavailable: dict[str, object] = {
        "schema_version": "runner-mcp/offline-signed-installed-record/v1",
        "state": "unverified",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }
    signed = offline_signed_evidence_preflight(
        manifest, receipt, wheel, installed_package, generation,
        manifest_sha256_pin, signer_public_key, detached_signature, signer_key_sha256_pin,
    )
    if signed["state"] != "offline_signed_candidate_match":
        return unavailable
    try:
        if not isinstance(manifest_sha256_pin, str) or len(manifest_sha256_pin) != 64:
            return unavailable
        raw = manifest.read_bytes()
        if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != manifest_sha256_pin:
            return unavailable
        candidate = json.loads(raw)
        if not isinstance(candidate, dict):
            return unavailable
        wheel_digest = candidate.get("wheel_sha256")
        checked = offline_installed_record_preflight(
            wheel, installed_package, wheel_digest
        )
        if checked["state"] != "offline_installed_record_match":
            return unavailable
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != manifest_sha256_pin:
            return unavailable
    except (OSError, UnicodeError, TypeError, ValueError):
        return unavailable
    return {**unavailable, "state": "offline_signed_installed_record_match"}
