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



# F30 0.1.150: gedeelde create-once opslag, GitHub trust zonder ED signer.
@pytest.mark.parametrize("count", [5, 33, 160])
def test_github_release_full_bytes_stage_only_in_existing_private_root(
    tmp_path, count,
):
    from runner_mcp.fabric_release_inactive_custody import (
        InactiveSignedCustodyUnqualified,
        _stage_github_release_inactive_once,
    )

    _unused_signed, observed, bodies = _generic_signed_inputs(count)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    active = tmp_path / "active"
    active.mkdir()
    (active / "original.txt").write_text("keep", encoding="ascii")
    args = {
        "local_bundles_root": root,
        "expected_commit": observed.commit,
        "expected_release_id": observed.release_id,
        "observed_metadata": observed,
        "asset_bodies": bodies,
    }
    receipt = _stage_github_release_inactive_once(**args)
    assert receipt == {
        "commit": observed.commit,
        "release_id": observed.release_id,
        "source": "github-release-provider-integrity-only",
        "inactive_custody": True,
        "asset_count": count,
        "github_ci_policy_verified": False,
        "independent_owner_signer_verified": False,
        "owner_authority_proven": False,
        "install_authorized": False,
        "rollback_verified": False,
        "original_client_ack": False,
    }
    target = root / observed.commit
    assert target.stat().st_mode & 0o777 == 0o700
    # De bestaande NOREPLACE-promotie verplaatst source/bundle als ÉÉN
    # map naar de VLAKKE eindbestemming (niet de bovenliggende .incoming).
    assert {x.name for x in target.iterdir()} == set(bodies)
    assert all((target / name).read_bytes() == blob
               for name, blob in bodies.items())
    assert all((target / name).stat().st_mode & 0o777 == 0o600
               for name in bodies)
    assert all((target / name).stat().st_nlink == 1 for name in bodies)
    assert (active / "original.txt").read_text() == "keep"
    assert not (root / "bundle").exists()

    # De bewaarde .incoming is uitsluitend lege herstel-/forensische
    # structuur; er mag nooit een tweede kopie van de assets achterblijven.
    pending = [p for p in root.iterdir() if p.name.startswith(".incoming-")]
    assert len(pending) == 1
    assert pending[0].stat().st_mode & 0o777 == 0o700
    assert {p.name for p in pending[0].iterdir()} == {"source"}
    source = pending[0] / "source"
    assert source.stat().st_mode & 0o777 == 0o700
    assert list(source.iterdir()) == []

    # Structurele local-readiness is geen autorisatie tot start_local/apply.
    from runner_mcp.fabric_update import FabricUpdateManager

    assert object.__new__(FabricUpdateManager)._validate_local_bundle_source(
        target
    ) is None

    # NOREPLACE is source policy; even equal bytes may never overwrite.
    first_inode = target.stat().st_ino
    with pytest.raises(
        InactiveSignedCustodyUnqualified,
        match="^fabric_signed_inactive_custody_unqualified$",
    ):
        _stage_github_release_inactive_once(**args)
    assert target.stat().st_ino == first_inode


