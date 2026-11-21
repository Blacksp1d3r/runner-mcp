"""M6 laatste primaire systemd-server: zuivere bron- en herstelregressies.

Test het enkelvoudige afsluitende cronblok en de bestaande serverunit na vijf
bewezen peerplannen. Geen server, systemd, SQL, netwerk of cron wordt gestart.
Bronplannen leveren nooit een fysieke cutoververgunning.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from runner_mcp import autostart
from runner_mcp.autostart import (
    SERVER_UNIT,
    AutostartError,
    plan_final_server_systemd_migration,
    render_user_units,
)
from runner_mcp.cron_autostart import CRON_BEGIN, CRON_COMPONENTS, render_cron_block


@pytest.fixture
def final_primary_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    executable = tmp_path / "bin" / "runner-mcp"
    executable.parent.mkdir()
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    config_dir = tmp_path / "private"
    config_dir.mkdir()
    installed_peers = {
        "github-watcher", "completion-watcher", "agent-bus-worker",
        "topology-heartbeat", "fabric-agent-qualification",
    }
    prior = tuple(role for role in CRON_COMPONENTS if role in installed_peers)
    monkeypatch.setattr(
        autostart, "configured_autostart_components",
        lambda _config: ("server", *prior),
    )

    def no_process(*_args: object, **_kwargs: object) -> None:
        pytest.fail("pure last-primary plan must not execute a process")

    monkeypatch.setattr(subprocess, "run", no_process)
    original = "17 * * * * /usr/bin/true # unrelated\n\n" + "\n".join(
        render_cron_block(
            executable=executable, config_dir=config_dir,
            components=("server",), port=8000,
        ),
    ) + "\n"
    return {
        "original_crontab": original,
        "executable": executable,
        "config_dir": config_dir,
        "preexisting_systemd_roles": prior,
    }


def test_final_server_preserves_last_rollback_and_uses_existing_primary_unit(
    final_primary_input: dict[str, object], tmp_path: Path,
) -> None:
    preview = plan_final_server_systemd_migration(**final_primary_input)
    assert preview.original_crontab == final_primary_input["original_crontab"]
    assert preview.rollback_crontab_sha256 == hashlib.sha256(
        preview.original_crontab.encode("utf-8")
    ).hexdigest()
    assert preview.candidate_crontab == "17 * * * * /usr/bin/true # unrelated\n\n"
    assert preview.server_unit_name == SERVER_UNIT
    assert preview.preexisting_systemd_roles == (
        final_primary_input["preexisting_systemd_roles"]
    )
    assert preview.cutover_authorized is False
    assert preview.server_unit_contents.count("ExecStart=") == 1
    assert '"autostart" "cron-run" "server" "--port" "8000"' in (
        preview.server_unit_contents
    )
    assert "Requires=" not in preview.server_unit_contents
    assert "NoNewPrivileges=true\n" in preview.server_unit_contents
    assert "PrivateTmp=true\n" in preview.server_unit_contents
    assert "WantedBy=default.target" in preview.server_unit_contents

    ordinary = render_user_units(
        config_dir=final_primary_input["config_dir"],
        executable=final_primary_input["executable"],
    )[SERVER_UNIT]
    assert preview.server_unit_contents.replace(
        '"autostart" "cron-run" "server" "--port" "8000"',
        '"serve" "--host" "127.0.0.1" "--port" "8000"',
    ) == ordinary
    assert not list(tmp_path.rglob("*.service"))


@pytest.mark.parametrize(
    "corruption",
    (
        "missing-peer", "duplicate-peer", "wrong-order",
        "second-server", "other-cron-role", "duplicate-marker",
        "wrong-port", "hidden-manager", "missing-newline",
        "modified-managed-body", "wrong-executable", "bool-port",
    ),
)
def test_final_primary_refuses_partial_or_ambiguous_original_cron(
    final_primary_input: dict[str, object],
    tmp_path: Path,
    corruption: str,
) -> None:
    values = dict(final_primary_input)
    original = values["original_crontab"]
    prior = values["preexisting_systemd_roles"]
    if corruption == "missing-peer":
        values["preexisting_systemd_roles"] = prior[:-1]
    elif corruption == "duplicate-peer":
        values["preexisting_systemd_roles"] = (*prior, prior[-1])
    elif corruption == "wrong-order":
        values["preexisting_systemd_roles"] = (prior[1], prior[0], *prior[2:])
    elif corruption == "second-server":
        server = next(line for line in original.splitlines() if "cron-run server" in line)
        values["original_crontab"] = original.replace(server + "\n", server + "\n" + server + "\n")
    elif corruption == "other-cron-role":
        values["original_crontab"] = original.replace(
            "# END RUNNER MCP AUTOSTART v1",
            "* * * * * /tmp/x --config-dir /tmp/y autostart cron-run agent-bus-worker "
            ">/dev/null 2>&1\n# END RUNNER MCP AUTOSTART v1",
        )
    elif corruption == "duplicate-marker":
        values["original_crontab"] = CRON_BEGIN + "\n" + original
    elif corruption == "wrong-port":
        values["original_crontab"] = original.replace("--port 8000", "--port 8001")
    elif corruption == "hidden-manager":
        values["original_crontab"] = (
            "27 * * * * /tmp/runner-mcp autostart cron-run server\n" + original
        )
    elif corruption == "missing-newline":
        values["original_crontab"] = original.rstrip("\n")
    elif corruption == "modified-managed-body":
        values["original_crontab"] = original.replace('MAILTO=""', 'MAILTO="root"')
    elif corruption == "wrong-executable":
        values["executable"] = tmp_path / "not-installed" / "runner-mcp"
    else:
        values["port"] = True
    with pytest.raises(AutostartError, match="final server primary migration"):
        plan_final_server_systemd_migration(**values)
    assert not list(tmp_path.rglob("*.service"))


def test_final_primary_rejects_changed_unit_security_contract(
    final_primary_input: dict[str, object],
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    units = render_user_units(
        config_dir=final_primary_input["config_dir"],
        executable=final_primary_input["executable"],
    )
    bad = {
        **units,
        SERVER_UNIT: units[SERVER_UNIT].replace(
            "NoNewPrivileges=true\n", "NoNewPrivileges=false\n",
        ),
    }
    monkeypatch.setattr(autostart, "render_user_units", lambda **_kwargs: bad)
    with pytest.raises(AutostartError, match="final server primary migration"):
        plan_final_server_systemd_migration(**final_primary_input)
    assert not list(tmp_path.rglob("*.service"))
