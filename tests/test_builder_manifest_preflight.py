from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from runner_mcp.builder_manifest_preflight import pinned_builder_manifest_preflight


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inputs(tmp_path: Path) -> tuple[Path, Path, str]:
    wheel = tmp_path / "package.whl"
    wheel.write_bytes(b"candidate wheel")
    manifest = tmp_path / "manifest.json"
    payload = {
        "schema_version": "runner-mcp/builder-manifest/v1",
        "source_revision": "a" * 40,
        "distribution_version": "0.1.12",
        "wheel_sha256": _sha(wheel.read_bytes()),
        "interface_schema_digest": "b" * 64,
    }
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return manifest, wheel, _sha(manifest.read_bytes())


def test_pinned_manifest_match_never_attests_active_process(tmp_path: Path):
    manifest, wheel, trusted_digest = _inputs(tmp_path)
    answer = pinned_builder_manifest_preflight(manifest, wheel, trusted_digest)
    assert answer["state"] == "offline_manifest_and_wheel_match"
    assert answer["active_build_provenance_verified"] is False
    assert answer["source_revision"] is None
    assert answer["artifact_digest"] is None


def test_rejects_modified_manifest_even_when_declared_wheel_is_correct(tmp_path: Path):
    manifest, wheel, trusted_digest = _inputs(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["source_revision"] = "c" * 40
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, trusted_digest)["state"]
        == "unverified"
    )


def test_rejects_modified_wheel_even_when_manifest_pin_is_valid(tmp_path: Path):
    manifest, wheel, trusted_digest = _inputs(tmp_path)
    wheel.write_bytes(b"new wheel same version")
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, trusted_digest)["state"]
        == "unverified"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": "wrong"},
        {"distribution_version": "not-a-version"},
        {"source_revision": "not-a-revision"},
        {"interface_schema_digest": "nope"},
        {"unexpected": "field"},
    ],
)
def test_invalid_manifest_fields_are_fail_closed(tmp_path: Path, mutation: dict[str, str]):
    manifest, wheel, _ = _inputs(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value.update(mutation)
    manifest.write_text(json.dumps(value), encoding="utf-8")
    digest = _sha(manifest.read_bytes())
    assert pinned_builder_manifest_preflight(manifest, wheel, digest)["state"] == "unverified"


@pytest.mark.parametrize("name", ["manifest", "wheel"])
def test_symlink_artifacts_are_fail_closed(tmp_path: Path, name: str):
    manifest, wheel, trusted_digest = _inputs(tmp_path)
    victim = manifest if name == "manifest" else wheel
    renamed = tmp_path / "original"
    victim.rename(renamed)
    victim.symlink_to(renamed)
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, trusted_digest)["state"]
        == "unverified"
    )


def test_rejects_publicly_writable_manifest(tmp_path: Path):
    manifest, wheel, trusted_digest = _inputs(tmp_path)
    manifest.chmod(0o666)
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, trusted_digest)["state"]
        == "unverified"
    )


def test_no_trust_anchor_means_no_valid_identity(tmp_path: Path):
    manifest, wheel, _ = _inputs(tmp_path)
    assert pinned_builder_manifest_preflight(manifest, wheel, "")["state"] == "unverified"


def test_duplicate_manifest_json_key_rejected(tmp_path: Path):
    manifest, wheel, _ = _inputs(tmp_path)
    raw = manifest.read_text(encoding="utf-8")
    duplicate = '"source_revision": "' + ("c" * 40) + '", "source_revision":'
    manifest.write_text(raw.replace('"source_revision":', duplicate), encoding="utf-8")
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, _sha(manifest.read_bytes()))[
            "state"
        ]
        == "unverified"
    )


def test_excessive_manifest_nesting_rejected(tmp_path: Path):
    manifest, wheel, _ = _inputs(tmp_path)
    manifest.write_text("[" * 1500 + "0" + "]" * 1500, encoding="utf-8")
    assert (
        pinned_builder_manifest_preflight(manifest, wheel, _sha(manifest.read_bytes()))[
            "state"
        ]
        == "unverified"
    )
