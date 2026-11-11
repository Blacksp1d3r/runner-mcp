"""Untrusted GitHub Release metadata never authorizes a Fabric update."""

from __future__ import annotations

from copy import deepcopy

import pytest

from runner_mcp.fabric_release_assets import (
    FabricReleaseAdmissionError,
    inspect_exact_release,
)

COMMIT = "a" * 40
PREFIX = "fabric-q7-bundle-"


def _fixture() -> tuple[dict, dict]:
    names = (
        "BUNDLE.json",
        "BOOTSTRAP.py",
        "COMMIT_SHA",
        "SHA256SUMS",
        "runner_fabric-0.0.1-py3-none-any.whl",
    )
    release = {
        "id": 123,
        "tag_name": PREFIX + COMMIT,
        "target_commitish": COMMIT,
        "draft": False,
        "prerelease": True,
        "assets": [
            {"id": n + 1, "name": name, "size": 10, "digest": "sha256:" + "b" * 64}
            for n, name in enumerate(names)
        ],
        # These untrusted URL fields are never processed or returned.
        "upload_url": "http://127.0.0.1/secret",
    }
    ref = {
        "ref": "refs/tags/" + PREFIX + COMMIT,
        "object": {"type": "commit", "sha": COMMIT},
    }
    return release, ref


def test_exact_pinned_release_is_classified_without_download_authority() -> None:
    release, ref = _fixture()
    admitted = inspect_exact_release(COMMIT, release, ref)
    assert admitted.project_wheel == "runner_fabric-0.0.1-py3-none-any.whl"
    assert len(admitted.files) == 5
    assert admitted.files[0].name == "BOOTSTRAP.py"
    assert admitted.public_dict() == {
        "state": "ready",
        "source": "github-release",
        "commit": COMMIT,
        "asset_count": 5,
        "project_wheel_sha256": "b" * 64,
        "mutation_authorized": False,
        "download_performed": False,
    }
    assert "127.0.0.1" not in repr(admitted)


def test_generic_tag_is_supported_without_arbitrary_tag_selection() -> None:
    release, ref = _fixture()
    release["tag_name"] = "fabric-update-bundle-" + COMMIT
    ref["ref"] = "refs/tags/" + release["tag_name"]
    assert inspect_exact_release(COMMIT, release, ref).release_id == 123


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r, t: r.update(tag_name="fabric-other-" + COMMIT),
        lambda r, t: r.update(target_commitish="c" * 40),
        lambda r, t: r.update(draft=True),
        lambda r, t: r.update(prerelease=False),
        lambda r, t: r.update(id=True),
        lambda r, t: t.update(ref="refs/tags/not-approved"),
        lambda r, t: t["object"].update(type="tag"),
        lambda r, t: t["object"].update(sha="c" * 40),
        lambda r, t: r.update(assets=[]),
        lambda r, t: r["assets"].pop(),
        lambda r, t: r["assets"].append(deepcopy(r["assets"][0])),
        lambda r, t: r["assets"][0].update(id=r["assets"][1]["id"]),
        lambda r, t: r["assets"][0].update(name="../private/file"),
        lambda r, t: r["assets"][0].update(name="secrets.env"),
        lambda r, t: r["assets"][0].update(size=0),
        lambda r, t: r["assets"][0].update(size=64 * 1024 * 1024 + 1),
        lambda r, t: r["assets"][0].update(digest="sha256:" + "z" * 64),
        lambda r, t: r["assets"][0].update(digest=None),
        lambda r, t: r["assets"][-1].update(name="other_project-0.0.1-py3-none-any.whl"),
    ],
)
def test_forged_or_incomplete_release_fails_closed(mutation) -> None:
    release, ref = _fixture()
    mutation(release, ref)
    with pytest.raises(
        FabricReleaseAdmissionError, match="^fabric_release_assets_unqualified$"
    ):
        inspect_exact_release(COMMIT, release, ref)


@pytest.mark.parametrize("commit", ["", "A" * 40, "0" * 39, "x" * 40, None])
def test_invalid_exact_source_does_not_leak_details(commit) -> None:
    release, ref = _fixture()
    with pytest.raises(FabricReleaseAdmissionError):
        inspect_exact_release(commit, release, ref)


def test_no_mutation_of_caller_metadata_or_returned_urls() -> None:
    release, ref = _fixture()
    saved = deepcopy((release, ref))
    inspected = inspect_exact_release(COMMIT, release, ref)
    assert (release, ref) == saved
    assert "http" not in repr(inspected)
