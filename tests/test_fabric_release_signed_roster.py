"""Synthetische regressies voor generieke, uitsluitend offline Release-handtekeningen.

De tests maken een tijdelijke Ed25519-sleutel in geheugen. Ze raken geen
servers, API's, secrets, updatebestanden, ingestelde ondertekenaars of services.
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
from runner_mcp.fabric_release_signed_roster import (
    SignedFabricRosterUnqualified,
    compare_signed_fabric_roster,
    verify_signed_fabric_roster,
)

_COMMIT = "a" * 40
_OTHER_COMMIT = "b" * 40
_RELEASE_ID = 987654
_TAG = "fabric-update-bundle-" + _COMMIT
_SCHEMA = "runner-fabric/signed-release-roster/v1"
_FILES = [
    "BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py",
    "runner_fabric-0.0.1-py3-none-any.whl",
]


def _document(count: int = 33) -> dict:
    names = _FILES + [
        f"dependency_{i:02d}-1.0-py3-none-any.whl"
        for i in range(count - len(_FILES))
    ]
    return {
        "schema_version": _SCHEMA,
        "repository": "Blacksp1d3r/Runner-Fabric",
        "commit": _COMMIT,
        "tag": _TAG,
        "release_id": _RELEASE_ID,
        "files": [
            {
                "name": name, "asset_id": 101 + index, "bytes": 17 + index,
                "sha256": hashlib.sha256(name.encode()).hexdigest(),
            }
            for index, name in enumerate(names)
        ],
    }


def _signed(*, doc: dict | None = None):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    raw = json.dumps(doc or _document(), sort_keys=True, separators=(",", ":")).encode()
    args = {
        "signed_document": raw,
        "signature": private.sign(raw),
        "public_key": public,
        "independently_trusted_key_sha256": hashlib.sha256(public).hexdigest(),
        "expected_commit": _COMMIT,
        "expected_release_id": _RELEASE_ID,
    }
    return private, args


def _verify(args):
    return verify_signed_fabric_roster(**args)


def _observed(doc):
    return inspect_exact_release(
        _COMMIT,
        {
            "id": doc["release_id"], "tag_name": doc["tag"],
            "target_commitish": doc["commit"], "draft": False, "prerelease": True,
            "assets": [
                {
                    "id": item["asset_id"], "name": item["name"],
                    "size": item["bytes"], "digest": "sha256:" + item["sha256"],
                }
                for item in doc["files"]
            ],
        },
        {
            "ref": "refs/tags/" + _TAG,
            "object": {"type": "commit", "sha": _COMMIT},
        },
    )


@pytest.mark.parametrize("count", [5, 33, 160])
def test_pinned_valid_release_matches_same_git_metadata_without_io(count):
    document = _document(count)
    _, args = _signed(doc=document)
    signed = _verify(args)
    observed = _observed(document)
    assert signed.commit == _COMMIT
    assert signed.release_id == _RELEASE_ID
    result = compare_signed_fabric_roster(signed, observed)
    assert result == {
        "comparison": "match_only",
        "asset_count": count,
        "operator_signer_authority_attested": False,
        "download_performed": False,
        "install_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }


@pytest.mark.parametrize("bad", [
    "wrong_signer", "wrong_hash", "modified_document", "wrong_signature_size",
    "invalid_public_key_size", "unsigned", "upper_key_hash",
])
def test_untrusted_signature_or_key_refused(bad):
    private, args = _signed()
    if bad == "wrong_signer":
        args["signature"] = Ed25519PrivateKey.generate().sign(args["signed_document"])
    elif bad == "wrong_hash":
        args["independently_trusted_key_sha256"] = "f" * 64
    elif bad == "modified_document":
        args["signed_document"] += b" "
    elif bad == "wrong_signature_size":
        args["signature"] = b"x" * 63
    elif bad == "invalid_public_key_size":
        args["public_key"] = b"x" * 33
    elif bad == "unsigned":
        args["signature"] = None
    else:
        args["independently_trusted_key_sha256"] = (
            args["independently_trusted_key_sha256"].upper()
        )
    with pytest.raises(
        SignedFabricRosterUnqualified, match="^fabric_signed_release_roster_unqualified$"
    ):
        _verify(args)
    assert private is not None


@pytest.mark.parametrize("field,value", [
    ("expected_commit", _OTHER_COMMIT),
    ("expected_commit", "A" * 40),
    ("expected_commit", None),
    ("expected_release_id", _RELEASE_ID + 1),
    ("expected_release_id", True),
    ("expected_release_id", 0),
])
def test_caller_pins_must_be_exact_independent_authority(field, value):
    _, args = _signed()
    args[field] = value
    with pytest.raises(SignedFabricRosterUnqualified):
        _verify(args)


@pytest.mark.parametrize("field,value", [
    ("schema_version", "runner-fabric/independent-q7-release-roster/v1"),
    ("schema_version", "runner-fabric/signed-release-roster/v2"),
    ("repository", "Blacksp1d3r/runner-mcp"),
    ("commit", _OTHER_COMMIT),
    ("tag", "fabric-q7-bundle-" + _COMMIT),
    ("tag", "fabric-update-bundle-" + _OTHER_COMMIT),
    ("release_id", _RELEASE_ID + 1),
    ("release_id", True),
    ("release_id", "987654"),
])
def test_even_validly_signed_wrong_policy_document_fails(field, value):
    doc = _document()
    doc[field] = value
    _, args = _signed(doc=doc)
    with pytest.raises(SignedFabricRosterUnqualified):
        _verify(args)


@pytest.mark.parametrize("issue", [
    "duplicate_file", "duplicate_id", "missing_file", "extra_unknown_file",
    "path_traversal", "bad_sha", "overlarge_file", "zero_file", "boolean_size",
    "boolean_id", "two_project_wheels", "missing_project_wheel", "161_assets",
    "four_assets", "asset_extra_key", "asset_missing_key",
])
def test_signed_invalid_asset_rosters_refused(issue):
    doc = _document()
    first = doc["files"][0]
    if issue == "duplicate_file":
        doc["files"][1]["name"] = first["name"]
    elif issue == "duplicate_id":
        doc["files"][1]["asset_id"] = first["asset_id"]
    elif issue == "missing_file":
        doc["files"] = [row for row in doc["files"] if row["name"] != "BUNDLE.json"]
    elif issue == "extra_unknown_file":
        doc["files"][5]["name"] = "README.md"
    elif issue == "path_traversal":
        doc["files"][5]["name"] = "../../escape.whl"
    elif issue == "bad_sha":
        first["sha256"] = "g" * 64
    elif issue == "overlarge_file":
        first["bytes"] = 64 * 1024 * 1024 + 1
    elif issue == "zero_file":
        first["bytes"] = 0
    elif issue == "boolean_size":
        first["bytes"] = True
    elif issue == "boolean_id":
        first["asset_id"] = True
    elif issue == "two_project_wheels":
        doc["files"][5]["name"] = "runner_fabric-2.0-py3-none-any.whl"
    elif issue == "missing_project_wheel":
        doc["files"][4]["name"] = "not_fabric-1.0-py3-none-any.whl"
    elif issue == "161_assets":
        doc = _document(161)
    elif issue == "four_assets":
        doc = _document(5)
        doc["files"].pop()
    elif issue == "asset_extra_key":
        first["source_url"] = "https://not-trusted.invalid"
    else:
        first.pop("sha256")
    _, args = _signed(doc=doc)
    with pytest.raises(SignedFabricRosterUnqualified):
        _verify(args)


def test_duplicate_signed_json_key_and_nonjson_are_refused():
    private, args = _signed()
    raw = args["signed_document"].replace(
        b'"commit":', b'"commit":"tampered","commit":', 1
    )
    args["signed_document"] = raw
    args["signature"] = private.sign(raw)
    with pytest.raises(SignedFabricRosterUnqualified):
        _verify(args)
    for invalid in (b"{", b"[]", b"\xff", b"x" * (64 * 1024 + 1)):
        args["signed_document"] = invalid
        args["signature"] = private.sign(invalid)
        with pytest.raises(SignedFabricRosterUnqualified):
            _verify(args)


@pytest.mark.parametrize("change", [
    {"asset_id": 99}, {"bytes": 1}, {"sha256": "f" * 64},
    {"name": "wrong.whl"},
])
def test_same_commit_and_release_id_do_not_hide_modified_github_asset(change):
    doc = _document()
    _, args = _signed(doc=doc)
    signed = _verify(args)
    actual = _observed(doc)
    modified = {**vars(actual.files[0]), **change}
    new_files = (ReleaseAsset(**modified),) + actual.files[1:]
    with pytest.raises(SignedFabricRosterUnqualified):
        compare_signed_fabric_roster(signed, replace(actual, files=new_files))


@pytest.mark.parametrize("field,value", [
    ("release_id", _RELEASE_ID + 1),
    ("commit", _OTHER_COMMIT),
    ("project_wheel", "missing.whl"),
])
def test_observed_release_identity_mismatch_refused(field, value):
    _, args = _signed()
    signed = _verify(args)
    actual = replace(_observed(_document()), **{field: value})
    with pytest.raises(SignedFabricRosterUnqualified):
        compare_signed_fabric_roster(signed, actual)


def test_no_network_disk_process_or_update_authority_in_pure_module():
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src/runner_mcp/fabric_release_signed_roster.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = [
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.Import) for alias in node.names
    ]
    assert not ({"os", "subprocess", "socket", "urllib", "requests", "shutil"} & set(imports))
    calls = [
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert not ({"start", "start_local", "stage_local_bundle", "rollback",
                 "fetch_pinned_asset_bytes", "write_bytes", "mkdir", "open"} & set(calls))
    assert "fabric-q7-bundle-" not in source_path.read_text(encoding="utf-8")
