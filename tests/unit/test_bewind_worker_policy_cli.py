from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner_mcp import cli


def test_bewind_worker_policy_cli_calls_fixed_configurator(
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
        lambda config_dir: (SimpleNamespace(env_file=env_file), object(), object()),
    )
    monkeypatch.setattr(
        cli,
        "load_env_file",
        lambda path: {
            "RUNNER_MCP_BEARER_TOKEN": "s" * 48,
            "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG": "/private/target.json",
        },
    )
    monkeypatch.setattr(
        cli,
        "operator_stop_status",
        lambda config_dir: (tmp_path / "operator.stop", safety),
    )

    class FakeConfigurator:
        def __init__(self, **kwargs: object) -> None:
            seen.update(kwargs)

        def configure(self) -> dict[str, object]:
            return {
                "schemaVersion": "runner-mcp/bewind-worker-qualification-policy/v1",
                "state": "configured",
                "workerId": "aifordable-lab",
                "capabilityProfile": "bewind-ocr-qualification-v1",
                "generation": 1,
                "policyValid": True,
                "sourceTargetReady": True,
                "agentRestartRequired": True,
                "normalActivationEnabled": False,
            }

    monkeypatch.setattr(cli, "BewindWorkerQualificationPolicyConfigurator", FakeConfigurator)

    result = cli.cmd_bewind_worker_policy(
        argparse.Namespace(config_dir=str(tmp_path))
    )

    assert result == 0
    assert seen["safety"] is safety
    assert seen["config_dir"] == tmp_path.resolve()
    assert isinstance(seen["environment"], dict)

    output = capsys.readouterr().out
    assert "State: configured" in output
    assert "Worker: aifordable-lab" in output
    assert "Capability: bewind-ocr-qualification-v1" in output
    assert "Generation: 1" in output
    assert "Agent restart required: yes" in output
    assert "Normal activation enabled: no" in output
    assert "s" * 48 not in output
    assert "/private/target.json" not in output


def test_bewind_worker_policy_parser_accepts_only_fixed_configure_action() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["bewind-worker-policy", "configure"])

    assert args.func is cli.cmd_bewind_worker_policy
    assert args.bewind_worker_policy_action == "configure"

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "bewind-worker-policy",
                "configure",
                "--path",
                "/tmp/override",
            ]
        )
