"""Offline integratie: ondertekend Fabric-rooster + gedeelde volledige bundelcontrole.

De tijdelijke cryptografische sleutel en bytes zijn fictief. Deze tests voeren
geen downloads, bestanden, processtarts, installaties of servermutaties uit.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.fabric_release_assets import ReleaseAsset, inspect_exact_release
from runner_mcp.fabric_release_full_bundle import (
    CompleteBundleMismatch,
    check_complete_signed_fabric_bundle,
)
from runner_mcp.fabric_release_signed_roster import verify_signed_fabric_roster

COMMIT = "a" * 40
TAG = "fabric-update-bundle-" + COMMIT
RELEASE_ID = 87654321
PROJECT = "runner_fabric-1.0.0-py3-none-any.whl"
REQUIRED = ("BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py")


def _bodies(count: int = 33) -> dict[str, bytes]:
    wheel_names = [PROJECT] + [
        f"dependency_{i:03d}-1.0-py3-none-any.whl" for i in range(count - 5)
    ]
    bodies = {"BOOTSTRAP.py": b"synthetic-offline-bootstrap"}
    for i, name in enumerate(wheel_names):
        bodies[name] = f"synthetic-wheel-{i}".encode()
    manifest = {
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": COMMIT,
        "python": "3.12",
        "projectWheel": PROJECT,
        "wheelCount": len(wheel_names),
        "bootstrapSha256": hashlib.sha256(bodies["BOOTSTRAP.py"]).hexdigest(),
    }
    bodies["BUNDLE.json"] = json.dumps(manifest, sort_keys=True).encode()
    bodies["COMMIT_SHA"] = (COMMIT + "\n").encode()
    bodies["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n"
        for name in sorted([*wheel_names, "BOOTSTRAP.py"])
    ).encode()
    assert len(bodies) == count
    return bodies


def _inputs(bodies: dict[str, bytes]):
    entries = [
        {
            "name": name,
            "asset_id": i + 100,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for i, (name, data) in enumerate(sorted(bodies.items()))
    ]
    roster = {
        "schema_version": "runner-fabric/signed-release-roster/v1",
        "repository": "Blacksp1d3r/Runner-Fabric",
        "commit": COMMIT,
        "tag": TAG,
        "release_id": RELEASE_ID,
        "files": entries,
    }
    raw = json.dumps(roster, sort_keys=True, separators=(",", ":")).encode()
    private = Ed25519PrivateKey.generate()
    pub = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    signed = verify_signed_fabric_roster(
        signed_document=raw,
        signature=private.sign(raw),
        public_key=pub,
        independently_trusted_key_sha256=hashlib.sha256(pub).hexdigest(),
        expected_commit=COMMIT,
        expected_release_id=RELEASE_ID,
    )
    observed = inspect_exact_release(
        COMMIT,
        {
            "id": RELEASE_ID,
            "tag_name": TAG,
            "target_commitish": COMMIT,
            "draft": False,
            "prerelease": True,
            "assets": [
                {
                    "name": row["name"], "id": row["asset_id"],
                    "size": row["bytes"], "digest": "sha256:" + row["sha256"],
                } for row in entries
            ],
        },
        {
            "ref": "refs/tags/" + TAG,
            "object": {"type": "commit", "sha": COMMIT},
        },
    )
    return signed, observed


def _reject(bodies, *, pin_current=True):
    good = bodies if pin_current else _bodies()
    signed, observed = _inputs(good)
    with pytest.raises(
        CompleteBundleMismatch, match="^fabric_release_full_bundle_unqualified$"
    ):
        check_complete_signed_fabric_bundle(signed, observed, bodies)


@pytest.mark.parametrize("count", [5, 33, 160])
def test_five_to_160_assets_reuse_existing_bundle_semantics(count):
    bodies = _bodies(count)
    signed, observed = _inputs(bodies)
    assert check_complete_signed_fabric_bundle(signed, observed, bodies) == {
        "inspection": "bundle_consistency_only",
        "asset_count": count,
        "wheel_count": count - 4,
        "operator_signer_authority_attested": False,
        "wheel_metadata_verified": False,
        "local_custody_verified": False,
        "download_performed": False,
        "mutation_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }


@pytest.mark.parametrize("field,bad", [
    ("schemaVersion", "v0"),
    ("commitSha", "b" * 40),
    ("python", "3.11"),
    ("projectWheel", "dependency_000-1.0-py3-none-any.whl"),
    ("wheelCount", 11),
    ("wheelCount", True),
    ("bootstrapSha256", "f" * 64),
])
def test_bad_manifest_refused_even_when_resigned_and_rehashed(field, bad):
    bodies = _bodies()
    manifest = json.loads(bodies["BUNDLE.json"].decode())
    manifest[field] = bad
    bodies["BUNDLE.json"] = json.dumps(manifest).encode()
    _reject(bodies)


@pytest.mark.parametrize("bad", [
    b"bad-json", b"\xff", b"[]",
    b'{"schemaVersion":1,"schemaVersion":2}',
    b"{" + b" " * (32 * 1024 + 1),
])
def test_bad_or_duplicate_manifest_refused_with_valid_asset_hashes(bad):
    bodies = _bodies()
    bodies["BUNDLE.json"] = bad
    _reject(bodies)


@pytest.mark.parametrize("bad", [
    b"b" * 40, b"b" * 40 + b"\n",
    (COMMIT + " ").encode(), (COMMIT + "\n\n").encode(),
])
def test_wrong_commit_sha_file_refused_even_if_resigned(bad):
    bodies = _bodies()
    bodies["COMMIT_SHA"] = bad
    _reject(bodies)


@pytest.mark.parametrize("bad", [
    b"missing",
    b"f" * 64 + b"  BOOTSTRAP.py\n",
    b"f" * 64 + b"  ../escape.whl\n",
    b"f" * 64 + b"  BOOTSTRAP.py\n" + b"f" * 64 + b"  BOOTSTRAP.py\n",
])
def test_wrong_sha256sums_refused_even_when_resigned(bad):
    bodies = _bodies()
    bodies["SHA256SUMS"] = bad
    _reject(bodies)


@pytest.mark.parametrize("target", [
    "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py",
    PROJECT, "dependency_000-1.0-py3-none-any.whl",
])
def test_changed_downloaded_bytes_do_not_match_independent_signed_pins(target):
    bodies = _bodies()
    bodies[target] = b"altered-after-independent-signing"
    _reject(bodies, pin_current=False)


def test_missing_extra_or_nonbytes_downloaded_asset_denied():
    for mode in ("missing", "extra", "nonbytes"):
        bodies = _bodies()
        if mode == "missing":
            del bodies["dependency_000-1.0-py3-none-any.whl"]
        elif mode == "extra":
            bodies["unexpected.whl"] = b"unknown"
        else:
            bodies[PROJECT] = bytearray(b"not-bytes")  # type: ignore[assignment]
        _reject(bodies, pin_current=False)


@pytest.mark.parametrize("change", [
    {"asset_id": 9999}, {"bytes": 1}, {"sha256": "f" * 64},
    {"name": "foreign.whl"},
])
def test_matching_source_tag_but_modified_github_metadata_fails(change):
    bodies = _bodies()
    signed, observed = _inputs(bodies)
    edited = ReleaseAsset(**{**vars(observed.files[0]), **change})
    observed = replace(observed, files=(edited, *observed.files[1:]))
    with pytest.raises(CompleteBundleMismatch):
        check_complete_signed_fabric_bundle(signed, observed, bodies)


def test_complete_bundle_memory_verifier_has_no_network_or_mutation():
    module = (
        Path(__file__).resolve().parents[1]
        / "src/runner_mcp/fabric_release_full_bundle.py"
    )
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imports.intersection({"os", "shutil", "subprocess", "urllib", "socket"})
    invoked = {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not invoked.intersection({
        "open", "write_bytes", "mkdir", "stage_local_bundle", "start_local",
        "start", "rollback", "fetch_pinned_asset_bytes",
    })
