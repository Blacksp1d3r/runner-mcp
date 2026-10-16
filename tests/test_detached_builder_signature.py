from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.detached_builder_signature import detached_builder_signature_preflight


def _fixture(tmp_path: Path):
    private = Ed25519PrivateKey.generate()
    public_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(b'{"source_revision":"a synthetic test value"}')
    public_key = tmp_path / "public-key.raw"
    public_key.write_bytes(public_bytes)
    signature = tmp_path / "signature.raw"
    signature.write_bytes(private.sign(manifest.read_bytes()))
    digest = hashlib.sha256(public_bytes).hexdigest()
    return manifest, public_key, signature, digest


def _state(inputs) -> dict[str, object]:
    return detached_builder_signature_preflight(*inputs)


def test_valid_signature_is_offline_only(tmp_path: Path):
    state = _state(_fixture(tmp_path))
    assert state["state"] == "offline_signature_match"
    assert state["active_build_provenance_verified"] is False
    assert state["source_revision"] is None
    assert state["artifact_digest"] is None


def test_mutated_manifest_fails(tmp_path: Path):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    manifest.write_bytes(b"changed document")
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"


def test_wrong_public_key_pin_fails(tmp_path: Path):
    manifest, public_key, signature, _digest = _fixture(tmp_path)
    assert _state((manifest, public_key, signature, "f" * 64))["state"] == "unverified"


@pytest.mark.parametrize("target", ["manifest", "public", "signature"])
def test_symlinked_evidence_fails(tmp_path: Path, target: str):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    selected = {"manifest": manifest, "public": public_key, "signature": signature}[target]
    original = tmp_path / (target + ".original")
    selected.rename(original)
    selected.symlink_to(original)
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"


@pytest.mark.parametrize("target", ["manifest", "public", "signature"])
def test_group_writable_evidence_fails(tmp_path: Path, target: str):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    selected = {"manifest": manifest, "public": public_key, "signature": signature}[target]
    selected.chmod(0o664)
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"


def test_wrong_length_signature_fails(tmp_path: Path):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    signature.write_bytes(b"short")
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"


def test_signature_by_different_key_fails(tmp_path: Path):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    other = Ed25519PrivateKey.generate()
    signature.write_bytes(other.sign(manifest.read_bytes()))
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"


def test_missing_expected_pin_fails(tmp_path: Path):
    manifest, public_key, signature, _ = _fixture(tmp_path)
    assert _state((manifest, public_key, signature, ""))["state"] == "unverified"


def test_manifest_over_maximum_fails(tmp_path: Path):
    manifest, public_key, signature, digest = _fixture(tmp_path)
    manifest.write_bytes(b"x" * 65537)
    assert _state((manifest, public_key, signature, digest))["state"] == "unverified"
