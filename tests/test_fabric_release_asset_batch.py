"""Offline simulatie van de generieke exact signed Release-byteimport.

Gebruik alleen tijdelijk gegenereerde Ed25519-sleutels, fictieve Release-metadata,
kleine zelfgemaakte WHEEL/RECORD ZIP's en een nep-assetlezer. Er is geen netwerk,
werkelijke eigenaarssigner, host, bestandscustody, BOOTSTRAP-uitvoering of update.
"""

from __future__ import annotations

import ast
import base64
import csv
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from runner_mcp.fabric_release_asset_bytes import (
    AssetBytesUnqualified,
    fetch_exact_signed_fabric_bundle_bytes,
)
from runner_mcp.fabric_release_assets import inspect_exact_release
from runner_mcp.fabric_update import FabricUpdateError, FabricUpdateManager

COMMIT = "a" * 40
RELEASE_ID = 222444
TAG = "fabric-update-bundle-" + COMMIT
PROJECT = "runner_fabric-1.2.3-py3-none-any.whl"
TOKEN = "synthetic-no-real-secret"


def _wheel(name: str, *, corrupt: bool = False) -> bytes:
    """Maak een echt, klein wiel waarvan RECORD alle ZIP-inhouden vastpint."""
    package, version, *_ = name.split("-")
    stem = f"{package}-{version}.dist-info/"
    members = {
        f"{package}/__init__.py": b"x=1\n",
        stem + "METADATA": (
            f"Metadata-Version: 2.3\nName: {package}\nVersion: {version}\n\n"
        ).encode(),
        stem + "WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: synthetic\n"
            b"Root-Is-Purelib: true\nTag: py3-none-any\n\n"
        ),
    }
    out = io.StringIO(newline="")
    rows = csv.writer(out, lineterminator="\n")
    for path, data in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.writerow((path, "sha256=" + digest, len(data)))
    rows.writerow((stem + "RECORD", "", ""))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, data in members.items():
            archive.writestr(path, data)
        archive.writestr(stem + "RECORD", out.getvalue())
        if corrupt:
            archive.writestr("unrecorded.bin", b"unverified")
    return buffer.getvalue()