@pytest.mark.parametrize("bad", [
    "commit", "release_id", "asset_bytes", "manifest", "zip",
    "symlink_root", "mode_root", "occupied_target",
])
def test_github_release_inactive_custody_refuses_without_replacing_target(
    tmp_path, bad,
):
    from runner_mcp.fabric_release_inactive_custody import (
        InactiveSignedCustodyUnqualified,
        _stage_github_release_inactive_once,
    )

    _unused_signed, observed, original = _generic_signed_inputs(5)
    bodies = dict(original)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    args = {
        "local_bundles_root": root,
        "expected_commit": observed.commit,
        "expected_release_id": observed.release_id,
        "observed_metadata": observed,
        "asset_bodies": bodies,
    }
    occupied = False
    if bad == "commit":
        args["expected_commit"] = "f" * 40
    elif bad == "release_id":
        args["expected_release_id"] += 1
    elif bad == "asset_bytes":
        bodies["BOOTSTRAP.py"] += b"modified"
    elif bad == "manifest":
        bodies["BUNDLE.json"] = b"not-json"
    elif bad == "zip":
        wheel = next(x for x in bodies if x.endswith(".whl"))
        bodies[wheel] = b"not-a-zip"
    elif bad == "symlink_root":
        elsewhere = tmp_path / "private-real"
        root.rename(elsewhere)
        root.symlink_to(elsewhere, target_is_directory=True)
    elif bad == "mode_root":
        root.chmod(0o755)
    else:
        target = root / observed.commit
        target.mkdir(mode=0o700)
        (target / "sentinel").write_text("keep", encoding="ascii")
        occupied = True
    with pytest.raises(
        InactiveSignedCustodyUnqualified,
        match="^fabric_signed_inactive_custody_unqualified$",
    ):
        _stage_github_release_inactive_once(**args)
    if occupied:
        assert (root / observed.commit / "sentinel").read_text() == "keep"
        assert not any((root / observed.commit / name).exists()
                       for name in bodies)
    else:
        assert not (root / observed.commit).exists()


def test_manager_source_stage_uses_one_release_snapshot_and_no_active_mutation(
    tmp_path,
):
    from runner_mcp.fabric_update import FabricUpdateManager

    _unused_signed, observed, bodies = _generic_signed_inputs(5)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    manager = object.__new__(FabricUpdateManager)
    manager.local_bundles_root = root
    events = []
    manager._read_exact_release_admission = lambda commit: (
        events.append(("release", commit)) or observed
    )
    manager._github_token = lambda: "synthetic-github-token-123456"

    def reader(*, token, asset_id, expected_size, independently_pinned_sha256):
        events.append(("asset", asset_id))
        name = next(item.name for item in observed.files
                    if item.asset_id == asset_id)
        return bodies[name]

    result = manager._stage_github_release_inactive_once(
        expected_commit=observed.commit,
        expected_release_id=observed.release_id,
        asset_reader=reader,
    )
    assert result["download_performed"] is True
    assert result["inactive_custody"] is True
    assert result["install_authorized"] is False
    assert result["rollback_verified"] is False
    assert events[0] == ("release", observed.commit)
    assert len(events) == len(observed.files) + 1
    assert all(events.count(("asset", item.asset_id)) == 1
               for item in observed.files)
    assert (root / observed.commit / "BUNDLE.json").read_bytes() == bodies["BUNDLE.json"]


def test_manager_wrong_release_id_fails_before_asset_transfer_and_stage(tmp_path):
    from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager

    _unused_signed, observed, bodies = _generic_signed_inputs(5)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    manager = object.__new__(FabricUpdateManager)
    manager.local_bundles_root = root
    requests = []
    manager._read_exact_release_admission = lambda commit: observed
    manager._github_token = lambda: "synthetic-github-token-123456"

    def reader(**kw):
        requests.append(kw)
        return bodies["BUNDLE.json"]

    with pytest.raises(FabricUpdateError, match="fabric_release_assets_unqualified"):
        manager._stage_github_release_inactive_once(
            expected_commit=observed.commit,
            expected_release_id=observed.release_id + 1,
            asset_reader=reader,
        )
    assert requests == []
    assert list(root.iterdir()) == []


def test_keyless_inactive_stage_remains_private_not_a_second_update_or_tool():
    from pathlib import Path

    from runner_mcp.fabric_release_inactive_custody import (
        _stage_github_release_inactive_once,
    )

    assert callable(_stage_github_release_inactive_once)
    root = Path(__file__).resolve().parents[1] / "src/runner_mcp"
    app = (root / "server.py").read_text(encoding="utf-8")
    installer = (root / "self_update_install.py").read_text(encoding="utf-8")
    assert "_stage_github_release_inactive_once" not in app
    assert "_stage_github_release_inactive_once" not in installer
    assert "github_release_inactive" not in app


