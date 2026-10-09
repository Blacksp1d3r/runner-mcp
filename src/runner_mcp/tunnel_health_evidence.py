from __future__ import annotations

import json
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

MAX_HEALTH_URL_BYTES = 2_048
MAX_HEALTH_RESPONSE_BYTES = 32_768
_HEALTH_TIMEOUT_SECONDS = 2.0
_INSTANCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$"
)
# tunnel-client's documented default is a 30-second long poll plus 5-second
# deadline guard. Three nominal polls (90s) is a bounded freshness policy,
# NOT a claim that custom longer poll configurations remain accepted.
_MAX_CONTROL_PLANE_AUTH_AGE = timedelta(seconds=90)
_MAX_CONTROL_PLANE_FUTURE_SKEW = timedelta(seconds=5)


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


def _local_health_component_url(base_url: str, component: str) -> str:
    if component not in {"mcp", "control-plane"}:
        raise TunnelHealthEvidenceError("unsupported tunnel health component")
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
    return f"http://127.0.0.1:{port}/health/{component}"


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


def _collect_health_component(
    config_dir: Path,
    *,
    component: str,
    opener,
) -> dict[str, Any] | None:
    base_url = _read_private_health_url(config_dir)
    if base_url is None:
        return None
    url = _local_health_component_url(base_url, component)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with opener(request, timeout=_HEALTH_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_HEALTH_RESPONSE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None

    payload = _decode_component_payload(raw)
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        return None
    if payload.get("component") != component:
        return None
    return payload


def collect_tunnel_runtime_instance_id(
    config_dir: Path,
    *,
    opener=_open_loopback,
) -> str | None:
    """Read only the tunnel-client's bounded process-scoped runtime identity."""

    base_url = _read_private_health_url(config_dir)
    if base_url is None:
        return None
    parsed = urllib.parse.urlsplit(base_url)
    if (
        parsed.scheme != "http"
        or (parsed.hostname or "").lower() != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise TunnelHealthEvidenceError(
            "tunnel health evidence is not fixed loopback HTTP"
        )
    try:
        port = parsed.port
    except ValueError as exc:
        raise TunnelHealthEvidenceError(
            "tunnel health evidence URL is invalid"
        ) from exc
    if port is None or not 1 <= port <= 65_535 or parsed.path not in {"", "/"}:
        raise TunnelHealthEvidenceError(
            "tunnel health evidence URL is invalid"
        )

    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/health?details=true",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with opener(request, timeout=_HEALTH_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_HEALTH_RESPONSE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None

    payload = _decode_component_payload(raw)
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        return None
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        return None
    instance_id = runtime.get("instance_id")
    if not isinstance(instance_id, str) or _INSTANCE_ID_RE.fullmatch(instance_id) is None:
        return None
    return instance_id


def collect_local_mcp_ready(
    config_dir: Path,
    *,
    opener=_open_loopback,
) -> bool:
    """Probe only the tunnel-client's fixed loopback MCP health component."""

    payload = _collect_health_component(
        config_dir,
        component="mcp",
        opener=opener,
    )
    if payload is None:
        return False
    if (
        payload.get("status") == "ok"
        and payload.get("state") in {"initialized", "discovered"}
    ):
        return True

    if payload.get("status") not in {"ok", "unknown"}:
        return False
    details = payload.get("details")
    if not isinstance(details, dict) or details.get("transport") != "http-streamable":
        return False
    startup_probe = details.get("startup_probe")
    if not isinstance(startup_probe, dict):
        return False
    return startup_probe.get("state") in {"succeeded", "auth_required"}


def collect_control_plane_authenticated(
    config_dir: Path,
    *,
    opener=_open_loopback,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> bool:
    """Require a recent authenticated poll, not merely historical success."""

    payload = _collect_health_component(
        config_dir,
        component="control-plane",
        opener=opener,
    )
    if payload is None or payload.get("status") != "ok":
        return False
    if payload.get("state") not in {"idle", "polling", "backpressured"}:
        return False
    details = payload.get("details")
    if not isinstance(details, dict):
        return False
    last_success = details.get("last_success")
    if (
        not isinstance(last_success, str)
        or len(last_success) > 64
        or _RFC3339_RE.fullmatch(last_success) is None
    ):
        return False
    try:
        observed = datetime.fromisoformat(last_success.replace("Z", "+00:00"))
    except ValueError:
        return False
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        return False
    if observed > now + _MAX_CONTROL_PLANE_FUTURE_SKEW:
        return False
    return now - observed <= _MAX_CONTROL_PLANE_AUTH_AGE
