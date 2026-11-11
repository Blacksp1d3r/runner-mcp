"""Read-only comparison of a GitHub Release inventory to independently held pins.

Do not derive trusted inputs from the Release/API payload being checked.
This function does not verify who signed the pins, download bytes, qualify a
host, persist artifacts, or authorize installation/agent dispatch.
"""
from __future__ import annotations

import hmac
import re
from dataclasses import dataclass

from .fabric_release_assets import ReleaseAdmission, ReleaseAsset

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.+\-]{0,150}\Z")
_REQUIRED = frozenset({"BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py"})
_MAX_ENTRY_BYTES = 64 * 1024 * 1024
_MAX_TOTAL_BYTES = 256 * 1024 * 1024
_Q7_ROSTER_SIZE = 33


class IndependentRosterMismatch(ValueError):
    """Fixed-denial category; no source, path, token or payload detail."""


@dataclass(frozen=True, slots=True)
class PinnedReleaseAsset:
    name: str
    asset_id: int
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class PinnedReleaseRoster:
    commit: str
    tag: str
    release_id: int
    files: tuple[PinnedReleaseAsset, ...]


def _deny() -> None:
    raise IndependentRosterMismatch("fabric_release_independent_roster_unqualified")


def _validate_pins(pins: PinnedReleaseRoster) -> None:
    if (
        type(pins) is not PinnedReleaseRoster
        or type(pins.commit) is not str
        or _HEX40.fullmatch(pins.commit) is None
        or pins.tag != "fabric-q7-bundle-" + pins.commit
        or type(pins.release_id) is not int
        or pins.release_id <= 0
        or type(pins.files) is not tuple
        or len(pins.files) != _Q7_ROSTER_SIZE
    ):
        _deny()
    names: set[str] = set()
    ids: set[int] = set()
    total = 0
    for pin in pins.files:
        if (
            type(pin) is not PinnedReleaseAsset
            or type(pin.name) is not str
            or _SAFE_NAME.fullmatch(pin.name) is None
            or pin.name in names
            or type(pin.asset_id) is not int
            or pin.asset_id <= 0
            or pin.asset_id in ids
            or type(pin.bytes) is not int
            or not 0 < pin.bytes <= _MAX_ENTRY_BYTES
            or type(pin.sha256) is not str
            or _HEX64.fullmatch(pin.sha256) is None
            or not (pin.name in _REQUIRED or pin.name.endswith(".whl"))
        ):
            _deny()
        total += pin.bytes
        if total > _MAX_TOTAL_BYTES:
            _deny()
        names.add(pin.name)
        ids.add(pin.asset_id)
    wheels = [name for name in names if name.endswith(".whl")]
    if (
        not _REQUIRED.issubset(names)
        or len(wheels) != len(names) - len(_REQUIRED)
        or sum(name.startswith("runner_fabric-") for name in wheels) != 1
    ):
        _deny()


def compare_exact_pinned_q7_roster(
    observed: ReleaseAdmission,
    independently_held: PinnedReleaseRoster,
) -> dict[str, object]:
    """Compare 33/33 fixed IDs, names, sizes and hashes without any I/O.

    'match' is structural comparison only, not authenticated signer evidence.
    A caller may NOT use the result by itself as release or mutation authority.
    """
    _validate_pins(independently_held)
    if (
        type(observed) is not ReleaseAdmission
        or observed.commit != independently_held.commit
        or observed.tag != independently_held.tag
        or type(observed.release_id) is not int
        or observed.release_id != independently_held.release_id
        or type(observed.files) is not tuple
        or len(observed.files) != _Q7_ROSTER_SIZE
    ):
        _deny()
    expected = {item.name: item for item in independently_held.files}
    if len(expected) != _Q7_ROSTER_SIZE:
        _deny()
    expected_project_wheel = next(
        name for name in expected if name.startswith("runner_fabric-")
    )
    if observed.project_wheel != expected_project_wheel:
        _deny()
    seen: set[str] = set()
    for asset in observed.files:
        if type(asset) is not ReleaseAsset or type(asset.name) is not str:
            _deny()
        pin = expected.get(asset.name)
        if (
            pin is None
            or asset.name in seen
            or type(asset.asset_id) is not int
            or asset.asset_id != pin.asset_id
            or type(asset.bytes) is not int
            or asset.bytes != pin.bytes
            or type(asset.sha256) is not str
            or _HEX64.fullmatch(asset.sha256) is None
            or not hmac.compare_digest(asset.sha256, pin.sha256)
        ):
            _deny()
        seen.add(asset.name)
    if seen != set(expected):
        _deny()
    return {
        "comparison": "match_only",
        "asset_count": _Q7_ROSTER_SIZE,
        "trusted_signer_verified": False,
        "download_performed": False,
        "mutation_authorized": False,
        "original_client_ack": False,
    }
