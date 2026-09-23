from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runner_mcp import autostart as autostart_module
from runner_mcp import secure_io as secure_io_module
from runner_mcp.autostart import (
    COMPLETION_WATCHER_UNIT,
    GITHUB_WATCHER_UNIT,
    MANAGED_MARKER,
    SERVER_UNIT,
    AutostartError,
    _write_managed_unit,
    install_user_services,
    remove_user_services,
    render_user_units,
    user_service_status,
)
from runner_mcp.completion_delivery import (
    bootstrap_completion_notifier,
    configure_github_issue_notifier,
)
from runner_mcp.config_manager import configure_github_mailbox
from runner_mcp.github_watcher import GitHubWatcherCursorStore
from runner_mcp.onboarding import SetupAnswers, install_private_configuration


class FakeSystemctl:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.enabled: set[str] = set()
        self.active: set[str] = set()

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        assert kwargs["stdin"] is subprocess.DEVNULL
        assert kwargs["stdout"] is subprocess.PIPE
        assert kwargs["stderr"] is subprocess.PIPE
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 30
        assert kwargs["check"] is False
        command = argv[2:]
        returncode = 0
        if command[:1] == ["enable"] and "--now" in command:
            names = [item for item in command[2:] if item.endswith(".service")]
            self.enabled.update(names)
            self.active.update(names)
        elif command[:1] == ["disable"] and "--now" in command:
            names = [item for item in command[2:] if item.endswith(".service")]
            self.enabled.difference_update(names)
            self.active.difference_update(names)
        elif command[:1] == ["is-enabled"]:
            returncode = 0 if command[1] in self.enabled else 1
        elif command[:1] == ["is-active"]:
            returncode = 0 if command[1] in self.active else 3
        return subprocess.CompletedProcess(argv, returncode, "", "")


def _private_config(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "private"
    paths = install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url="http://127.0.0.1:8000/mcp",
            auth_issuer="http://127.0.0.1:8000/",
            project_code="demo",
            project_name="Demo",
            repository="example/demo",
            project_root=project,
        ),
    )
    executable = tmp_path / "runner-mcp"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    return paths, executable


def test_render_server_unit_contains_no_credentials(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)

    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert set(units) == {SERVER_UNIT}
    assert units[SERVER_UNIT].startswith(MANAGED_MARKER)
    assert "127.0.0.1" in units[SERVER_UNIT]
    assert "serve" in units[SERVER_UNIT]
    assert "Authorization" not in units[SERVER_UNIT]
    assert "token" not in units[SERVER_UNIT].lower()


def test_mailbox_autostart_requires_explicit_bootstrap(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="a" * 40,
    )

    with pytest.raises(AutostartError, match="not bootstrapped"):
        render_user_units(
            config_dir=paths.config_dir,
            executable=executable,
        )


def test_optional_watchers_are_added_only_after_bootstrap(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    configure_github_mailbox(
        paths.config_dir,
        repository="example/private-mailbox",
        request_ref="runner-control",
        result_ref="runner-results",
        token="a" * 40,
    )
    GitHubWatcherCursorStore(
        paths.config_dir / "github-mailbox-cursor.json"
    ).initialize("b" * 40)
    configure_github_issue_notifier(
        paths.config_dir,
        repository="example/private-mailbox",
        issue_number=25,
        mention="operator-user",
        token="c" * 40,
    )

    with pytest.raises(AutostartError, match="completion notifier.*not bootstrapped"):
        render_user_units(
            config_dir=paths.config_dir,
            executable=executable,
        )

    bootstrap_completion_notifier(paths.config_dir)
    units = render_user_units(
        config_dir=paths.config_dir,
        executable=executable,
    )

    assert set(units) == {
        SERVER_UNIT,
        GITHUB_WATCHER_UNIT,
        COMPLETION_WATCHER_UNIT,
    }
    combined = "\n".join(units.values())
    assert "a" * 40 not in combined
    assert "c" * 40 not in combined
    assert "github-watcher" in units[GITHUB_WATCHER_UNIT]
    assert "completion-watcher" in units[COMPLETION_WATCHER_UNIT]


def test_install_uses_fixed_systemctl_arrays_and_managed_files(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "units"
    systemctl = FakeSystemctl()

    installed = install_user_services(
        paths.config_dir,
        executable=executable,
        unit_dir=unit_dir,
        runner=systemctl,
    )

    assert installed == [SERVER_UNIT]
    path = unit_dir / SERVER_UNIT
    assert path.is_file()
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert path.read_text().startswith(MANAGED_MARKER)
    assert systemctl.calls == [
        ["systemctl", "--user", "show-environment"],
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", SERVER_UNIT],
    ]


def test_install_refuses_to_replace_foreign_unit(tmp_path: Path) -> None:
    paths, executable = _private_config(tmp_path)
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    unit_path = unit_dir / SERVER_UNIT
    foreign_content = "[Service]\nExecStart=/bin/false\n"
    unit_path.write_text(foreign_content)
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="not managed"):
        install_user_services(
            paths.config_dir,
            executable=executable,
            unit_dir=unit_dir,
            runner=systemctl,
        )

    assert unit_path.read_text(encoding="utf-8") == foreign_content


def test_write_managed_unit_uses_private_atomic_replace(tmp_path: Path) -> None:
    target = tmp_path / SERVER_UNIT
    target.write_text(MANAGED_MARKER + "\nold\n", encoding="utf-8")
    target.chmod(0o644)

    _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert target.read_text(encoding="utf-8") == MANAGED_MARKER + "\nnew\n"
    assert target.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.glob(f".{SERVER_UNIT}.*.tmp")) == []


