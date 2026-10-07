from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner_mcp import cli
from runner_mcp.bewind_disposable_bootstrap import (
    BewindDisposableBootstrapError,
    BewindDisposableBootstrapRestorer,
)
from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy


def _safety(tmp_path: Path) -> OperatorSafetyGuard:
    return OperatorSafetyGuard(
        stop_file=tmp_path / "operator.stop",
        retention=RetentionPolicy(),
        retention_confirmed=True,
    )


def _runtime(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, mode=0o700)
    config_dir.chmod(0o700)
    env_file = config_dir / "runner-mcp.env"
    env_file.write_text("RUNNER_MCP_BEARER_TOKEN=" + "s" * 48 + "\n", encoding="utf-8")
    env_file.chmod(0o600)
    return config_dir, {"RUNNER_MCP_BEARER_TOKEN": "s" * 48}



def _trusted_inventory(fingerprint: str = "b" * 64) -> list[dict[str, object]]:
    return [
        {
            "fingerprint": fingerprint,
            "type": "virtual-machine",
            "properties": {"os": "Ubuntu", "release": "noble"},
            "update_source": {
                "server": "https://images.linuxcontainers.org",
                "protocol": "simplestreams",
                "alias": "ubuntu/24.04",
            },
        }
    ]


def test_restore_is_host_bound(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "github-runner",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(BewindDisposableBootstrapError, match="host_mismatch"):
        restorer.restore()

    assert "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG" not in values


def test_restore_writes_fixed_private_bootstrap(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
        image_inventory_provider=_trusted_inventory,
    )

    result = restorer.restore()

    assert result["state"] == "restored"
    assert result["workerId"] == "aifordable-lab"
    assert result["capabilityProfile"] == "bewind-ocr-qualification-v1"
    assert result["generation"] == 1
    assert result["normalActivationEnabled"] is False

    raw = values["RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"]
    config_path = Path(raw)
    assert config_path == config_dir / "worker-qualification" / "disposable-target.json"
    assert config_path.stat().st_mode & 0o777 == 0o600

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload == {
        "mode": "af14-disposable-v1",
        "qualification_id": "bewind-ocr-lab-v1",
        "target_allocation_id": result["targetAllocationId"],
        "host_binding_key": "aifordable-lab",
        "project_binding_key": "bewind-qualification",
        "project_name": "rf-bewind-qualification",
        "instance_binding_key": "bewind-ocr-guest",
        "instance_name": "rf-bewind-ocr",
        "network_binding_key": "bewind-ocr-net",
        "network_name": "rf-bewind-ocr-net",
        "storage_binding_key": "default",
        "storage_pool_name": "default",
        "binding_created_at": "2026-10-07T15:00:00+00:00",
        "binding_expires_at": "2026-10-07T17:00:00+00:00",
        "incus_executable": "/usr/bin/incus",
        "image_remote": "local",
        "image_fingerprint": "b" * 64,
        "cpu_count": 4,
        "memory_mib": 8192,
        "root_disk_gib": 20,
    }

    env_text = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    assert "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG=" in env_text
    assert str(config_path) in env_text


def test_restore_is_deterministic_except_timestamps(tmp_path: Path) -> None:
    first_dir, first_values = _runtime(tmp_path / "one")
    second_dir, second_values = _runtime(tmp_path / "two")
    clock = lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC)

    first = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path / "s1"),
        environment=first_values,
        config_dir=first_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=clock,
        image_inventory_provider=_trusted_inventory,
    ).restore()
    second = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path / "s2"),
        environment=second_values,
        config_dir=second_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=clock,
        image_inventory_provider=_trusted_inventory,
    ).restore()

    assert first["targetAllocationId"] == second["targetAllocationId"]



def test_restore_fails_closed_when_trusted_image_is_missing(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
        image_inventory_provider=list,
    )

    with pytest.raises(BewindDisposableBootstrapError, match="trusted_image_unavailable"):
        restorer.restore()


def test_restore_fails_closed_when_trusted_image_is_ambiguous(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    inventory = _trusted_inventory("b" * 64) + _trusted_inventory("c" * 64)
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
        image_inventory_provider=lambda: inventory,
    )

    with pytest.raises(BewindDisposableBootstrapError, match="trusted_image_unavailable"):
        restorer.restore()


def test_restore_rejects_wrong_source_metadata(tmp_path: Path) -> None:
    config_dir, values = _runtime(tmp_path)
    inventory = _trusted_inventory()
    inventory[0]["update_source"] = {
        "server": "https://example.invalid",
        "protocol": "simplestreams",
        "alias": "ubuntu/24.04",
    }
    restorer = BewindDisposableBootstrapRestorer(
        safety=_safety(tmp_path),
        environment=values,
        config_dir=config_dir,
        hostname_provider=lambda: "aifordable-lab",
        now=lambda: datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
        image_inventory_provider=lambda: inventory,
    )

    with pytest.raises(BewindDisposableBootstrapError, match="trusted_image_unavailable"):
        restorer.restore()


def test_cli_calls_fixed_restorer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_file = tmp_path / "runner-mcp.env"
    env_file.write_text("RUNNER_MCP_BEARER_TOKEN=" + "s" * 48 + "\n", encoding="utf-8")
    env_file.chmod(0o600)
    safety = object()
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "read_private_runtime",
        lambda config_dir: (
            type("Paths", (), {"env_file": env_file})(),
            object(),
            object(),
        ),
    )
    monkeypatch.setattr(
        cli,
        "load_env_file",
        lambda path: {"RUNNER_MCP_BEARER_TOKEN": "s" * 48},
    )
    monkeypatch.setattr(
        cli,
        "operator_stop_status",
        lambda config_dir: (tmp_path / "operator.stop", safety),
    )

    class FakeRestorer:
        def __init__(self, **kwargs: object) -> None:
            seen.update(kwargs)

        def restore(self) -> dict[str, object]:
            return {
                "schemaVersion": "runner-mcp/bewind-disposable-bootstrap/v1",
                "state": "restored",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "qualificationId": "bewind-ocr-lab-v1",
                "targetAllocationId": "11111111-1111-5111-8111-111111111111",
                "policyValid": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(cli, "BewindDisposableBootstrapRestorer", FakeRestorer)

    result = cli.cmd_bewind_disposable_bootstrap(
        argparse.Namespace(config_dir=str(tmp_path))
    )

    assert result == 0
    assert seen["safety"] is safety
    assert seen["config_dir"] == tmp_path.resolve()
    output = capsys.readouterr().out
    assert "State: restored" in output
    assert "Worker: aifordable-lab" in output
    assert "Normal activation enabled: no" in output


def test_parser_accepts_only_fixed_restore_action() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["bewind-disposable-bootstrap", "restore"])
    assert args.func is cli.cmd_bewind_disposable_bootstrap
    assert args.bewind_disposable_bootstrap_action == "restore"

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "bewind-disposable-bootstrap",
                "restore",
                "--path",
                "/tmp/override",
            ]
        )
