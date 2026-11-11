"""#341: existing A7 custody option reaches the actual self-update manager.

A qualified Fabric owner may select the opt-in only via explicit application
composition. The normal production CLI supplies no such option: default OFF.
No new endpoint, env switch, updater or background supervisor is introduced.
"""

from pathlib import Path

import pytest

from runner_mcp import server
from runner_mcp.config import ProjectConfig, ProjectRegistry
from runner_mcp.self_update import SelfUpdateError


def _safe_settings(tmp_path: Path) -> server.Settings:
    return server.Settings(
        bearer_token="x" * 32,
        auth_issuer="https://auth.example.invalid/",
        resource_url="https://mcp.example.invalid/mcp",
        projects_config=tmp_path / "projects.yml",
        audit_log=tmp_path / "audit.jsonl",
        rate_limit_per_minute=60,
        operator_stop_file=tmp_path / "operator.stop",
        retention_confirmed=True,
    )


def _registry(tmp_path: Path) -> ProjectRegistry:
    root = tmp_path / "repository"
    root.mkdir()
    return ProjectRegistry(
        projects={
            "demo": ProjectConfig(
                display_name="Demo",
                repository="example/demo",
                root=root,
            )
        }
    )


@pytest.mark.parametrize(
    ("use_explicit", "retention", "expected"),
    [
        (False, None, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_application_forwards_a7_opt_in_to_original_self_update_manager(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    use_explicit: bool,
    retention: bool | None,
    expected: bool,
) -> None:
    original_manager = server.SelfUpdateManager
    observed: list[bool] = []

    class ObservedManager(original_manager):
        def __init__(self, *args, **kwargs) -> None:
            observed.append(kwargs["retain_activation_baseline"])
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(server, "SelfUpdateManager", ObservedManager)
    args: dict[str, bool] = (
        {"self_update_retain_activation_baseline": retention}
        if use_explicit
        else {}
    )
    app = server.create_app(
        settings=_safe_settings(tmp_path),
        registry=_registry(tmp_path),
        secret_values={},
        **args,
    )
    assert app is not None
    assert observed == [expected]


@pytest.mark.parametrize("untrusted", [None, 1, "true", [], {}])
def test_application_cannot_downgrade_manager_boolean_contract(
    tmp_path: Path, untrusted: object
) -> None:
    with pytest.raises(SelfUpdateError, match="retention flag is invalid"):
        server.create_app(
            settings=_safe_settings(tmp_path),
            registry=_registry(tmp_path),
            secret_values={},
            self_update_retain_activation_baseline=untrusted,
        )
