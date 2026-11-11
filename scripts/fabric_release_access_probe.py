"""Bounded, operator-interactive GitHub Release metadata ACCESS probe.

Runs without installed Runner-MCP/Fabric and never downloads assets, stages,
installs, enrolls, activates, or authorizes any mutation. A successful read
is not trusted release content or a host qualification receipt.
"""
from __future__ import annotations

import getpass
import http.client
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Any

_COMMIT = "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
_TAG = "fabric-q7-bundle-" + _COMMIT
_URL = "https://api.github.com/repos/Blacksp1d3r/Runner-Fabric/releases/tags/" + _TAG
_MAX_JSON_BYTES = 256 * 1024
_MAX_TOKEN_CHARS = 512


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _parse_release(payload: bytes) -> bool:
    try:
        obj = json.loads(payload.decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (UnicodeError, ValueError, RecursionError):
        return False
    return (
        isinstance(obj, dict)
        and type(obj.get("id")) is int
        and obj["id"] > 0
        and obj.get("tag_name") == _TAG
        and obj.get("target_commitish") == _COMMIT
        and obj.get("draft") is False
        and obj.get("prerelease") is True
        and isinstance(obj.get("assets"), list)
        and len(obj["assets"]) == 33
    )


def probe_metadata_access(token: str, *, opener: Any | None = None) -> str:
    """Safe category: only exact prerelease metadata readable, never install-ready.

    The optional opener is an offline test injection. Normal transport blocks
    environment proxies and ALL HTTP redirects before attaching Authorization.
    """
    if (
        type(token) is not str
        or not 8 <= len(token) <= _MAX_TOKEN_CHARS
        or re.fullmatch(r"[\x21-\x7e]+", token) is None
    ):
        return "WAIT_TOKEN_INVALID"
    client = opener if opener is not None else urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect()
    )
    request = urllib.request.Request(
        _URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "runner-mcp-readonly-release-access-probe",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with client.open(request, timeout=8) as response:
            if getattr(response, "status", None) != 200:
                return "WAIT_HTTP_UNAVAILABLE"
            declared = getattr(response, "headers", {}).get("Content-Length")
            if declared is not None and (
                not isinstance(declared, str)
                or re.fullmatch(r"[0-9]{1,9}", declared) is None
                or not 0 < int(declared) <= _MAX_JSON_BYTES
            ):
                return "WAIT_RESPONSE_UNQUALIFIED"
            content = response.read(_MAX_JSON_BYTES + 1)
            if len(content) > _MAX_JSON_BYTES or (
                declared is not None and len(content) != int(declared)
            ):
                return "WAIT_RESPONSE_UNQUALIFIED"
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return "WAIT_AUTHENTICATION"
        if exc.code == 403:
            return "WAIT_AUTHORIZATION_OR_RATE_LIMIT"
        if exc.code == 404:
            return "WAIT_RELEASE_NOT_ACCESSIBLE"
        return "WAIT_HTTP_UNAVAILABLE"
    except (urllib.error.URLError, http.client.HTTPException, OSError, TimeoutError, ValueError):
        return "WAIT_TRANSPORT_UNAVAILABLE"

    return "PASS_METADATA_READ" if _parse_release(content) else "WAIT_RESPONSE_UNQUALIFIED"


def _can_prompt() -> bool:
    return sys.stdin.isatty() and sys.stderr.isatty()


def main() -> int:
    if len(sys.argv) != 1:
        print("WAIT_ARGUMENTS_UNSUPPORTED")
        return 1
    if not _can_prompt():
        print("WAIT_INTERACTIVE_TERMINAL_REQUIRED")
        return 1
    # No credential via argv/env/stdin pipe. getpass requires an interactive tty.
    # Python str memory cannot be guaranteed to be securely zeroized.
    try:
        token = getpass.getpass("One-time read-only GitHub token (hidden): ")
    except (EOFError, KeyboardInterrupt):
        print("WAIT_INPUT_UNAVAILABLE")
        return 1
    try:
        result = probe_metadata_access(token)
    finally:
        del token
    print(result)
    print("NO_DOWNLOAD_NO_INSTALL_NO_ACTIVATION")
    return 0 if result == "PASS_METADATA_READ" else 1


if __name__ == "__main__":
    raise SystemExit(main())
