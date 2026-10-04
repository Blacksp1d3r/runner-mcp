from __future__ import annotations

import pytest

from runner_mcp.ci_runner_guest_enrollment import CIRunnerGuestSpec
from runner_mcp.ci_runner_guest_github import (
    CIRunnerGuestGitHubController,
    CIRunnerGuestRegistrationToken,
)
from runner_mcp.ci_runner_github import CIRunnerGitHubError
from runner_mcp.github_mailbox import GitHubApiSession


class FakeSession(GitHubApiSession):
    def __init__(self) -> None:
        super().__init__(token="t" * 40)
        self.calls: list[tuple[str, str, object]] = []
        self.responses: list[object] = []

    def get_json(self, path, *, query=None, allow_not_found=False):
        self.calls.append(("get", path, query))
        return self.responses.pop(0)

    def post_json(self, path, *, payload):
        self.calls.append(("post", path, payload))
        return self.responses.pop(0)


def spec() -> CIRunnerGuestSpec:
    return CIRunnerGuestSpec(
        alias="aifordable-lab-ci",
        repository="Blacksp1d3r/AIfordable",
        runner_name="aifordable-lab-ci",
        labels=("aifordable-ci",),
        transport_binding_key="aifordable-lab-ci",
    )


def runner_payload():
    return {
        "id": 42,
        "name": "aifordable-lab-ci",
        "status": "online",
        "busy": False,
        "labels": [
            {"name": "self-hosted", "type": "read-only"},
            {"name": "Linux", "type": "read-only"},
            {"name": "X64", "type": "read-only"},
            {"name": "aifordable-ci", "type": "custom"},
        ],
    }


def test_guest_status_uses_only_repository_and_runner_identity() -> None:
    session = FakeSession()
    session.responses.append(
        {"total_count": 1, "runners": [runner_payload()]}
    )

    result = CIRunnerGuestGitHubController(session).status(spec())

    assert result is not None
    assert result.runner_id == 42
    assert result.online is True
    assert result.custom_labels == ("aifordable-ci",)
    assert session.calls == [
        (
            "get",
            "/repos/Blacksp1d3r/AIfordable/actions/runners",
            {"per_page": "100"},
        )
    ]


def test_guest_registration_token_is_redacted_and_short_lived_authority_only() -> None:
    session = FakeSession()
    session.responses.append(
        {"token": "r" * 40, "expires_at": "private"}
    )
    controller = CIRunnerGuestGitHubController(session)

    token = controller.create_registration_token(spec())

    assert isinstance(token, CIRunnerGuestRegistrationToken)
    assert token.value == "r" * 40
    assert token.value not in repr(token)
    assert token.value not in repr(controller)
    assert session.calls == [
        (
            "post",
            (
                "/repos/Blacksp1d3r/AIfordable/actions/runners/"
                "registration-token"
            ),
            {},
        )
    ]


def test_missing_guest_runner_is_not_error() -> None:
    session = FakeSession()
    session.responses.append({"total_count": 0, "runners": []})

    assert CIRunnerGuestGitHubController(session).status(spec()) is None


def test_ambiguous_guest_runner_fails_closed() -> None:
    session = FakeSession()
    session.responses.append(
        {
            "total_count": 2,
            "runners": [runner_payload(), runner_payload()],
        }
    )

    with pytest.raises(CIRunnerGitHubError, match="ambiguous"):
        CIRunnerGuestGitHubController(session).status(spec())


def test_invalid_guest_runner_payload_is_bounded() -> None:
    session = FakeSession()
    session.responses.append(
        {"runners": [{"name": "aifordable-lab-ci"}]}
    )

    with pytest.raises(CIRunnerGitHubError, match="invalid"):
        CIRunnerGuestGitHubController(session).status(spec())


def test_guest_controller_has_no_local_path_surface() -> None:
    rendered = repr(spec())

    assert "runner_root" not in rendered
    assert "work_root" not in rendered
    assert "/opt/actions-runner" not in rendered