@pytest.mark.parametrize("failure_point", ["fsync", "replace"])
def test_write_managed_unit_bounded_failure_preserves_previous_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    target = tmp_path / SERVER_UNIT
    previous = MANAGED_MARKER + "\nold\n"
    target.write_text(previous, encoding="utf-8")
    target.chmod(0o600)
    sensitive = str(tmp_path / "private-sensitive-value")

    def fail(*_args: object) -> None:
        raise OSError(sensitive)

    monkeypatch.setattr(secure_io_module.os, failure_point, fail)

    with pytest.raises(AutostartError) as captured:
        _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert str(captured.value) == "autostart unit could not be written"
    assert sensitive not in str(captured.value)
    assert target.read_text(encoding="utf-8") == previous
    assert list(tmp_path.glob(f".{SERVER_UNIT}.*.tmp")) == []


def test_write_managed_unit_symlink_swap_cannot_touch_referent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / SERVER_UNIT
    target.write_text(MANAGED_MARKER + "\nold\n", encoding="utf-8")
    referent = tmp_path / "foreign.service"
    referent.write_text("foreign\n", encoding="utf-8")
    referent.chmod(0o640)
    referent_mode = referent.stat().st_mode & 0o777
    real_replace = secure_io_module.atomic_replace_private

    def swap_to_symlink_then_replace(path: Path, content: bytes) -> None:
        path.unlink()
        path.symlink_to(referent)
        real_replace(path, content)

    monkeypatch.setattr(
        autostart_module,
        "atomic_replace_private",
        swap_to_symlink_then_replace,
    )

    with pytest.raises(AutostartError, match="could not be written"):
        _write_managed_unit(target, MANAGED_MARKER + "\nnew\n")

    assert target.is_symlink()
    assert referent.read_text(encoding="utf-8") == "foreign\n"
    assert referent.stat().st_mode & 0o777 == referent_mode


def test_status_is_safe_and_normalized(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text(MANAGED_MARKER + "\n")
    (unit_dir / SERVER_UNIT).chmod(0o600)
    systemctl = FakeSystemctl()
    systemctl.enabled.add(SERVER_UNIT)
    systemctl.active.add(SERVER_UNIT)

    rows = user_service_status(unit_dir=unit_dir, runner=systemctl)

    assert [row.public_dict() for row in rows] == [
        {
            "component": "server",
            "installed": True,
            "enabled": True,
            "active": True,
        },
        {
            "component": "github-watcher",
            "installed": False,
            "enabled": False,
            "active": False,
        },
        {
            "component": "completion-watcher",
            "installed": False,
            "enabled": False,
            "active": False,
        },
    ]


def test_remove_only_deletes_runner_mcp_managed_units(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    managed = unit_dir / SERVER_UNIT
    managed.write_text(MANAGED_MARKER + "\n")
    managed.chmod(0o600)
    systemctl = FakeSystemctl()

    removed = remove_user_services(unit_dir=unit_dir, runner=systemctl)

    assert removed == [SERVER_UNIT]
    assert not managed.exists()
    assert ["systemctl", "--user", "disable", "--now", SERVER_UNIT] in systemctl.calls
    assert systemctl.calls[-1] == ["systemctl", "--user", "daemon-reload"]


def test_remove_refuses_foreign_unit(tmp_path: Path) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / SERVER_UNIT).write_text("[Unit]\nDescription=foreign\n")
    systemctl = FakeSystemctl()

    with pytest.raises(AutostartError, match="not managed"):
        remove_user_services(unit_dir=unit_dir, runner=systemctl)
