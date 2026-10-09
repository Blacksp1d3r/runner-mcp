from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ci_runner_lifecycle import CIRunnerLifecycleError, CIRunnerSpec
from .github_mailbox import GitHubApiSession, GitHubMailboxTransportError

_MAX_RUNNERS_PAGE = "100"


class CIRunnerGitHubError(RuntimeError):
    """Bounded GitHub runner-control failure without token/response disclosure."""


@dataclass(frozen=True, slots=True)
class GitHubRunnerState:
    runner_id: int
    online: bool
    busy: bool
    custom_labels: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "online": self.online,
            "busy": self.busy,
            "custom_labels": list(self.custom_labels),
        }


@dataclass(frozen=True, slots=True)
class _ShortLivedRunnerToken:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not 16 <= len(self.value) <= 4096
            or not self.value.isascii()
            or any(ord(char) < 33 or ord(char) == 127 for char in self.value)
        ):
            raise CIRunnerGitHubError("GitHub runner token response is invalid")


class CIRunnerGitHubController:
    def __init__(self, session: GitHubApiSession) -> None:
        if not isinstance(session, GitHubApiSession):
            raise TypeError("session must be GitHubApiSession")
        self._session = session

    def status(self, spec: CIRunnerSpec) -> GitHubRunnerState | None:
        _require_spec(spec)
        payload = self._request(
            "get",
            f"/repos/{spec.repository}/actions/runners",
            query={"per_page": _MAX_RUNNERS_PAGE},
        )
        if not isinstance(payload, dict):
            raise CIRunnerGitHubError("GitHub runner inventory is invalid")
        runners = payload.get("runners")
        total_count = payload.get("total_count")
        if (
            not isinstance(runners, list)
            or isinstance(total_count, bool)
            or not isinstance(total_count, int)
            or total_count < 0
            or len(runners) > int(_MAX_RUNNERS_PAGE)
        ):
            raise CIRunnerGitHubError("GitHub runner inventory is invalid")
        # Only the first page is requested. Without complete inventory,
        # treating an unfound name as absent could authorize a duplicate
        # registration; likewise a first-page match could be ambiguous.
        if total_count != len(runners):
            raise CIRunnerGitHubError("GitHub runner inventory is incomplete")
        # Even a nonmatching malformed row can conceal the configured runner.
        # A complete count is not proof that each enumerated identity is valid.
        if any(
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not item["name"]
            for item in runners
        ):
            raise CIRunnerGitHubError("GitHub runner inventory item is invalid")

        matches = [
            item
            for item in runners
            if isinstance(item, dict) and item.get("name") == spec.runner_name
        ]
        if not matches:
            return None
        if len(matches) != 1:
            raise CIRunnerGitHubError("GitHub runner identity is ambiguous")
        return _parse_runner_state(matches[0])

    def create_registration_token(self, spec: CIRunnerSpec) -> _ShortLivedRunnerToken:
        _require_spec(spec)
        payload = self._request(
            "post",
            f"/repos/{spec.repository}/actions/runners/registration-token",
            payload={},
        )
        return _parse_token(payload)

    def create_remove_token(self, spec: CIRunnerSpec) -> _ShortLivedRunnerToken:
        _require_spec(spec)
        payload = self._request(
            "post",
            f"/repos/{spec.repository}/actions/runners/remove-token",
            payload={},
        )
        return _parse_token(payload)

    def set_custom_labels(
        self,
        spec: CIRunnerSpec,
        *,
        runner_id: int,
        labels: tuple[str, ...],
    ) -> GitHubRunnerState:
        _require_spec(spec)
        if isinstance(runner_id, bool) or not isinstance(runner_id, int) or runner_id <= 0:
            raise CIRunnerGitHubError("GitHub runner id is invalid")
        if not isinstance(labels, tuple):
            raise CIRunnerGitHubError("GitHub runner labels are invalid")
        allowed = set(spec.labels)
        if any(label not in allowed for label in labels):
            raise CIRunnerGitHubError("GitHub runner labels exceed configured authority")

        payload = self._request(
            "put",
            f"/repos/{spec.repository}/actions/runners/{runner_id}/labels",
            payload={"labels": list(labels)},
        )
        if not isinstance(payload, dict):
            raise CIRunnerGitHubError("GitHub runner label response is invalid")
        returned = payload.get("labels")
        if not isinstance(returned, list):
            raise CIRunnerGitHubError("GitHub runner label response is invalid")

        custom = tuple(
            sorted(
                item["name"]
                for item in returned
                if isinstance(item, dict)
                and item.get("type") == "custom"
                and isinstance(item.get("name"), str)
            )
        )
        if set(custom) != set(labels):
            raise CIRunnerGitHubError("GitHub runner labels did not converge")

        current = self.status(spec)
        if current is None or current.runner_id != runner_id:
            raise CIRunnerGitHubError("GitHub runner disappeared during label update")
        return current

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        try:
            if method == "get":
                return self._session.get_json(path, query=query)
            if method == "post":
                return self._session.post_json(path, payload=payload or {})
            if method == "put":
                return self._session.put_json(path, payload=payload or {})
        except GitHubMailboxTransportError as exc:
            raise CIRunnerGitHubError("GitHub runner control is unavailable") from exc
        raise ValueError("unsupported CI runner GitHub method")


def _parse_token(payload: object) -> _ShortLivedRunnerToken:
    if not isinstance(payload, dict):
        raise CIRunnerGitHubError("GitHub runner token response is invalid")
    token = payload.get("token")
    if not isinstance(token, str):
        raise CIRunnerGitHubError("GitHub runner token response is invalid")
    return _ShortLivedRunnerToken(token)


def _parse_runner_state(item: dict[str, Any]) -> GitHubRunnerState:
    runner_id = item.get("id")
    status = item.get("status")
    busy = item.get("busy")
    labels = item.get("labels")
    if (
        isinstance(runner_id, bool)
        or not isinstance(runner_id, int)
        or runner_id <= 0
        or status not in {"online", "offline"}
        or not isinstance(busy, bool)
        or not isinstance(labels, list)
    ):
        raise CIRunnerGitHubError("GitHub runner inventory item is invalid")

    custom: list[str] = []
    for label in labels:
        if not isinstance(label, dict):
            raise CIRunnerGitHubError("GitHub runner label item is invalid")
        name = label.get("name")
        label_type = label.get("type")
        if not isinstance(name, str) or label_type not in {"read-only", "custom"}:
            raise CIRunnerGitHubError("GitHub runner label item is invalid")
        if label_type == "custom":
            custom.append(name)

    return GitHubRunnerState(
        runner_id=runner_id,
        online=status == "online",
        busy=busy,
        custom_labels=tuple(sorted(custom)),
    )


def _require_spec(spec: CIRunnerSpec) -> None:
    if not isinstance(spec, CIRunnerSpec):
        raise TypeError("spec must be CIRunnerSpec")
    try:
        CIRunnerSpec(
            alias=spec.alias,
            repository=spec.repository,
            runner_name=spec.runner_name,
            runner_root=spec.runner_root,
            work_root=spec.work_root,
            labels=spec.labels,
        )
    except CIRunnerLifecycleError as exc:
        raise CIRunnerGitHubError("CI runner spec is invalid") from exc
