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

from runner_mcp.fabric_release_assets import ReleaseAdmission, ReleaseAsset
from runner_mcp.fabric_release_independent_roster import PinnedReleaseAsset, PinnedReleaseRoster
from runner_mcp.fabric_release_wheelhouse import (
    WheelhouseUnqualified,
    verify_pinned_q7_wheelhouse,
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
