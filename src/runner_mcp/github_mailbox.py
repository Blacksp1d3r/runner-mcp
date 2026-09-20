from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .bridge_processor import BridgeResultSinkError
from .bridge_protocol import (
    MAX_BRIDGE_REQUEST_BYTES,
    MAX_BRIDGE_RESULT_BYTES,
    REQUEST_ID_RE,
    BridgeProtocolError,
    parse_bridge_request,
    parse_bridge_result,
)
from .bridge_resilience import (
    MAX_HEARTBEAT_BYTES,
    BridgeResilienceError,
    TransportFailureKind,
    parse_watcher_heartbeat,
    transport_retry_delays,
)

GITHUB_API_BASE = "https://api.github.com"
MAX_GITHUB_RESPONSE_BYTES = 1_048_576
MAX_MAILBOX_ENTRIES = 1_000
MAILBOX_ROOT = ".runner-control"
REQUESTS_PATH = f"{MAILBOX_ROOT}/requests"
RESULTS_PATH = f"{MAILBOX_ROOT}/results"
HEARTBEAT_PATH = f"{MAILBOX_ROOT}/heartbeat.json"

_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}/"
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}$"
)
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GitHubMailboxTransportError(BridgeResilienceError):
    """Safe GitHub mailbox transport failure without private response details."""

    def __init__(
        self,
        message: str,
        *,
        kind: TransportFailureKind,
    ) -> None:
        super().__init__(message)
        self.kind = kind


class GitHubMailboxResultSinkError(BridgeResultSinkError):
    """Safe durable-result failure compatible with BridgeProcessor."""

    def __init__(
        self,
        message: str,
        *,
        kind: TransportFailureKind,
    ) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True, slots=True)
class GitHubMailboxConfig:
    repository: str
    request_ref: str
    result_ref: str

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("repository must use a safe owner/name shape")
        _validate_ref(self.request_ref)
        _validate_ref(self.result_ref)


@dataclass(frozen=True, slots=True)
class MailboxFile:
    path: str
    sha: str
    content: bytes


def _validate_ref(ref: str) -> None:
    if not _REF_RE.fullmatch(ref):
        raise ValueError("mailbox ref contains unsupported characters")
    if (
        ref.startswith(("/", "."))
        or ref.endswith(("/", ".", ".lock"))
        or "//" in ref
        or ".." in ref
        or "@{" in ref
    ):
        raise ValueError("mailbox ref has an unsafe shape")


def _validate_token(token: str) -> None:
    if not token or len(token) > 4_096:
        raise ValueError("GitHub token is missing or unreasonably large")
    if not token.isascii():
        raise ValueError("GitHub token must use ASCII characters")
    if any(ord(char) < 33 or ord(char) == 127 for char in token):
        raise ValueError("GitHub token contains unsupported characters")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _load_strict_json(raw: bytes) -> Any:
    return json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonstandard_json_constant,
    )


class GitHubApiSession:
    """Minimal fixed-host GitHub Contents API client."""

    def __init__(
        self,
        *,
        token: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        _validate_token(token)
        if not 1 <= timeout_seconds <= 120:
            raise ValueError("GitHub timeout is outside the supported range")
        self._token = token
        self._timeout_seconds = timeout_seconds

    def get_json(
        self,
        api_path: str,
        *,
        query: dict[str, str] | None = None,
        allow_not_found: bool = False,
    ) -> Any | None:
        return self._request_json(
            "GET",
            api_path,
            query=query,
            allow_not_found=allow_not_found,
        )

    def put_json(
        self,
        api_path: str,
        *,
        payload: dict[str, Any],
    ) -> Any:
        return self._request_json(
            "PUT",
            api_path,
            payload=payload,
            allow_not_found=False,
        )

    def _request_json(
        self,
        method: str,
        api_path: str,
        *,
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        allow_not_found: bool,
    ) -> Any | None:
        if method not in {"GET", "PUT"}:
            raise ValueError("unsupported GitHub API method")
        if (
            not api_path.startswith("/repos/")
            or "://" in api_path
            or any(char in api_path for char in "\r\n?#\\")
        ):
            raise ValueError("GitHub API path must stay repository-scoped")

        url = f"{GITHUB_API_BASE}{api_path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        data = None
        if payload is not None:
            data = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "runner-mcp",
            },
            method=method,
        )

        raw: bytes | None = None
        delay_before_attempt = 0
        while True:
            if delay_before_attempt:
                time.sleep(delay_before_attempt)
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self._timeout_seconds,
                ) as response:
                    raw = response.read(MAX_GITHUB_RESPONSE_BYTES + 1)
                break
            except urllib.error.HTTPError as exc:
                if allow_not_found and exc.code == 404:
                    return None
                error = _http_error(exc)
            except TimeoutError:
                error = GitHubMailboxTransportError(
                    "GitHub mailbox transport timed out",
                    kind=TransportFailureKind.TIMEOUT,
                )
            except urllib.error.URLError:
                error = GitHubMailboxTransportError(
                    "GitHub mailbox transport is unavailable",
                    kind=TransportFailureKind.UNAVAILABLE,
                )

            delays = transport_retry_delays(error.kind)
            if not delays:
                raise error from None
            if delay_before_attempt == 0:
                delay_before_attempt = delays[0]
                continue
            if len(delays) > 1 and delay_before_attempt == delays[0]:
                delay_before_attempt = delays[1]
                continue
            raise error from None

        assert raw is not None
        if len(raw) > MAX_GITHUB_RESPONSE_BYTES:
            raise GitHubMailboxTransportError(
                "GitHub mailbox response exceeds size limit",
                kind=TransportFailureKind.INVALID_RESPONSE,
            )

        try:
            return _load_strict_json(raw)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            raise GitHubMailboxTransportError(
                "GitHub mailbox returned invalid JSON",
                kind=TransportFailureKind.INVALID_RESPONSE,
            ) from exc


