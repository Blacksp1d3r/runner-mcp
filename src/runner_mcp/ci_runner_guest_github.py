from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ci_runner_github import CIRunnerGitHubError, GitHubRunnerState
from .ci_runner_guest_enrollment import CIRunnerGuestSpec
from .github_mailbox import GitHubApiSession, GitHubMailboxTransportError

_MAX_RUNNERS_PAGE = "100"


@dataclass(frozen=True, slots=True, repr=False)
class CIRunnerGuestRegistrationToken:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not 16 <= len(self.value) <= 4096
            or not self.value.isascii()
            or any(ord(char) < 33 or ord(char) == 127 for char in self.value)
        ):
            raise CIRunnerGitHubError(
                "GitHub guest runner token response is invalid"
            )

    def __repr__(self) -> str:
        return "<CIRunnerGuestRegistrationToken redacted>"


class CIRunnerGuestGitHubController:
    """GitHub authority for guest runners without local filesystem authority."""

    def __init__(self, session: GitHubApiSession) -> None:
        if not isinstance(session, GitHubApiSession):
            raise TypeError("session must be GitHubApiSession")
        self._session = session

    def status(
        self,
        spec: CIRunnerGuestSpec,
    ) -> GitHubRunnerState | None:
        self._require_spec(spec)
        payload = self._request(
            "get",
            f"/repos/{spec.repository}/actions/runners",
            query={"per_page": _MAX_RUNNERS_PAGE},
        )
        if not isinstance(payload, dict):
            raise CIRunnerGitHubError(
                "GitHub guest runner inventory is invalid"
            )
        runners = payload.get("runners")
        if not isinstance(runners, list):
            raise CIRunnerGitHubError(
                "GitHub guest runner inventory is invalid"
            )

        matches = [
            item
            for item in runners
            if isinstance(item, dict)
            and item.get("name") == spec.runner_name
        ]
        if not matches:
            return None
        if len(matches) != 1:
            raise CIRunnerGitHubError(
                "GitHub guest runner identity is ambiguous"
            )
        return self._parse_state(matches[0])

    def create_registration_token(
        self,
        spec: CIRunnerGuestSpec,
    ) -> CIRunnerGuestRegistrationToken:
        self._require_spec(spec)
        payload = self._request(
            "post",
            (
                f"/repos/{spec.repository}/actions/runners/"
                "registration-token"
            ),
            payload={},
        )
        if not isinstance(payload, dict):
            raise CIRunnerGitHubError(
                "GitHub guest runner token response is invalid"
            )
        token = payload.get("token")
        if not isinstance(token, str):
            raise CIRunnerGitHubError(
                "GitHub guest runner token response is invalid"
            )
        return CIRunnerGuestRegistrationToken(token)

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
                return self._session.post_json(
                    path,
                    payload=payload or {},
                )
        except GitHubMailboxTransportError as exc:
            raise CIRunnerGitHubError(
                "GitHub guest runner control is unavailable"
            ) from exc
        raise ValueError("unsupported guest CI runner GitHub method")

    @staticmethod
    def _require_spec(spec: CIRunnerGuestSpec) -> None:
        if not isinstance(spec, CIRunnerGuestSpec):
            raise TypeError("spec must be CIRunnerGuestSpec")

    @staticmethod
    def _parse_state(item: dict[str, Any]) -> GitHubRunnerState:
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
            raise CIRunnerGitHubError(
                "GitHub guest runner inventory item is invalid"
            )

        custom: list[str] = []
        for label in labels:
            if not isinstance(label, dict):
                raise CIRunnerGitHubError(
                    "GitHub guest runner label item is invalid"
                )
            name = label.get("name")
            label_type = label.get("type")
            if (
                not isinstance(name, str)
                or label_type not in {"read-only", "custom"}
            ):
                raise CIRunnerGitHubError(
                    "GitHub guest runner label item is invalid"
                )
            if label_type == "custom":
                custom.append(name)

        return GitHubRunnerState(
            runner_id=runner_id,
            online=status == "online",
            busy=busy,
            custom_labels=tuple(sorted(custom)),
        )
