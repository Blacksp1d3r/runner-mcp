"""Read-only, fail-closed concurrent patch-release preflight (#662).

This is NOT an atomic lock. Only a required GitHub check combined with a
merge queue or up-to-date protection and a single release steward can
prevent check-to-merge races.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from check_release_version import needs_bump, version_tuple

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = "Blacksp1d3r/runner-mcp"
MAX_PAGES = 4
MAX_RESPONSE = 8 * 1024 * 1024
MAX_META = 32 * 1024


class AdmissionError(ValueError):
    pass


def validate(
    *,
    main_sha: str,
    event_base_sha: str,
    event_head_sha: str,
    checkout_pr_sha: str,
    main_version: str,
    proposed_version: str,
    competing_versions: dict[int, str],
    own_number: int,
) -> None:
    if not all(
        isinstance(s, str) and SHA.fullmatch(s)
        for s in (main_sha, event_base_sha, event_head_sha, checkout_pr_sha)
    ):
        raise AdmissionError("revision unavailable")
    if main_sha != event_base_sha:
        raise AdmissionError("main advanced; current base required")
    if checkout_pr_sha != event_head_sha:
        raise AdmissionError("tested merge does not match PR head")
    if type(own_number) is not int or own_number < 1:
        raise AdmissionError("PR number unavailable")
    base = version_tuple(main_version)
    proposed = version_tuple(proposed_version)
    if proposed[:2] != base[:2] or proposed[2] != base[2] + 1:
        raise AdmissionError("candidate is not the next patch after main")
    for number, version in competing_versions.items():
        if type(number) is not int or number < 1 or number == own_number:
            raise AdmissionError("invalid competing PR")
        # Deterministic arbitration: the oldest numbered READY, main-targeted
        # PR wins a duplicate candidate. Newer contenders WAIT and must rebase
        # or be reassigned by the one release steward. This avoids deadlocking
        # two ready feature PRs. It is not a cross-PR atomic merge lease.
        if version_tuple(version) == proposed and number < own_number:
            raise AdmissionError("next patch already prioritized to PR #" + str(number))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise AdmissionError("duplicate JSON property")
        output[key] = value
    return output


def _json(raw: bytes) -> object:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise AdmissionError("invalid JSON evidence") from exc


def _project_version(raw: bytes) -> str:
    try:
        value = tomllib.loads(raw.decode("utf-8"))["project"]["version"]
        version_tuple(value)
        return value
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise AdmissionError("unknown source package version") from exc


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _api(path: str, token: str) -> object:
    if not path.startswith("/repos/" + REPO + "/"):
        raise AdmissionError("outside release repository")
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "runner-mcp-release-reservation",
        },
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=12) as response:
            if response.status != 200:
                raise AdmissionError("read-only release evidence unavailable")
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise AdmissionError("release evidence oversized")
        return _json(raw)
    except (OSError, urllib.error.HTTPError, TimeoutError) as exc:
        raise AdmissionError("GitHub evidence unavailable") from exc


def _main_head(token: str) -> str:
    response = _api("/repos/" + REPO + "/branches/main", token)
    commit = response.get("commit") if isinstance(response, dict) else None
    sha = commit.get("sha") if isinstance(commit, dict) else None
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise AdmissionError("main commit unavailable")
    return sha


def _check_current_pr(token: str, number: int, main_sha: str, head_sha: str) -> None:
    """Re-read the exact current PR from trusted GitHub, not old event JSON."""
    if type(number) is not int or number < 1:
        raise AdmissionError("invalid own PR number")
    pr = _api("/repos/" + REPO + "/pulls/" + str(number), token)
    if not isinstance(pr, dict) or pr.get("number") != number:
        raise AdmissionError("current PR identity unavailable")
    base, head = pr.get("base"), pr.get("head")
    if (
        pr.get("state") != "open"
        or pr.get("draft") is not False
        or not isinstance(base, dict)
        or base.get("ref") != "main"
        or base.get("sha") != main_sha
        or not isinstance(head, dict)
        or head.get("sha") != head_sha
    ):
        raise AdmissionError("current PR branch, base or readiness changed")


def _version_at(token: str, sha: str) -> str:
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise AdmissionError("unverified competing revision")
    response = _api(
        "/repos/" + REPO + "/contents/pyproject.toml?ref=" + sha, token
    )
    if not isinstance(response, dict) or response.get("encoding") != "base64":
        raise AdmissionError("metadata content unavailable")
    text = response.get("content")
    if not isinstance(text, str) or len(text) > MAX_META * 2:
        raise AdmissionError("oversized source metadata")
    try:
        raw = base64.b64decode(text.replace("\n", ""), validate=True)
    except (ValueError, TypeError) as exc:
        raise AdmissionError("unreadable source metadata") from exc
    if len(raw) > MAX_META:
        raise AdmissionError("oversized source metadata")
    return _project_version(raw)


def _contenders(token: str, own_number: int) -> dict[int, str]:
    contenders: dict[int, str] = {}
    seen_numbers: set[int] = set()
    for page in range(1, MAX_PAGES + 1):
        data = _api(
            "/repos/" + REPO + "/pulls?state=open&per_page=100&page=" + str(page),
            token,
        )
        if not isinstance(data, list):
            raise AdmissionError("PR inventory unavailable")
        for row in data:
            if not isinstance(row, dict):
                raise AdmissionError("invalid PR inventory")
            number, head, base = row.get("number"), row.get("head"), row.get("base")
            if type(number) is not int or number < 1 or number in seen_numbers:
                raise AdmissionError("PR inventory identity unavailable or duplicated")
            seen_numbers.add(number)
            if (
                row.get("state") != "open"
                or type(row.get("draft")) is not bool
                or not isinstance(base, dict)
                or not isinstance(base.get("ref"), str)
            ):
                raise AdmissionError("PR inventory state is incomplete")
            if number == own_number or row["draft"]:
                continue
            if base["ref"] != "main":
                continue
            sha = head.get("sha") if isinstance(head, dict) else None
            contenders[number] = _version_at(token, sha)
        if len(data) < 100:
            return contenders
    raise AdmissionError("PR inventory too large for supported audit")


def _git(*parts: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *parts], stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8").strip()
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        raise AdmissionError("local checkout unavailable") from exc


def run() -> str:
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return "SKIP non-PR"
    if os.environ.get("GITHUB_REPOSITORY") != REPO:
        raise AdmissionError("wrong repository")
    path, token = os.environ.get("GITHUB_EVENT_PATH"), os.environ.get("GITHUB_TOKEN")
    if not path or not token:
        raise AdmissionError("GitHub evidence authority unavailable")
    try:
        file = Path(path)
        if file.stat().st_size > MAX_RESPONSE:
            raise AdmissionError("PR event oversized")
        event = _json(file.read_bytes())
    except OSError as exc:
        raise AdmissionError("PR event unavailable") from exc
    pr = event.get("pull_request") if isinstance(event, dict) else None
    if not isinstance(pr, dict):
        raise AdmissionError("PR identity unavailable")
    number, base, head = pr.get("number"), pr.get("base"), pr.get("head")
    if (
        type(number) is not int or number < 1
        or not isinstance(base, dict) or base.get("ref") != "main"
        or not isinstance(head, dict)
        or not isinstance(base.get("sha"), str)
        or not isinstance(head.get("sha"), str)
    ):
        raise AdmissionError("PR must target main with verified identities")
    if not needs_bump(
        _git("diff", "--no-renames", "--name-only", base["sha"], "HEAD").splitlines()
    ):
        return "SKIP docs-only"
    candidate_sha = _git("rev-parse", "HEAD^2")
    main_sha = _main_head(token)
    _check_current_pr(token, number, main_sha, head["sha"])
    validate(
        main_sha=main_sha,
        event_base_sha=base["sha"],
        event_head_sha=head["sha"],
        checkout_pr_sha=candidate_sha,
        main_version=_version_at(token, main_sha),
        proposed_version=_project_version(Path("pyproject.toml").read_bytes()),
        competing_versions=_contenders(token, number),
        own_number=number,
    )
    # Candidate head, draft/ready state and base may change even if main
    # itself stays fixed; check both sides again before returning admission.
    _check_current_pr(token, number, main_sha, head["sha"])
    if _main_head(token) != main_sha:
        raise AdmissionError("main advanced during release preflight")
    return "PASS unique next patch on current main"


def main() -> int:
    try:
        result = run()
    except (AdmissionError, OSError, ValueError, TypeError) as exc:
        print("RELEASE_RESERVATION_GATE: WAIT/FAIL (" + str(exc) + ")", file=sys.stderr)
        return 1
    print("RELEASE_RESERVATION_GATE: " + result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
