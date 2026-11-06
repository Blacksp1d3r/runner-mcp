"""Synthetic ZIP wheelhouse gate: source-only, no trusted remote bytes or installation."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import stat
import warnings
import zipfile
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.fabric_release_assets import ReleaseAdmission, ReleaseAsset, inspect_exact_release
from runner_mcp.fabric_release_independent_roster import PinnedReleaseAsset, PinnedReleaseRoster
from runner_mcp.fabric_release_signed_roster import verify_signed_fabric_roster
from runner_mcp.fabric_release_wheelhouse import (
    WheelhouseUnqualified,
    verify_pinned_q7_wheelhouse,
    verify_signed_fabric_wheelhouse,
)

COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
PROJECT = "runner_fabric-1.2.3-py3-none-any.whl"
WHEELS = [PROJECT, *(f"dependency_{i:02d}-1.0-py3-none-any.whl" for i in range(28))]


def _wheel(name: str, *, defect: str | None = None) -> bytes:
    package, version, *_ = name.split("-")
    stem = f"{package}-{version}.dist-info/"
    members = {
        f"{package}/__init__.py": b"__version__='x'\n",
        stem + "METADATA": (
            f"Metadata-Version: 2.3\nName: "
            f"{'wrong-name' if defect == 'wrong_metadata' else package}\n"
            f"Version: {version}\n\n"
        ).encode(),
        stem + "WHEEL": b"Wheel-Version: 1.0\nGenerator: synthetic\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n",
    }
    if defect == "traversal":
        members["../evil.py"] = b"x"
    if defect == "missing_metadata":
        del members[stem + "METADATA"]
    if defect == "unrecorded":
        members["extra.bin"] = b"z"
    rec = io.StringIO(newline="")
    writer = csv.writer(rec, lineterminator="\n")
    for path, data in members.items():
        if defect == "unrecorded" and path == "extra.bin":
            continue
        hash_value = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        if defect == "wrong_digest" and path.endswith("__init__.py"):
            hash_value = "a" * 43
        writer.writerow((path, "sha256=" + hash_value, len(data)))
    writer.writerow((stem + "RECORD", "", ""))
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, data in members.items():
            bundle.writestr(path, data)
        bundle.writestr(stem + "RECORD", rec.getvalue())
        if defect == "duplicate":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                bundle.writestr(f"{package}/__init__.py", b"duplicate")
        if defect == "symlink":
            link = zipfile.ZipInfo("link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            bundle.writestr(link, b"file")
    return result.getvalue()


def _bodies(*, corrupt: str | None = None):
    bodies = {
        name: _wheel(name, defect=corrupt if name == WHEELS[1] else None)
        for name in WHEELS
    }
    bodies["BOOTSTRAP.py"] = b"synthetic-bootstrap"
    bodies["COMMIT_SHA"] = (COMMIT + "\n").encode()
    bodies["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n"
        for name in sorted((*WHEELS, "BOOTSTRAP.py"))
    ).encode()
    bodies["BUNDLE.json"] = json.dumps({
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": COMMIT, "python": "3.12",
        "projectWheel": PROJECT, "wheelCount": 29,
        "bootstrapSha256": hashlib.sha256(bodies["BOOTSTRAP.py"]).hexdigest(),
    }).encode()
    assert len(bodies) == 33
    return bodies


def _inputs(bodies):
    pins = PinnedReleaseRoster(
        COMMIT, "fabric-q7-bundle-" + COMMIT, 415955374,
        tuple(PinnedReleaseAsset(name, ix + 1, len(data), hashlib.sha256(data).hexdigest())
              for ix, (name, data) in enumerate(sorted(bodies.items()))),
    )
    admission = ReleaseAdmission(
        pins.commit, pins.tag, pins.release_id,
        tuple(ReleaseAsset(a.asset_id, a.name, a.bytes, a.sha256) for a in pins.files),
        PROJECT,
    )
    return admission, pins


def _reject(bodies):
    with pytest.raises(WheelhouseUnqualified, match="fabric_q7_wheelhouse_unqualified"):
        verify_pinned_q7_wheelhouse(*_inputs(bodies), bodies)


def test_valid_29_real_zip_wheels_have_record_metadata_consistency_only():
    bodies = _bodies()
    assert verify_pinned_q7_wheelhouse(*_inputs(bodies), bodies) == {
        "inspection": "wheel_metadata_record_only",
        "asset_count": 33, "wheel_count": 29,
        "wheel_metadata_verified": True,
        "independent_signer_verified": False,
        "local_custody_verified": False,
        "host_qualified": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }


@pytest.mark.parametrize("defect", [
    "wrong_metadata", "missing_metadata", "wrong_digest", "unrecorded",
    "duplicate", "symlink", "traversal",
])
def test_bad_wheel_denied_even_after_manifest_and_all_digests_are_repinned(defect):
    _reject(_bodies(corrupt=defect))


def test_random_bytes_denied_even_if_rehashed_in_manifest():
    bodies = _bodies()
    bodies[WHEELS[1]] = b"not a zip archive"
    bodies["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n"
        for name in sorted((*WHEELS, "BOOTSTRAP.py"))
    ).encode()
    _reject(bodies)


def test_wrong_independent_release_pin_refused_before_wheel_bytes():
    bodies = _bodies()
    admission, pins = _inputs(bodies)
    with pytest.raises(WheelhouseUnqualified):
        verify_pinned_q7_wheelhouse(replace(admission, release_id=222), pins, bodies)


def test_unknown_wheel_filename_denied():
    bodies = _bodies()
    previous = WHEELS[1]
    bodies["badname.whl"] = bodies.pop(previous)
    bodies["SHA256SUMS"] = b"".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n".encode()
        for name in sorted(set(bodies) - {"SHA256SUMS", "COMMIT_SHA", "BUNDLE.json"})
    )
    _reject(bodies)


def test_missing_wheel_denied():
    bodies = _bodies()
    bodies.pop(WHEELS[1])
    _reject(bodies)


def _generic_signed_inputs(count: int = 33, defect: str | None = None):
    """Bouw een volledig fictieve generieke release, zonder externe sleutel of I/O."""
    commit = "a" * 40
    tag = "fabric-update-bundle-" + commit
    asset_names = [PROJECT, *(
        f"dependency_{i:03d}-1.0-py3-none-any.whl" for i in range(count - 5)
    )]
    bodies = {
        name: _wheel(name, defect=defect if name == asset_names[-1] else None)
        for name in asset_names
    }
    bodies["BOOTSTRAP.py"] = b"synthetic-offline-bootstrap"
    bodies["COMMIT_SHA"] = (commit + "\n").encode()
    bodies["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n"
        for name in sorted([*asset_names, "BOOTSTRAP.py"])
    ).encode()
    bodies["BUNDLE.json"] = json.dumps({
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": commit, "python": "3.12",
        "projectWheel": PROJECT, "wheelCount": len(asset_names),
        "bootstrapSha256": hashlib.sha256(bodies["BOOTSTRAP.py"]).hexdigest(),
    }).encode()
    roster = [
        {
            "name": name, "asset_id": i + 1111, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for i, (name, data) in enumerate(sorted(bodies.items()))
    ]
    document = json.dumps({
        "schema_version": "runner-fabric/signed-release-roster/v1",
        "repository": "Blacksp1d3r/Runner-Fabric", "commit": commit,
        "tag": tag, "release_id": 222444, "files": roster,
    }, sort_keys=True, separators=(",", ":")).encode()
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    signed = verify_signed_fabric_roster(
        signed_document=document, signature=private.sign(document),
        public_key=public,
        independently_trusted_key_sha256=hashlib.sha256(public).hexdigest(),
        expected_commit=commit, expected_release_id=222444,
    )
    observed = inspect_exact_release(commit, {
        "id": 222444, "tag_name": tag, "target_commitish": commit,
        "draft": False, "prerelease": True,
        "assets": [{
            "id": row["asset_id"], "name": row["name"], "size": row["bytes"],
            "digest": "sha256:" + row["sha256"],
        } for row in roster],
    }, {"ref": "refs/tags/" + tag, "object": {"type": "commit", "sha": commit}})
    return signed, observed, bodies


@pytest.mark.parametrize("count", [5, 33, 160])
def test_generic_signed_wheelhouse_reuses_q7_parser_for_all_assets(count):
    signed, observed, bodies = _generic_signed_inputs(count)
    assert verify_signed_fabric_wheelhouse(signed, observed, bodies) == {
        "inspection": "wheel_metadata_record_only",
        "asset_count": count,
        "wheel_count": count - 4,
        "wheel_metadata_verified": True,
        "operator_signer_authority_attested": False,
        "local_custody_verified": False,
        "download_performed": False,
        "mutation_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }


@pytest.mark.parametrize("defect", [
    "wrong_metadata", "missing_metadata", "wrong_digest", "unrecorded",
    "duplicate", "symlink", "traversal",
])
def test_signed_generic_wheel_is_denied_despite_rehashed_bundle_and_manifest(defect):
    signed, observed, bodies = _generic_signed_inputs(defect=defect)
    with pytest.raises(WheelhouseUnqualified, match="^fabric_q7_wheelhouse_unqualified$"):
        verify_signed_fabric_wheelhouse(signed, observed, bodies)


def test_generic_bad_or_tampered_download_denied_before_wheel_parser():
    signed, observed, bodies = _generic_signed_inputs()
    bodies[PROJECT] = b"tampered-after-signature"
    with pytest.raises(WheelhouseUnqualified):
        verify_signed_fabric_wheelhouse(signed, observed, bodies)


def test_generic_untrusted_release_id_mismatch_denied():
    signed, observed, bodies = _generic_signed_inputs()
    with pytest.raises(WheelhouseUnqualified):
        verify_signed_fabric_wheelhouse(
            signed, replace(observed, release_id=777), bodies
        )



# F30 #341: GitHub bron-/CI-vertrouwen, GEEN Ed25519 productiesleutel.
@pytest.mark.parametrize("count", [5, 33, 160])
def test_github_release_full_byte_read_uses_existing_wheel_gate_without_ed(count):
    from runner_mcp.fabric_release_asset_bytes import (
        fetch_exact_github_release_bundle_bytes,
    )
    from runner_mcp.fabric_release_wheelhouse import (
        verify_github_release_wheelhouse,
    )

    _unused_test_signed, observed, bodies = _generic_signed_inputs(count)
    calls: list[int] = []

    def reader(*, token, asset_id, expected_size, independently_pinned_sha256):
        assert token == "synthetic-github-token-123456"
        calls.append(asset_id)
        match = next(x for x in observed.files if x.asset_id == asset_id)
        body = bodies[match.name]
        assert expected_size == len(body)
        assert independently_pinned_sha256 == hashlib.sha256(body).hexdigest()
        return body

    checked = verify_github_release_wheelhouse(observed, bodies)
    assert checked == {
        "inspection": "github_release_wheel_metadata_record_only",
        "asset_count": count,
        "wheel_count": count - 4,
        "provider_asset_bytes_verified": True,
        "wheel_metadata_verified": True,
        "independent_owner_signer_verified": False,
        "github_ci_policy_verified": False,
        "original_host_verified": False,
        "local_custody_verified": False,
        "install_authorized": False,
        "rollback_verified": False,
        "original_client_ack_proven": False,
    }
    result = fetch_exact_github_release_bundle_bytes(
        token="synthetic-github-token-123456",
        expected_commit=observed.commit,
        observed_metadata=observed,
        asset_reader=reader,
    )
    assert result == bodies
    assert calls == [item.asset_id for item in observed.files]


@pytest.mark.parametrize("bad", [
    "wrong_commit", "q7_tag", "wrong_release_id", "missing_file",
    "duplicate_id", "overcap_size", "bad_token", "extra_asset",
])
def test_github_batch_refuses_invalid_input_before_first_asset_get(bad):
    from runner_mcp.fabric_release_asset_bytes import (
        AssetBytesUnqualified,
        fetch_exact_github_release_bundle_bytes,
    )

    _signed, observed, bodies = _generic_signed_inputs(5)
    commit = observed.commit
    token = "synthetic-github-token-123456"
    if bad == "wrong_commit":
        commit = "f" * 40
    elif bad == "q7_tag":
        observed = replace(observed, tag="fabric-q7-bundle-" + commit)
    elif bad == "wrong_release_id":
        observed = replace(observed, release_id=True)
    elif bad == "missing_file":
        observed = replace(observed, files=observed.files[:-1])
    elif bad == "duplicate_id":
        first = observed.files[0]
        second = replace(observed.files[1], asset_id=first.asset_id)
        observed = replace(observed, files=(first, second, *observed.files[2:]))
    elif bad == "overcap_size":
        first = replace(observed.files[0], bytes=64 * 1024 * 1024 + 1)
        observed = replace(observed, files=(first, *observed.files[1:]))
    elif bad == "bad_token":
        token = ""
    else:
        observed = replace(observed, files=(
            *observed.files,
            replace(observed.files[0], name="unapproved-file.txt",
                    asset_id=98777),
        ))
    calls: list[int] = []

    def reader(**kwargs):
        calls.append(kwargs["asset_id"])
        raise AssertionError("unqualified metadata must never read an asset")

    with pytest.raises(
        AssetBytesUnqualified, match="^fabric_release_asset_bytes_unqualified$"
    ):
        fetch_exact_github_release_bundle_bytes(
            token=token, expected_commit=commit,
            observed_metadata=observed, asset_reader=reader,
        )
    assert calls == []
    assert len(bodies) == 5


@pytest.mark.parametrize("bad", [
    "altered_blob", "short_blob", "wrong_type", "read_error",
    "invalid_wheel", "missing_manifest", "wrong_sha256sums",
])
def test_github_batch_denies_partial_or_corrupt_bytes_without_result(bad):
    from runner_mcp.fabric_release_asset_bytes import (
        AssetBytesUnqualified,
        fetch_exact_github_release_bundle_bytes,
    )

    _signed, observed, bodies = _generic_signed_inputs(5)
    wrong_name = next(name for name in bodies if name.endswith(".whl"))
    if bad == "invalid_wheel":
        # De provider metadata wordt opnieuw op ongeldige ZIP gepind: zelfs
        # dan moet de bestaande ZIP/RECORD-parser deze inhoud weigeren.
        bodies[wrong_name] = b"invalid-wheel"
        observed = replace(observed, files=tuple(
            replace(x, bytes=len(bodies[wrong_name]),
                    sha256=hashlib.sha256(bodies[wrong_name]).hexdigest())
            if x.name == wrong_name else x
            for x in observed.files
        ))
        bodies["SHA256SUMS"] = "".join(
            f"{hashlib.sha256(bodies[name]).hexdigest()}  {name}\n"
            for name in sorted(set(bodies) - {
                "SHA256SUMS", "BUNDLE.json", "COMMIT_SHA"
            })
        ).encode()
        observed = replace(observed, files=tuple(
            replace(x, bytes=len(bodies["SHA256SUMS"]),
                    sha256=hashlib.sha256(bodies["SHA256SUMS"]).hexdigest())
            if x.name == "SHA256SUMS" else x
            for x in observed.files
        ))
    if bad == "missing_manifest":
        bodies["BUNDLE.json"] = b""
    if bad == "wrong_sha256sums":
        bodies["SHA256SUMS"] = b"0" * 64 + b"  BOOTSTRAP.py\n"

    def reader(*, asset_id, **_kwargs):
        name = next(x.name for x in observed.files if x.asset_id == asset_id)
        if name == wrong_name:
            if bad == "altered_blob":
                return b"forged-wheel-data"
            if bad == "short_blob":
                return bodies[name][:-1]
            if bad == "wrong_type":
                return bytearray(bodies[name])
            if bad == "read_error":
                raise TimeoutError("simulated asset timeout")
        return bodies[name]

    with pytest.raises(
        AssetBytesUnqualified, match="^fabric_release_asset_bytes_unqualified$"
    ):
        fetch_exact_github_release_bundle_bytes(
            token="synthetic-github-token-123456",
            expected_commit=observed.commit,
            observed_metadata=observed,
            asset_reader=reader,
        )


def test_manager_github_release_source_reuses_fixed_snapshot_without_install():
    from runner_mcp.fabric_update import FabricUpdateManager

    _signed, observed, bodies = _generic_signed_inputs(5)
    manager = object.__new__(FabricUpdateManager)
    calls: list[tuple[str, str]] = []
    manager._read_exact_release_admission = lambda commit: (
        calls.append(("exact_fixed_release_tag", commit)) or observed
    )
    manager._github_token = lambda: "synthetic-github-token-123456"

    def reader(*, token, asset_id, expected_size, independently_pinned_sha256):
        calls.append(("asset", str(asset_id)))
        name = next(x.name for x in observed.files if x.asset_id == asset_id)
        return bodies[name]

    assert manager._read_exact_github_release_bytes(
        expected_commit=observed.commit, asset_reader=reader
    ) == bodies
    assert calls[0] == ("exact_fixed_release_tag", observed.commit)
    assert len(calls) == 1 + len(observed.files)
    # De publieke update-API, BOOTSTRAP, launcher en originele Q7 blijven
    # ongewijzigd. De private methode downloadt alleen echte gecontroleerde
    # bytes in het geheugen en geeft geen hostbevoegdheid.