# F30/#341: dezelfde bestaande manager moet de gepromoveerde release ook kunnen
# TERUGLEZEN, zonder ooit bootstrap/preflight/apply of een service te starten.
@pytest.mark.parametrize("count", [5, 33, 160])
def test_keyless_release_stage_to_existing_local_readiness_is_read_only(tmp_path, count):
    """Controleer de hele offline opslag-/leesketen zonder hostbevoegdheid.

    Alle GitHub-data en assets zijn fictief; de enige echte I/O gebeurt binnen
    pytest-tmp_path. De private source-route krijgt GEEN bevoegdheid tot
    installatie en de bestaande public local_readiness wordt niet gewijzigd.
    """
    from runner_mcp.fabric_update import FabricUpdateManager

    _unused_signed, observed, bodies = _generic_signed_inputs(count)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    active = tmp_path / "active"
    active.mkdir()
    (active / "sentinel").write_text("never touch", encoding="ascii")

    manager = object.__new__(FabricUpdateManager)
    manager.local_bundles_root = root
    calls = []
    manager._read_exact_release_admission = lambda commit: (
        calls.append(("release", commit)) or observed
    )
    manager._github_token = lambda: "synthetic-test-token"
    # Alleen in deze geïsoleerde test: normale runtime/launcher-bevoegdheid
    # wordt NIET nagebootst als geslaagd productieattest.
    manager._require_safe_runtime = lambda: None
    manager._assert_managed_launcher = lambda: None
    manager._runner = lambda *args, **kw: pytest.fail("bootstrap was executed")

    def asset_reader(*, token, asset_id, expected_size, independently_pinned_sha256):
        calls.append(("asset", asset_id))
        name = next(item.name for item in observed.files if item.asset_id == asset_id)
        return bodies[name]

    stored = manager._stage_github_release_inactive_once(
        expected_commit=observed.commit,
        expected_release_id=observed.release_id,
        asset_reader=asset_reader,
    )
    assert stored["inactive_custody"] is True
    assert stored["download_performed"] is True
    assert stored["install_authorized"] is False
    assert stored["rollback_verified"] is False
    assert stored["original_client_ack"] is False

    # Dit controleert het werkelijk vlak gepromoveerde bundle-formaat met
    # dezelfde _validated_bootstrap als het bestaande lokale updatepad.
    ready = manager.local_readiness(observed.commit)
    assert ready == {
        "commit": observed.commit,
        "artifact_ready": True,
        "source": "local-custody",
    }
    assert all(ready.get(key) is not True for key in (
        "install_authorized", "rollback_verified", "original_client_ack",
    ))
    assert calls.count(("release", observed.commit)) == 1
    assert len(calls) == count + 1
    assert (active / "sentinel").read_text("ascii") == "never touch"
    assert not (root / "bundle").exists()
    assert not (tmp_path / "slots").exists()
    assert not (tmp_path / "transaction.json").exists()


