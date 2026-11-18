from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.offline_receipt_writer import write_offline_receipt_candidate
from runner_mcp.offline_signed_evidence import offline_signed_evidence_preflight

_REV = "a" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path):
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"wheel bytes")
    wheel_sha = _sha(wheel.read_bytes())
    generation = tmp_path / f"generation-{_REV}-{wheel_sha}"
    generation.mkdir(mode=0o700)
    package = generation / "runner_mcp"
    package.mkdir()
    (package / "module.py").write_bytes(b"module content")
    receipt = tmp_path / "receipt.json"
    assert write_offline_receipt_candidate(receipt, {
        "schema_version": "runner-mcp/offline-artifact-receipt/v1",
        "source_revision": _REV,
        "wheel_sha256": wheel_sha,
        "modules": {"module.py": _sha(b"module content")},
    })
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(json.dumps({
        "schema_version": "runner-mcp/builder-manifest/v1",
        "source_revision": _REV,
        "distribution_version": "0.1.16",
        "wheel_sha256": wheel_sha,
        "interface_schema_digest": "b" * 64,
    }, sort_keys=True).encode("utf-8"))
    private = Ed25519PrivateKey.generate()
    raw_key = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_key = tmp_path / "key.raw"
    public_key.write_bytes(raw_key)
    signature = tmp_path / "sig.raw"
    signature.write_bytes(private.sign(manifest.read_bytes()))
    return (
        manifest, receipt, wheel, package, generation, _sha(manifest.read_bytes()),
        public_key, signature, _sha(raw_key),
    )


def test_signed_candidate_match_still_refuses_active_attestation(tmp_path: Path):
    result = offline_signed_evidence_preflight(*_fixture(tmp_path))
    assert result["state"] == "offline_signed_candidate_match"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


@pytest.mark.parametrize(
    "tamper",
    ["manifest", "receipt", "wheel", "module", "signature", "public_key", "key_pin"],
)
def test_tampered_evidence_fails_closed(tmp_path: Path, tamper: str):
    values = list(_fixture(tmp_path))
    if tamper == "manifest":
        values[0].write_bytes(b"changed manifest")
    elif tamper == "receipt":
        values[1].write_text("{}", encoding="utf-8")
    elif tamper == "wheel":
        values[2].write_bytes(b"changed wheel")
    elif tamper == "module":
        (values[3] / "module.py").write_bytes(b"changed module")
    elif tamper == "signature":
        values[7].write_bytes(b"malformed signature")
    elif tamper == "public_key":
        values[6].write_bytes(b"untrusted key")
    else:
        values[8] = "f" * 64
    result = offline_signed_evidence_preflight(*values)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False


def test_wrong_independent_manifest_pin_rejected(tmp_path: Path):
    values = list(_fixture(tmp_path))
    values[5] = "f" * 64
    assert offline_signed_evidence_preflight(*values)["state"] == "unverified"