def _http_error(exc: urllib.error.HTTPError) -> GitHubMailboxTransportError:
    status = exc.code
    if status == 401:
        return GitHubMailboxTransportError(
            "GitHub mailbox authorization failed",
            kind=TransportFailureKind.AUTHORIZATION,
        )
    if status == 403:
        retry_after = exc.headers.get("Retry-After")
        rate_remaining = exc.headers.get("X-RateLimit-Remaining")
        if retry_after is not None or rate_remaining == "0":
            return GitHubMailboxTransportError(
                "GitHub mailbox is rate limited",
                kind=TransportFailureKind.RATE_LIMITED,
            )
        return GitHubMailboxTransportError(
            "GitHub mailbox authorization failed",
            kind=TransportFailureKind.AUTHORIZATION,
        )
    if status == 408:
        return GitHubMailboxTransportError(
            "GitHub mailbox transport timed out",
            kind=TransportFailureKind.TIMEOUT,
        )
    if status == 429:
        return GitHubMailboxTransportError(
            "GitHub mailbox is rate limited",
            kind=TransportFailureKind.RATE_LIMITED,
        )
    if status == 409 or 500 <= status <= 599:
        return GitHubMailboxTransportError(
            "GitHub mailbox transport is unavailable",
            kind=TransportFailureKind.UNAVAILABLE,
        )
    return GitHubMailboxTransportError(
        "GitHub mailbox request failed",
        kind=TransportFailureKind.INVALID_RESPONSE,
    )


