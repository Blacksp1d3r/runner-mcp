from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from runner_mcp.offline_installed_record_preflight import offline_installed_record_preflight
from runner_mcp.offline_receipt_writer import write_offline_receipt_candidate
from runner_mcp.offline_signed_evidence import offline_signed_installed_record_preflight

_DIST = "aifordable_runner_mcp-0.1.40.dist-info"
_RECORD = f"{_DIST}/RECORD"


def _record_row(name: str, content: bytes) -> list[str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
    return [name, f"sha256={digest}", str(len(content))]


def _record_bytes(files: dict[str, bytes], *, extra: bool = False) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for name, content in sorted(files.items()):
        writer.writerow(_record_row(name, content))
    writer.writerow([_RECORD, "", ""])
    if extra:
        # pip's installed RECORD can include scripts outside site-packages.
        writer.writerow(["../../../bin/runner-mcp", "", ""])
    return stream.getvalue().encode()


def _fixture(tmp_path: Path) -> tuple[Path, Path, str, dict[str, bytes]]:
    files = {
        "runner_mcp/__init__.py": b"__version__ = '0.1.40'\n",
        "runner_mcp/module.py": b"VALUE = 123\n",
        f"{_DIST}/METADATA": b"Name: aifordable-runner-mcp\nVersion: 0.1.40\n",
        f"{_DIST}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n",
    }
    root = tmp_path / "private-generation" / "site-packages"
    root.mkdir(parents=True)
    package = root / "runner_mcp"
    package.mkdir()
    for name, data in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (root / _RECORD).write_bytes(_record_bytes(files, extra=True))

    wheel = tmp_path / "candidate.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr(_RECORD, _record_bytes(files))
    return wheel, package, hashlib.sha256(wheel.read_bytes()).hexdigest(), files


def test_offline_wheel_and_installed_record_match_is_not_live_proof(tmp_path: Path) -> None:
    wheel, package, wheel_digest, _ = _fixture(tmp_path)
    result = offline_installed_record_preflight(wheel, package, wheel_digest)
    assert result == {
        "schema_version": "runner-mcp/offline-installed-record/v1",
        "state": "offline_installed_record_match",
        "active_build_provenance_verified": False,
        "source_revision": None,
        "artifact_digest": None,
    }


@pytest.mark.parametrize(
    "tamper",
    [
        "bad_pin",
        "changed_package",
        "changed_metadata",
        "missing_record",
        "record_hash",
        "record_duplicate",
        "record_extra_module",
        "unlisted_module",
        "unlisted_native",
        "linked_module",
        "wheel_changed_same_version",
        "duplicate_wheel_member",
        "linked_package",
    ],
)
def test_offline_record_denies_tampering(
    tmp_path: Path, tamper: str
) -> None:
    wheel, package, digest, files = _fixture(tmp_path)
    root = package.parent
    if tamper == "bad_pin":
        digest = "f" * 64
    elif tamper == "changed_package":
        (package / "module.py").write_bytes(b"VALUE = 999\n")
    elif tamper == "changed_metadata":
        (root / _DIST / "METADATA").write_bytes(b"Version: 0.1.40\nModified: yes\n")
    elif tamper == "missing_record":
        (root / _RECORD).unlink()
    elif tamper == "record_hash":
        (root / _RECORD).write_bytes(_record_bytes({**files, "runner_mcp/module.py": b"wrong"}))
    elif tamper == "record_duplicate":
        with (root / _RECORD).open("ab") as stream:
            stream.write(("runner_mcp/module.py,sha256=" + "x" * 43 + ",12\n").encode())
    elif tamper == "record_extra_module":
        with (root / _RECORD).open("ab") as stream:
            stream.write(("runner_mcp/extra.py,sha256=" + "x" * 43 + ",12\n").encode())
    elif tamper == "unlisted_module":
        (package / "extra.py").write_bytes(b"EXTRA = True\n")
    elif tamper == "unlisted_native":
        (package / "module.so").write_bytes(b"extra native code")
    elif tamper == "linked_module":
        (package / "module.py").unlink()
        (package / "module.py").symlink_to(root / _DIST / "METADATA")
    elif tamper == "wheel_changed_same_version":
        with zipfile.ZipFile(wheel, "a") as archive:
            archive.writestr("added_file.txt", b"same version, different wheel")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    elif tamper == "duplicate_wheel_member":
        with zipfile.ZipFile(wheel, "a") as archive:
            archive.writestr("runner_mcp/module.py", b"VALUE = 123\n")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    elif tamper == "linked_package":
        other = root / "other"
        other.mkdir()
        for file in package.iterdir():
            (other / file.name).write_bytes(file.read_bytes())
        for file in package.iterdir():
            file.unlink()
        package.rmdir()
        package.symlink_to(other, target_is_directory=True)
    else:
        raise AssertionError("unknown fixture")

    result = offline_installed_record_preflight(wheel, package, digest)
    assert result["state"] == "unverified"
    assert result["active_build_provenance_verified"] is False
    assert result["source_revision"] is None
    assert result["artifact_digest"] is None


def test_offline_record_refuses_caller_supplied_unbounded_input(tmp_path: Path) -> None:
    wheel, package, digest, _ = _fixture(tmp_path)
    assert offline_installed_record_preflight(wheel, package, "invalid")["state"] == "unverified"
    assert offline_installed_record_preflight(wheel, Path("."), digest)["state"] == "unverified"
    assert offline_installed_record_preflight(Path("/not-existing.whl"), package, digest)[
        "state"
    ] == "unverified"



def _signed_fixture(tmp_path: Path) -> tuple[object, ...]:
    wheel, package, digest, files = _fixture(tmp_path)
    revision = "a" * 40
    generation = tmp_path / f"generation-{revision}-{digest}"
    generation.mkdir(mode=0o700)
    shutil.move(str(package.parent), str(generation / "site-packages"))
    package = generation / "site-packages" / "runner_mcp"
    receipt = tmp_path / "receipt.json"
    assert write_offline_receipt_candidate(
        receipt,
        {
            "schema_version": "runner-mcp/offline-artifact-receipt/v1",
            "source_revision": revision,
            "wheel_sha256": digest,
            "modules": {
                key.removeprefix("runner_mcp/"): hashlib.sha256(data).hexdigest()
                for key, data in files.items() if key.startswith("runner_mcp/")
            },
        },
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "runner-mcp/builder-manifest/v1",
                "source_revision": revision,
                "distribution_version": "0.1.40",
                "wheel_sha256": digest,
                "interface_schema_digest": "b" * 64,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    signer = Ed25519PrivateKey.generate()
    public_bytes = signer.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub = tmp_path / "signer.pub"
    pub.write_bytes(public_bytes)
    signature = tmp_path / "manifest.sig"
    signature.write_bytes(signer.sign(manifest.read_bytes()))
    return (
        manifest, receipt, wheel, package, generation,
        hashlib.sha256(manifest.read_bytes()).hexdigest(),
        pub, signature, hashlib.sha256(public_bytes).hexdigest(),
    )


def test_signed_manifest_and_record_still_do_not_attest_live_process(tmp_path: Path):
    evidence = _signed_fixture(tmp_path)
    response = offline_signed_installed_record_preflight(*evidence)
    assert response["state"] == "offline_signed_installed_record_match"
    assert response["active_build_provenance_verified"] is False
    assert response["source_revision"] is None
    assert response["artifact_digest"] is None


@pytest.mark.parametrize("broken", ["installed-record", "module", "signer"])
def test_signed_record_chain_rejects_tampering(tmp_path: Path, broken: str):
    evidence = _signed_fixture(tmp_path)
    if broken == "installed-record":
        (evidence[3].parent / _RECORD).write_bytes(b"malformed")
    elif broken == "module":
        (evidence[3] / "module.py").write_bytes(b"VALUE = forged\n")
    else:
        evidence[7].write_bytes(b"forged")
    response = offline_signed_installed_record_preflight(*evidence)
    assert response["state"] == "unverified"
    assert response["active_build_provenance_verified"] is False