def _case(count: int = 5, *, corrupt_wheel: bool = False):
    """Lever ondertekend, volledig overeenkomend gesimuleerd transport aan."""
    wheels = [PROJECT, *(
        f"dependency_{i:03d}-1.0-py3-none-any.whl"
        for i in range(count - 5)
    )]
    bodies = {
        name: _wheel(name, corrupt=corrupt_wheel and name == wheels[-1])
        for name in wheels
    }
    bodies["BOOTSTRAP.py"] = b"synthetic-bootstrap"
    bodies["COMMIT_SHA"] = (COMMIT + "\n").encode()
    bodies["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(bodies[n]).hexdigest()}  {n}\n"
        for n in sorted([*wheels, "BOOTSTRAP.py"])
    ).encode()
    bodies["BUNDLE.json"] = json.dumps({
        "schemaVersion": "runner.fabric/control-plane-update-bundle/v1",
        "commitSha": COMMIT,
        "python": "3.12",
        "projectWheel": PROJECT,
        "wheelCount": len(wheels),
        "bootstrapSha256": hashlib.sha256(bodies["BOOTSTRAP.py"]).hexdigest(),
    }).encode()
    roster = [
        {
            "name": name,
            "asset_id": i + 1001,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for i, (name, data) in enumerate(sorted(bodies.items()))
    ]
    raw = json.dumps({
        "schema_version": "runner-fabric/signed-release-roster/v1",
        "repository": "Blacksp1d3r/Runner-Fabric",
        "commit": COMMIT,
        "tag": TAG,
        "release_id": RELEASE_ID,
        "files": roster,
    }, sort_keys=True, separators=(",", ":")).encode()
    signer = Ed25519PrivateKey.generate()
    pub = signer.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    observed = inspect_exact_release(COMMIT, {
        "id": RELEASE_ID,
        "tag_name": TAG,
        "target_commitish": COMMIT,
        "draft": False,
        "prerelease": True,
        "assets": [{
            "name": row["name"],
            "id": row["asset_id"],
            "size": row["bytes"],
            "digest": "sha256:" + row["sha256"],
        } for row in roster],
    }, {
        "ref": "refs/tags/" + TAG,
        "object": {"type": "commit", "sha": COMMIT},
    })
    args = {
        "token": TOKEN,
        "signed_document": raw,
        "signature": signer.sign(raw),
        "public_key": pub,
        "independently_trusted_key_sha256": hashlib.sha256(pub).hexdigest(),
        "expected_commit": COMMIT,
        "expected_release_id": RELEASE_ID,
        "observed_metadata": observed,
    }
    lookup = {i + 1001: data for i, (_, data) in enumerate(sorted(bodies.items()))}
    return args, bodies, lookup


def _reader(lookup, calls, *, failure_at=None, bad=None):
    def read(*, token, asset_id, expected_size, independently_pinned_sha256):
        calls.append(asset_id)
        assert token == TOKEN
        assert expected_size == len(lookup[asset_id])
        assert independently_pinned_sha256 == hashlib.sha256(
            lookup[asset_id]
        ).hexdigest()
        if asset_id == failure_at:
            if bad == "error":
                raise ValueError("injected-token-never-expose")
            if bad == "short":
                return lookup[asset_id][:-1]
            if bad == "wrong":
                return b"x" * expected_size
            if bad == "nonbytes":
                return bytearray(lookup[asset_id])
        return lookup[asset_id]
    return read


@pytest.mark.parametrize("count", [5, 33, 160])
def test_exact_signed_batch_reuses_asset_reader_and_wheelhouse(count):
    args, bodies, lookup = _case(count)
    calls = []
    actual = fetch_exact_signed_fabric_bundle_bytes(
        **args, asset_reader=_reader(lookup, calls)
    )
    assert actual == bodies
    assert len(calls) == count
    assert calls == sorted(lookup)
    assert all(type(b) is bytes for b in actual.values())


@pytest.mark.parametrize("change", [
    "key", "signature", "commit", "release_id", "api_asset_id",
    "api_size", "api_digest", "api_tag", "api_commit", "token",
])
def test_identity_or_transport_authority_fails_before_any_asset_get(change):
    args, _, lookup = _case(5)
    calls = []
    if change == "key":
        args["independently_trusted_key_sha256"] = "f" * 64
    elif change == "signature":
        args["signature"] = b"\0" * 64
    elif change == "commit":
        args["expected_commit"] = "b" * 40
    elif change == "release_id":
        args["expected_release_id"] = RELEASE_ID + 1
    elif change == "api_asset_id":
        original = args["observed_metadata"]
        first = replace(original.files[0], asset_id=42)
        args["observed_metadata"] = replace(original, files=(first, *original.files[1:]))
    elif change == "api_size":
        original = args["observed_metadata"]
        first = replace(original.files[0], bytes=42)
        args["observed_metadata"] = replace(original, files=(first, *original.files[1:]))
    elif change == "api_digest":
        original = args["observed_metadata"]
        first = replace(original.files[0], sha256="b" * 64)
        args["observed_metadata"] = replace(original, files=(first, *original.files[1:]))
    elif change == "api_tag":
        args["observed_metadata"] = replace(
            args["observed_metadata"], tag="fabric-update-bundle-" + "b" * 40
        )
    elif change == "api_commit":
        args["observed_metadata"] = replace(
            args["observed_metadata"], commit="b" * 40
        )
    else:
        args["token"] = "bad\nheader"
    with pytest.raises(AssetBytesUnqualified, match="^fabric_release_asset_bytes_unqualified$"):
        fetch_exact_signed_fabric_bundle_bytes(
            **args, asset_reader=_reader(lookup, calls)
        )
    assert calls == []


@pytest.mark.parametrize("bad", ["error", "short", "wrong", "nonbytes"])
def test_failed_asset_read_does_not_return_partial_bodies_or_fetch_more(bad):
    args, _, lookup = _case(33)
    calls = []
    failure_at = sorted(lookup)[2]
    with pytest.raises(AssetBytesUnqualified) as exc:
        fetch_exact_signed_fabric_bundle_bytes(
            **args,
            asset_reader=_reader(lookup, calls, failure_at=failure_at, bad=bad),
        )
    assert calls == sorted(lookup)[:3]
    assert "injected-token" not in str(exc.value)
    assert "synthetic-no-real-secret" not in str(exc.value)


def test_corrupted_wheel_with_valid_signature_and_sha_denied_after_reads():
    args, _, lookup = _case(5, corrupt_wheel=True)
    calls = []
    with pytest.raises(AssetBytesUnqualified):
        fetch_exact_signed_fabric_bundle_bytes(
            **args, asset_reader=_reader(lookup, calls)
        )
    assert len(calls) == 5


def test_no_actual_network_or_host_update_is_part_of_test_or_batch_path():
    path = Path(__file__).resolve().parents[1] / (
        "src/runner_mcp/fabric_release_asset_bytes.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    funcs = {
        node.name: node
        for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    batch = funcs["fetch_exact_signed_fabric_bundle_bytes"]
    call_attrs = {
        n.func.attr for n in ast.walk(batch)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert not call_attrs.intersection({
        "start_local", "stage_local_bundle", "apply", "rollback", "mkdir",
        "write_bytes", "replace", "rmtree", "run", "Popen", "open",
    })
    # De oude downloader blijft via importlib op bestandsniveau te laden:
    # de nieuw toegevoegde pakketafhankelijkheden staan uitsluitend lokaal.
    assert not any(
        isinstance(n, ast.ImportFrom) and (n.module or "").startswith("fabric_release")
        for n in tree.body
    )


def _mock_manager_for_signed_batch(monkeypatch, args, *, metadata_change=None):
    """Bevestig dat de manager alleen de TWEE bestaande vaste endpoints leest."""
    manager = object.__new__(FabricUpdateManager)
    audit = []
    observed = args["observed_metadata"]
    meta = {
        "id": observed.release_id,
        "tag_name": observed.tag,
        "target_commitish": observed.commit,
        "draft": False,
        "prerelease": True,
        "assets": [{
            "name": row.name,
            "id": row.asset_id,
            "size": row.bytes,
            "digest": "sha256:" + row.sha256,
        } for row in observed.files],
    }
    if metadata_change is not None:
        meta = metadata_change(meta)
    tag_ref = {
        "ref": "refs/tags/" + observed.tag,
        "object": {"type": "commit", "sha": observed.commit},
    }
    monkeypatch.setattr(manager, "_require_safe_runtime",
                        lambda: audit.append("safe"))
    monkeypatch.setattr(manager, "_assert_managed_launcher",
                        lambda: audit.append("launcher"))
    monkeypatch.setattr(manager, "_github_token",
                        lambda: TOKEN)
    def read(token, path, *, category):
        assert token == TOKEN
        assert category == "fabric_release_metadata_unavailable"
        audit.append(path)
        if path == "/repos/Blacksp1d3r/Runner-Fabric/releases/tags/" + TAG:
            return meta
        if path == "/repos/Blacksp1d3r/Runner-Fabric/git/ref/tags/" + TAG:
            return tag_ref
        pytest.fail("unexpected GitHub endpoint")
    monkeypatch.setattr(manager, "_api_json", read)
    for op in ("start_local", "stage_local_bundle", "_activate_bundle",
               "_validated_bootstrap", "_download_artifact"):
        monkeypatch.setattr(
            manager, op, lambda *a, **k: pytest.fail(
                "Geen opslag, activatie, oude updater of bootstrap toegestaan"
            )
        )
    return manager, audit


def _invoke_manager_batch(manager, args, asset_reader):
    """Gebruik exacte v1-signer/provenance-invoer, nooit een echte token."""
    fields = {key: args[key] for key in (
        "expected_commit", "expected_release_id", "signed_document",
        "signature", "public_key", "independently_trusted_key_sha256",
    )}
    return manager._read_verified_signed_release_bytes(
        **fields, asset_reader=asset_reader
    )


@pytest.mark.parametrize("count", [5, 33])
def test_manager_reuses_exact_metadata_and_full_existing_signed_byte_gate(
    monkeypatch, count,
):
    """Geen nieuwe API-route, tweede downloader of servicewijziging."""
    args, bodies, lookup = _case(count)
    manager, audit = _mock_manager_for_signed_batch(monkeypatch, args)
    requested = []
    verified = _invoke_manager_batch(
        manager, args, _reader(lookup, requested)
    )
    assert verified == bodies
    assert requested == sorted(lookup)
    assert audit == [
        "safe", "launcher",
        "/repos/Blacksp1d3r/Runner-Fabric/releases/tags/" + TAG,
        "/repos/Blacksp1d3r/Runner-Fabric/git/ref/tags/" + TAG,
    ]


@pytest.mark.parametrize("broken", [
    "signature", "wrong_key", "wrong_commit", "wrong_release_id"
])
def test_manager_denies_bad_signed_owner_pins_before_metadata_or_download(
    monkeypatch, broken,
):
    args, _, lookup = _case()
    manager, audit = _mock_manager_for_signed_batch(monkeypatch, args)
    if broken == "signature":
        args["signature"] = b"x" * 64
    elif broken == "wrong_key":
        args["independently_trusted_key_sha256"] = "f" * 64
    elif broken == "wrong_commit":
        args["expected_commit"] = "b" * 40
    else:
        args["expected_release_id"] = RELEASE_ID + 1
    requested = []
    with pytest.raises(
        FabricUpdateError, match="^fabric_signed_release_roster_unqualified$"
    ):
        _invoke_manager_batch(manager, args, _reader(lookup, requested))
    assert audit == []
    assert requested == []


def test_manager_denies_changed_github_metadata_before_any_asset_get(monkeypatch):
    """Zelfde release-ID en commit kunnen gewijzigde asset-ID niet verhullen."""
    args, _, lookup = _case()
    def mutate(data):
        data["assets"][0]["id"] += 17
        return data
    manager, audit = _mock_manager_for_signed_batch(
        monkeypatch, args, metadata_change=mutate
    )
    requested = []
    with pytest.raises(
        FabricUpdateError, match="^fabric_release_asset_bytes_unqualified$"
    ):
        _invoke_manager_batch(manager, args, _reader(lookup, requested))
    assert len(audit) == 4
    assert requested == []


def test_manager_rejects_partial_or_corrupt_response_without_custody(monkeypatch):
    args, _, lookup = _case(33)
    manager, audit = _mock_manager_for_signed_batch(monkeypatch, args)
    requested = []
    with pytest.raises(
        FabricUpdateError, match="^fabric_release_asset_bytes_unqualified$"
    ):
        _invoke_manager_batch(
            manager, args,
            _reader(lookup, requested, failure_at=sorted(lookup)[2], bad="short"),
        )
    assert len(audit) == 4
    assert requested == sorted(lookup)[:3]


def test_internal_manager_batch_not_exported_as_server_or_tool():
    """Broncontract: nog GEEN publieke importtool en geen installatie-autoriteit."""
    server = (Path(__file__).resolve().parents[1] / "src/runner_mcp/server.py")
    tree = ast.parse(server.read_text(encoding="utf-8"))
    names = {
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_read_verified_signed_release_bytes" not in names
    manager_path = (
        Path(__file__).resolve().parents[1] / "src/runner_mcp/fabric_update.py"
    )
    manager_ast = ast.parse(manager_path.read_text(encoding="utf-8"))
    method = [
        m for n in ast.walk(manager_ast)
        if isinstance(n, ast.ClassDef) and n.name == "FabricUpdateManager"
        for m in n.body
        if isinstance(m, ast.FunctionDef)
        and m.name == "_read_verified_signed_release_bytes"
    ]
    assert len(method) == 1
    called = {
        n.attr for n in ast.walk(method[0])
        if isinstance(n, ast.Attribute)
    }
    assert "start_local" not in called
    assert "stage_local_bundle" not in called
    assert "_activate_bundle" not in called
    assert "_validated_bootstrap" not in called


# F30 S2e: enkel tijdelijke Python-testmappen, geen echte release of dienst.
def _offline_inactive_args(args, bodies, root):
    return {
        "local_bundles_root": root,
        "signed_document": args["signed_document"],
        "signature": args["signature"],
        "public_key": args["public_key"],
        "independently_trusted_key_sha256": args["independently_trusted_key_sha256"],
        "expected_commit": args["expected_commit"],
        "expected_release_id": args["expected_release_id"],
        "observed_metadata": args["observed_metadata"],
        "asset_bodies": bodies,
    }


@pytest.mark.parametrize("count", [5, 33])
def test_signed_bundle_private_inactive_noreplace_source_only(tmp_path, count):
    from runner_mcp.fabric_release_inactive_custody import (
        _stage_signed_release_inactive_once,
    )

    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    args, bodies, _ = _case(count)
    active = tmp_path / "bundle"
    active.mkdir()
    (active / "active").write_text("prior", encoding="utf-8")
    result = _stage_signed_release_inactive_once(
        **_offline_inactive_args(args, bodies, root)
    )
    assert result["inactive_custody"] is True
    assert result["install_authorized"] is False
    assert result["owner_authority_proven"] is False
    assert result["rollback_verified"] is False
    assert result["original_client_ack"] is False
    target = root / COMMIT
    assert {p.name for p in target.iterdir()} == set(bodies)
    assert all((target / name).read_bytes() == body for name, body in bodies.items())
    assert all((target / name).stat().st_mode & 0o077 == 0 for name in bodies)
    assert (active / "active").read_text(encoding="utf-8") == "prior"

    old_inode = target.stat().st_ino
    with pytest.raises(ValueError, match="^fabric_signed_inactive_custody_unqualified$"):
        _stage_signed_release_inactive_once(**_offline_inactive_args(args, bodies, root))
    assert target.stat().st_ino == old_inode


@pytest.mark.parametrize("bad", ["signature", "digest", "asset", "root_symlink"])
def test_signed_inactive_stage_denies_bad_inputs_without_final_target(tmp_path, bad):
    from runner_mcp.fabric_release_inactive_custody import (
        _stage_signed_release_inactive_once,
    )

    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    args, bodies, _ = _case()
    options = _offline_inactive_args(args, bodies, root)
    if bad == "signature":
        options["signature"] = b"?" * 64
    elif bad == "digest":
        options["independently_trusted_key_sha256"] = "0" * 64
    elif bad == "asset":
        first = min(bodies)
        options["asset_bodies"] = {**bodies, first: bodies[first] + b"!"}
    else:
        redirect = tmp_path / "redirect"
        root.rename(redirect)
        root.symlink_to(redirect, target_is_directory=True)
    with pytest.raises(ValueError, match="^fabric_signed_inactive_custody_unqualified$"):
        _stage_signed_release_inactive_once(**options)
    assert not (root / COMMIT).exists()


def test_competing_inactive_stage_never_replaces_existing_target(tmp_path, monkeypatch):
    from runner_mcp import fabric_release_inactive_custody as custody

    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    args, bodies, _ = _case()
    original = custody._promote_inactive_bundle_noreplace

    def concurrent(root_path, incoming, commit):
        assert commit == COMMIT
        old = root / commit
        old.mkdir(mode=0o700)
        (old / "sentinel").write_text("keep", encoding="utf-8")
        return original(root_path, incoming, commit)

    monkeypatch.setattr(custody, "_promote_inactive_bundle_noreplace", concurrent)
    with pytest.raises(ValueError, match="^fabric_signed_inactive_custody_unqualified$"):
        custody._stage_signed_release_inactive_once(
            **_offline_inactive_args(args, bodies, root)
        )
    assert (root / COMMIT / "sentinel").read_text(encoding="utf-8") == "keep"
    assert any(p.name.startswith(".incoming-") for p in root.iterdir())


def test_interrupted_write_retains_partial_for_review_without_promotion(
    tmp_path, monkeypatch,
):
    from runner_mcp import fabric_release_inactive_custody as custody

    root = tmp_path / "local-bundles"
    root.mkdir(mode=0o700)
    args, bodies, _ = _case()
    original = custody.os.write
    count = [0]

    def interrupted(fd, content):
        count[0] += 1
        if count[0] == 2:
            raise OSError("simulated-incomplete-write")
        return original(fd, content)

    monkeypatch.setattr(custody.os, "write", interrupted)
    with pytest.raises(ValueError, match="^fabric_signed_inactive_custody_unqualified$"):
        custody._stage_signed_release_inactive_once(
            **_offline_inactive_args(args, bodies, root)
        )
    assert not (root / COMMIT).exists()
    assert len([p for p in root.iterdir() if p.name.startswith(".incoming-")]) == 1


def test_signed_inactive_stage_is_not_exported_to_mcp_or_update_flow():
    from runner_mcp.fabric_release_inactive_custody import (
        _stage_signed_release_inactive_once,
    )

    assert callable(_stage_signed_release_inactive_once)
    server = Path(__file__).resolve().parents[1] / "src/runner_mcp/server.py"
    manager = Path(__file__).resolve().parents[1] / "src/runner_mcp/fabric_update.py"
    for source in (server, manager):
        assert "_stage_signed_release_inactive_once" not in source.read_text("utf-8")


# F30 Release-description contract: gebruik dezelfde bestaande signed-byte fixtures.
_NOTES_V1 = "Exact Fabric release notes; never authorized to install."
_BEGIN_V1 = "\n\n-----BEGIN RUNNER-FABRIC SIGNED-RELEASE-ROSTER V1-----\n"
_END_V1 = "-----END RUNNER-FABRIC SIGNED-RELEASE-ROSTER V1-----\n"


def _body_for_signed_fixture(args):
    """Bouw alleen in-memory het door Fabric #924 gestandaardiseerde tekstblok."""
    values = (
        args["signed_document"], args["signature"], args["public_key"],
    )
    lines = (
        name + base64.b64encode(raw).decode("ascii") + "\n"
        for name, raw in zip(
            ("document=", "signature=", "public_key="), values, strict=True
        )
    )
    return _NOTES_V1 + _BEGIN_V1 + "".join(lines) + _END_V1


@pytest.mark.parametrize("count", [5, 33, 160])
def test_signed_fabric_description_matches_existing_verified_roster(count):
    from runner_mcp.fabric_release_body_envelope import verify_signed_release_body

    args, _, _ = _case(count)
    body = _body_for_signed_fixture(args)
    actual = verify_signed_release_body(
        body=body,
        independently_trusted_key_sha256=args["independently_trusted_key_sha256"],
        expected_commit=args["expected_commit"],
        expected_release_id=args["expected_release_id"],
        observed_metadata=args["observed_metadata"],
    )
    assert actual == (
        args["signed_document"], args["signature"], args["public_key"]
    )
    assert len(body.encode("utf-8")) < 100 * 1024
    assert body.count(_BEGIN_V1) == body.count(_END_V1) == 1


@pytest.mark.parametrize("bad", [
    "absent", "trailing", "duplicate", "embedded_cr", "bad_document",
    "bad_signature", "bad_public_key", "wrong_key_pin", "wrong_commit",
    "wrong_release_id", "metadata_mismatch", "bad_base64", "extra_line",
    "oversize_notes", "truncated", "noncanonical", "wrong_body_type",
])
def test_signed_description_fails_closed_without_import_or_stage(bad):
    from runner_mcp.fabric_release_body_envelope import (
        SignedBodyEnvelopeUnqualified,
        verify_signed_release_body,
    )

    args, _, _ = _case()
    body = _body_for_signed_fixture(args)
    values = {
        "body": body,
        "independently_trusted_key_sha256": args[
            "independently_trusted_key_sha256"
        ],
        "expected_commit": args["expected_commit"],
        "expected_release_id": args["expected_release_id"],
        "observed_metadata": args["observed_metadata"],
    }
    if bad == "absent":
        values["body"] = _NOTES_V1
    elif bad == "trailing":
        values["body"] += "forged-suffix"
    elif bad == "duplicate":
        values["body"] += _BEGIN_V1 + "document=fake\n"
    elif bad == "embedded_cr":
        values["body"] = values["body"].replace(
            _NOTES_V1, _NOTES_V1 + "\r"
        )
    elif bad == "bad_document":
        values["body"] = values["body"].replace(
            "document=", "document=AA", 1
        )
    elif bad == "bad_signature":
        values["body"] = values["body"].replace(
            "signature=", "signature=AA", 1
        )
    elif bad == "bad_public_key":
        values["body"] = values["body"].replace(
            "public_key=", "public_key=AA", 1
        )
    elif bad == "wrong_key_pin":
        values["independently_trusted_key_sha256"] = "f" * 64
    elif bad == "wrong_commit":
        values["expected_commit"] = "b" * 40
    elif bad == "wrong_release_id":
        values["expected_release_id"] = RELEASE_ID + 2
    elif bad == "metadata_mismatch":
        original = values["observed_metadata"]
        changed = replace(original.files[0], sha256="d" * 64)
        values["observed_metadata"] = replace(
            original, files=(changed, *original.files[1:])
        )
    elif bad == "bad_base64":
        values["body"] = values["body"].replace(
            "document=", "document=!", 1
        )
    elif bad == "extra_line":
        values["body"] = values["body"].replace(
            _END_V1, "injected=true\n" + _END_V1
        )
    elif bad == "oversize_notes":
        values["body"] = "x" * (8 * 1024 + 1) + values["body"]
    elif bad == "truncated":
        values["body"] = values["body"][:-5]
    elif bad == "noncanonical":
        values["body"] = values["body"].replace(
            "document=", "document=A", 1
        )
    else:
        values["body"] = b"bytes-not-text"

    with pytest.raises(
        SignedBodyEnvelopeUnqualified,
        match="^fabric_signed_release_body_unqualified$",
    ):
        verify_signed_release_body(**values)


def test_release_description_parser_is_private_and_has_no_network_or_stage():
    parser = (
        Path(__file__).resolve().parents[1]
        / "src/runner_mcp/fabric_release_body_envelope.py"
    ).read_text("utf-8")
    server = (
        Path(__file__).resolve().parents[1]
        / "src/runner_mcp/server.py"
    ).read_text("utf-8")
    assert "verify_signed_release_body" not in server
    for forbidden in (
        "start_local", "stage_local_bundle", "os.open", "urllib",
        "requests.", "subprocess", "systemctl", "github_token",
    ):
        assert forbidden not in parser
