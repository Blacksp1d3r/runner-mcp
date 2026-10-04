from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.ci_runner_github import (
    CIRunnerGitHubController,
    CIRunnerGitHubError,
)
from runner_mcp.ci_runner_lifecycle import CIRunnerSpec
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

    def put_json(self, path, *, payload):
        self.calls.append(("put", path, payload))
        return self.responses.pop(0)


def spec(tmp_path: Path) -> CIRunnerSpec:
    return CIRunnerSpec(
        alias="aifordable-lab-ci",
        repository="Blacksp1d3r/AIfordable",
        runner_name="aifordable-lab-ci",
        runner_root=tmp_path / "runner",
        work_root=tmp_path / "runner" / "_work",
        labels=("aifordable-ci",),
    )


def runner_payload(*, labels=None):
    return {
        "id": 42,
        "name": "aifordable-lab-ci",
        "status": "online",
        "busy": False,
        "labels": labels
        or [
            {"name": "self-hosted", "type": "read-only"},
            {"name": "Linux", "type": "read-only"},
            {"name": "X64", "type": "read-only"},
            {"name": "aifordable-ci", "type": "custom"},
        ],
    }


def test_status_finds_exact_configured_identity(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.append({"total_count": 1, "runners": [runner_payload()]})

    result = CIRunnerGitHubController(session).status(spec(tmp_path))

    assert result is not None
    assert result.runner_id == 42
    assert result.online is True
    assert result.busy is False
    assert result.custom_labels == ("aifordable-ci",)
    assert session.calls == [
        (
            "get",
            "/repos/Blacksp1d3r/AIfordable/actions/runners",
            {"per_page": "100"},
        )
    ]


def test_missing_runner_is_not_error(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.append({"total_count": 0, "runners": []})

    assert CIRunnerGitHubController(session).status(spec(tmp_path)) is None


def test_ambiguous_runner_name_fails_closed(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.append(
        {"total_count": 2, "runners": [runner_payload(), runner_payload()]}
    )

    with pytest.raises(CIRunnerGitHubError, match="ambiguous"):
        CIRunnerGitHubController(session).status(spec(tmp_path))


def test_registration_and_remove_tokens_remain_internal(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.extend(
        [
            {"token": "r" * 40, "expires_at": "private"},
            {"token": "x" * 40, "expires_at": "private"},
        ]
    )
    controller = CIRunnerGitHubController(session)

    registration = controller.create_registration_token(spec(tmp_path))
    removal = controller.create_remove_token(spec(tmp_path))

    assert registration.value == "r" * 40
    assert removal.value == "x" * 40
    assert "r" * 40 not in repr(controller)
    assert session.calls[0][1].endswith("/registration-token")
    assert session.calls[1][1].endswith("/remove-token")


def test_label_control_cannot_exceed_configured_authority(tmp_path: Path) -> None:
    session = FakeSession()
    controller = CIRunnerGitHubController(session)

    with pytest.raises(CIRunnerGitHubError, match="exceed"):
        controller.set_custom_labels(
            spec(tmp_path),
            runner_id=42,
            labels=("production-secret",),
        )

    assert session.calls == []


def test_label_withdrawal_supports_drain_without_process_kill(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.extend(
        [
            {
                "total_count": 2,
                "labels": [
                    {"name": "self-hosted", "type": "read-only"},
                    {"name": "Linux", "type": "read-only"},
                    {"name": "X64", "type": "read-only"},
                ],
            },
            {
                "total_count": 1,
                "runners": [
                    runner_payload(
                        labels=[
                            {"name": "self-hosted", "type": "read-only"},
                            {"name": "Linux", "type": "read-only"},
                            {"name": "X64", "type": "read-only"},
                        ]
                    )
                ],
            },
        ]
    )

    result = CIRunnerGitHubController(session).set_custom_labels(
        spec(tmp_path),
        runner_id=42,
        labels=(),
    )

    assert result.custom_labels == ()
    assert session.calls[0] == (
        "put",
        "/repos/Blacksp1d3r/AIfordable/actions/runners/42/labels",
        {"labels": []},
    )


def test_github_payload_errors_are_bounded(tmp_path: Path) -> None:
    session = FakeSession()
    session.responses.append({"runners": [{"name": "aifordable-lab-ci"}]})

    with pytest.raises(CIRunnerGitHubError, match="invalid"):
        CIRunnerGitHubController(session).status(spec(tmp_path))
