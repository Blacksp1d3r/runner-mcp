from __future__ import annotations

import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

MAX_HEALTH_URL_BYTES = 2_048
MAX_HEALTH_RESPONSE_BYTES = 32_768
_HEALTH_TIMEOUT_SECONDS = 2.0


class TunnelHealthEvidenceError(RuntimeError):
    """Bounded local tunnel-health evidence failure without private details."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _read_private_health_url(config_dir: Path) -> str | None:
    path = config_dir.expanduser().resolve() / "tunnel-health.url"
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink():
        raise TunnelHealthEvidenceError("tunnel health evidence path is unsafe")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TunnelHealthEvidenceError(
            "tunnel health evidence could not be opened safely"
        ) from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise TunnelHealthEvidenceError("tunnel health evidence path is unsafe")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise TunnelHealthEvidenceError(
                "tunnel health evidence permissions are unsafe"
            )
        if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
            raise TunnelHealthEvidenceError("tunnel health evidence owner is unsafe")
        if info.st_size > MAX_HEALTH_URL_BYTES:
            raise TunnelHealthEvidenceError("tunnel health evidence is oversized")
        raw = os.read(fd, MAX_HEALTH_URL_BYTES + 1)
    finally:
        os.close(fd)

    if len(raw) > MAX_HEALTH_URL_BYTES:
        raise TunnelHealthEvidenceError("tunnel health evidence is oversized")
    try:
        value = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise TunnelHealthEvidenceError(
            "tunnel health evidence is not valid UTF-8"
        ) from exc
    if not value:
        raise TunnelHealthEvidenceError("tunnel health evidence is empty")
    return value


def _local_health_component_url(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != "http":
        raise TunnelHealthEvidenceError("tunnel health evidence is not loopback HTTP")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise TunnelHealthEvidenceError("tunnel health evidence URL is unsafe")
    if (parsed.hostname or "").lower() != "127.0.0.1":
        raise TunnelHealthEvidenceError("tunnel health evidence is not fixed loopback HTTP")
    try:
        port = parsed.port
    except ValueError as exc:
        raise TunnelHealthEvidenceError("tunnel health evidence URL is invalid") from exc
    if port is None or not 1 <= port <= 65_535:
        raise TunnelHealthEvidenceError("tunnel health evidence URL is invalid")
    if parsed.path not in {"", "/"}:
        raise TunnelHealthEvidenceError("tunnel health evidence URL is invalid")
    return f"http://127.0.0.1:{port}/health/mcp"


def _decode_component_payload(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_HEALTH_RESPONSE_BYTES:
        raise TunnelHealthEvidenceError("tunnel health response is oversized")
    try:
        text = raw.decode("utf-8")
        payload = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise TunnelHealthEvidenceError(
            "tunnel health response is invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise TunnelHealthEvidenceError("tunnel health response is invalid")
    return payload


def _open_loopback(request: urllib.request.Request, *, timeout: float):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(request, timeout=timeout)


def collect_local_mcp_ready(
    config_dir: Path,
    *,
    opener=_open_loopback,
) -> bool:
    """Probe only the tunnel-client's fixed loopback MCP health component."""

    base_url = _read_private_health_url(config_dir)
    if base_url is None:
        return False
    url = _local_health_component_url(base_url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with opener(request, timeout=_HEALTH_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_HEALTH_RESPONSE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return False

    payload = _decode_component_payload(raw)
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        return False
    if payload.get("component") != "mcp":
        return False
    if payload.get("status") != "ok":
        return False
    return payload.get("state") in {"initialized", "discovered"}