class GitHubMailboxTransport:
    """Fixed-path GitHub mailbox transport for the shared bridge processor."""

    def __init__(
        self,
        *,
        config: GitHubMailboxConfig,
        session: GitHubApiSession,
    ) -> None:
        self._config = config
        self._session = session

    def list_request_ids(self) -> list[str]:
        raw = self._session.get_json(
            self._contents_path(REQUESTS_PATH),
            query={"ref": self._config.request_ref},
            allow_not_found=True,
        )
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise self._invalid_response("request mailbox is not a directory")
        if len(raw) > MAX_MAILBOX_ENTRIES:
            raise self._invalid_response("request mailbox contains too many entries")

        request_ids: list[str] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise self._invalid_response("request mailbox entry is invalid")
            if entry.get("type") != "file":
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name.endswith(".json"):
                continue
            request_id = name[:-5]
            if not REQUEST_ID_RE.fullmatch(request_id):
                continue
            request_ids.append(request_id)

        if len(request_ids) != len(set(request_ids)):
            raise self._invalid_response("request mailbox contains duplicate request IDs")
        return sorted(request_ids)

    def fetch_request(self, request_id: str) -> bytes:
        _validate_request_id(request_id)
        mailbox_file = self._fetch_file(
            f"{REQUESTS_PATH}/{request_id}.json",
            ref=self._config.request_ref,
            max_bytes=MAX_BRIDGE_REQUEST_BYTES,
            allow_not_found=False,
        )
        assert mailbox_file is not None
        request = parse_bridge_request(mailbox_file.content)
        if request.request_id != request_id:
            raise GitHubMailboxTransportError(
                "request filename and payload ID do not match",
                kind=TransportFailureKind.INVALID_RESPONSE,
            )
        return mailbox_file.content

    def result_exists(self, request_id: str) -> bool:
        _validate_request_id(request_id)
        return (
            self._fetch_file(
                f"{RESULTS_PATH}/{request_id}.json",
                ref=self._config.result_ref,
                max_bytes=MAX_BRIDGE_RESULT_BYTES,
                allow_not_found=True,
            )
            is not None
        )

    def persist_result(self, request_id: str, result_json: str) -> None:
        _validate_request_id(request_id)
        encoded = result_json.encode("utf-8")
        if len(encoded) > MAX_BRIDGE_RESULT_BYTES:
            raise BridgeProtocolError("bridge result exceeds size limit")
        result = parse_bridge_result(result_json)
        if result.request_id != request_id:
            raise BridgeProtocolError("result request_id does not match mailbox path")

        path = f"{RESULTS_PATH}/{request_id}.json"
        try:
            existing = self._fetch_file(
                path,
                ref=self._config.result_ref,
                max_bytes=MAX_BRIDGE_RESULT_BYTES,
                allow_not_found=True,
            )
            if existing is not None:
                if existing.content == encoded:
                    return
                raise GitHubMailboxTransportError(
                    "result already exists with different content",
                    kind=TransportFailureKind.INVALID_RESPONSE,
                )

            self._session.put_json(
                self._contents_path(path),
                payload={
                    "message": "runner: publish bridge result",
                    "content": base64.b64encode(encoded).decode("ascii"),
                    "branch": self._config.result_ref,
                },
            )
        except GitHubMailboxTransportError as exc:
            raise GitHubMailboxResultSinkError(
                "GitHub mailbox result persistence failed",
                kind=exc.kind,
            ) from exc

    def publish_heartbeat(self, heartbeat_json: str) -> None:
        encoded = heartbeat_json.encode("utf-8")
        if len(encoded) > MAX_HEARTBEAT_BYTES:
            raise BridgeResilienceError("watcher heartbeat exceeds size limit")
        parse_watcher_heartbeat(heartbeat_json)

        existing = self._fetch_file(
            HEARTBEAT_PATH,
            ref=self._config.result_ref,
            max_bytes=MAX_HEARTBEAT_BYTES,
            allow_not_found=True,
        )
        payload: dict[str, Any] = {
            "message": "runner: publish watcher heartbeat",
            "content": base64.b64encode(encoded).decode("ascii"),
            "branch": self._config.result_ref,
        }
        if existing is not None:
            payload["sha"] = existing.sha

        self._session.put_json(
            self._contents_path(HEARTBEAT_PATH),
            payload=payload,
        )

    def _fetch_file(
        self,
        path: str,
        *,
        ref: str,
        max_bytes: int,
        allow_not_found: bool,
    ) -> MailboxFile | None:
        raw = self._session.get_json(
            self._contents_path(path),
            query={"ref": ref},
            allow_not_found=allow_not_found,
        )
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise self._invalid_response("mailbox file response is invalid")

        sha = raw.get("sha")
        content = raw.get("content")
        encoding = raw.get("encoding")
        if (
            not isinstance(sha, str)
            or not _SHA_RE.fullmatch(sha)
            or not isinstance(content, str)
            or encoding != "base64"
        ):
            raise self._invalid_response("mailbox file metadata is invalid")

        compact_content = "".join(content.split())
        try:
            decoded = base64.b64decode(compact_content, validate=True)
        except (ValueError, TypeError) as exc:
            raise self._invalid_response("mailbox file base64 is invalid") from exc

        if len(decoded) > max_bytes:
            raise self._invalid_response("mailbox file exceeds size limit")

        return MailboxFile(path=path, sha=sha, content=decoded)

    def _contents_path(self, path: str) -> str:
        owner, repo = self._config.repository.split("/", 1)
        safe_path = "/".join(
            urllib.parse.quote(segment, safe="")
            for segment in path.split("/")
        )
        return f"/repos/{owner}/{repo}/contents/{safe_path}"

    def _invalid_response(self, message: str) -> GitHubMailboxTransportError:
        return GitHubMailboxTransportError(
            message,
            kind=TransportFailureKind.INVALID_RESPONSE,
        )


def _validate_request_id(request_id: str) -> None:
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("request_id contains unsupported characters")
