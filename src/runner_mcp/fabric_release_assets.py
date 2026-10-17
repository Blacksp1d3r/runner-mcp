"""Read-only fixed-repository Fabric GitHub Release asset admission.

No mutable downloader, remote URL authority, staging or runtime installation.
The GitHub API responses are untrusted even when fetched by a credentialed
first-party transport. Source pin, tag ref, asset identity and immutable digest
must agree before any future fixed-source local-custody importer may use them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.+\-]{0,150}\Z")
_REQUIRED = frozenset({"BUNDLE.json", "COMMIT_SHA", "SHA256SUMS", "BOOTSTRAP.py"})
_MAX_FILES = 160
_MAX_FILE_BYTES = 64 * 1024 * 1024
_MAX_BYTES = 256 * 1024 * 1024
_TAG_PREFIXES = ("fabric-q7-bundle-", "fabric-update-bundle-")


class FabricReleaseAdmissionError(RuntimeError):
    """Constant denial reason without origin paths, tokens or URLs."""


@dataclass(frozen=True)
class ReleaseAsset:
    asset_id: int
    name: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class ReleaseAdmission:
    commit: str
    tag: str
    release_id: int
    files: tuple[ReleaseAsset, ...]
    project_wheel: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "state": "ready",
            "source": "github-release",
            "commit": self.commit,
            "asset_count": len(self.files),
            "project_wheel_sha256": next(
                item.sha256 for item in self.files
                if item.name == self.project_wheel
            ),
            "mutation_authorized": False,
            "download_performed": False,
        }


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _deny() -> None:
    raise FabricReleaseAdmissionError("fabric_release_assets_unqualified")


def inspect_exact_release(
    commit: str,
    release: object,
    tag_ref: object,
) -> ReleaseAdmission:
    """Admit only an exact-tag, exact-source, digest-covered fixed Fabric set.

    Caller must separately use the hardcoded Runner-Fabric GitHub API owner,
    and fetch the matching tag reference from the same repository. No provided
    browser URL, asset API URL, storage root or host is followed here.
    """
    if not isinstance(commit, str) or _COMMIT.fullmatch(commit) is None:
        _deny()
    if not isinstance(release, dict) or not isinstance(tag_ref, dict):
        _deny()
    tag = release.get("tag_name")
    if (
        not isinstance(tag, str)
        or tag not in {prefix + commit for prefix in _TAG_PREFIXES}
        or release.get("target_commitish") != commit
        or release.get("draft") is not False
        or release.get("prerelease") is not True
        or not _positive(release.get("id"))
    ):
        _deny()

    tagged = tag_ref.get("object")
    if (
        tag_ref.get("ref") != "refs/tags/" + tag
        or not isinstance(tagged, dict)
        or tagged.get("type") != "commit"
        or tagged.get("sha") != commit
    ):
        _deny()

    source = release.get("assets")
    if not isinstance(source, list) or not 5 <= len(source) <= _MAX_FILES:
        _deny()
    seen_names: set[str] = set()
    seen_ids: set[int] = set()
    files: list[ReleaseAsset] = []
    total = 0
    for raw in source:
        if not isinstance(raw, dict):
            _deny()
        name, asset_id = raw.get("name"), raw.get("id")
        size, digest = raw.get("size"), raw.get("digest")
        if (
            not isinstance(name, str)
            or _NAME.fullmatch(name) is None
            or name in seen_names
            or not _positive(asset_id)
            or asset_id in seen_ids
            or not _positive(size)
            or size > _MAX_FILE_BYTES
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
            or not (name.endswith(".whl") or name in _REQUIRED)
        ):
            _deny()
        seen_names.add(name)
        seen_ids.add(asset_id)
        total += size
        if total > _MAX_BYTES:
            _deny()
        files.append(ReleaseAsset(asset_id, name, size, digest.removeprefix("sha256:")))
    wheels = {f.name for f in files if f.name.endswith(".whl")}
    project = [name for name in wheels if name.startswith("runner_fabric-")]
    if not _REQUIRED.issubset(seen_names) or len(project) != 1 or len(wheels) != len(files) - len(_REQUIRED):
        _deny()
    files.sort(key=lambda a: a.name)
    return ReleaseAdmission(commit, tag, release["id"], tuple(files), project[0])