@pytest.mark.parametrize("damage", ["bootstrap", "wheel", "manifest"])
def test_keyless_local_readiness_refuses_changed_disk_bytes_without_activation(
    tmp_path, damage,
):
    """Na opslag is elk gewijzigd bestand opnieuw een lokale STOP.

    De SHA256SUMS/BUNDLE/BOOTSTRAP-controle is van de bestaande manager;
    er is geen nieuwe validator, installer, netwerk- of herstelcontroller.
    """
    from runner_mcp.fabric_release_inactive_custody import (
        _stage_github_release_inactive_once,
    )
    from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager

    _unused_signed, observed, bodies = _generic_signed_inputs(5)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    receipt = _stage_github_release_inactive_once(
        local_bundles_root=root,
        expected_commit=observed.commit,
        expected_release_id=observed.release_id,
        observed_metadata=observed,
        asset_bodies=bodies,
    )
    assert receipt["install_authorized"] is False
    final = root / observed.commit
    name = (
        "BOOTSTRAP.py" if damage == "bootstrap" else
        "BUNDLE.json" if damage == "manifest" else
        next(name for name in bodies if name.endswith(".whl"))
    )
    file = final / name
    original = file.read_bytes()
    file.write_bytes((b"x" if original[:1] != b"x" else b"y") + original[1:])

    manager = object.__new__(FabricUpdateManager)
    manager.local_bundles_root = root
    manager._require_safe_runtime = lambda: None
    manager._assert_managed_launcher = lambda: None
    manager._runner = lambda *args, **kw: pytest.fail("bootstrap was executed")
    with pytest.raises(
        FabricUpdateError,
        match="^fabric_bundle_(?:invalid|integrity_failed)$",
    ):
        manager.local_readiness(observed.commit)
    assert file.read_bytes() != original
    assert not (root / "bundle").exists()
    assert not (tmp_path / "slots").exists()
    assert not (tmp_path / "transaction.json").exists()


# F30/#341 v0.1.151: hashrepinning na bewaring mag geen ongeldige wheel
# tot een geschikt lokale-updatebestand maken. Dezelfde, eerder bestaande
# ZIP/METADATA/RECORD-lezer dient zowel byte-import als lokale consumptie.
def test_local_readiness_rechecks_wheel_record_after_checksum_repin(tmp_path):
    """Bewaar fictieve geldige bytes en vervang daarna wheel plus SHA256SUMS.

    De oudere digest-only bundlechecker ziet dan nog overeenstemmende hashes,
    maar de werkelijke local_readiness en interne local-update stage mogen
    geen ongeldige ZIP doorlaten. Alle I/O blijft binnen pytest-tmp_path.
    """
    from types import SimpleNamespace

    from runner_mcp.fabric_release_inactive_custody import (
        _stage_github_release_inactive_once,
    )
    from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager

    _unused_signed, observed, bodies = _generic_signed_inputs(5)
    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    stored = _stage_github_release_inactive_once(
        local_bundles_root=root,
        expected_commit=observed.commit,
        expected_release_id=observed.release_id,
        observed_metadata=observed,
        asset_bodies=bodies,
    )
    assert stored["install_authorized"] is False

    final = root / observed.commit
    wheel = next(final.glob("*.whl"))
    wheel.write_bytes(b"invalid zip after local staging")
    payload_names = sorted([wheel.name for wheel in final.glob("*.whl")] +
                           ["BOOTSTRAP.py"])
    (final / "SHA256SUMS").write_text(
        "".join(
            f"{hashlib.sha256((final / name).read_bytes()).hexdigest()}  {name}\n"
            for name in payload_names
        ),
        encoding="ascii",
    )

    manager = object.__new__(FabricUpdateManager)
    manager.local_bundles_root = root
    manager.state_root = tmp_path / "state"
    manager._require_safe_runtime = lambda: None
    manager._assert_managed_launcher = lambda: None
    manager._runner = lambda *args, **kw: pytest.fail("unexpected subprocess")

    # Bewijs precies waarom louter het opnieuw vergelijken van SHA256SUMS
    # onvoldoende is: ze kunnen samen met de wheel zijn aangepast.
    assert manager._validated_bootstrap(observed.commit, root=final) == (
        final / "BOOTSTRAP.py"
    )
    with pytest.raises(
        FabricUpdateError, match="^fabric_bundle_integrity_failed$",
    ):
        manager.local_readiness(observed.commit)
    with pytest.raises(
        FabricUpdateError, match="^fabric_bundle_integrity_failed$",
    ):
        manager._stage_local_bundle(
            SimpleNamespace(commit=observed.commit, job_id="b" * 32),
        )
    assert not (tmp_path / "state").exists()
    assert not (tmp_path / "bundle").exists()
    assert not (tmp_path / "transaction.json").exists()
