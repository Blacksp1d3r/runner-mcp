from __future__ import annotations

import json
from pathlib import Path

from runner_mcp.cli import main


def test_registered_app_plugin_package_cli_hides_connection_metadata(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "runner-plugin"
    app_id = "plugin_asdk_app_abc123"

    result = main(
        [
            "plugin-package",
            "registered-app",
            "--app-id",
            app_id,
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert "first-party plugin package created" in captured.out
    assert "Mode: registered-app" in captured.out
    assert app_id not in captured.out
    assert str(output) not in captured.out

    app_manifest = json.loads((output / ".app.json").read_text(encoding="utf-8"))
    assert app_manifest["apps"]["runner-mcp"]["id"] == "asdk_app_abc123"


def test_http_plugin_package_cli_never_prints_url_or_token_value(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    output = tmp_path / "runner-plugin"
    endpoint = "https://control.example.invalid/mcp"
    secret = "private-bearer-value"
    monkeypatch.setenv("RUNNER_MCP_PLUGIN_TOKEN", secret)

    result = main(
        [
            "plugin-package",
            "http",
            "--url",
            endpoint,
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert "Mode: http" in captured.out
    assert endpoint not in captured.out
    assert secret not in captured.out
    assert secret not in captured.err

    mcp = json.loads((output / ".mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["runner_mcp"]
    assert server["bearer_token_env_var"] == "RUNNER_MCP_PLUGIN_TOKEN"
    assert secret not in (output / ".mcp.json").read_text(encoding="utf-8")


def test_plugin_package_cli_prints_output_only_when_requested(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "runner-plugin"

    result = main(
        [
            "plugin-package",
            "registered-app",
            "--app-id",
            "asdk_app_abc123",
            "--output",
            str(output),
            "--show-output-location",
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert str(output.resolve()) in captured.out


def test_plugin_package_cli_reports_bounded_validation_failure(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "runner-plugin"

    result = main(
        [
            "plugin-package",
            "http",
            "--url",
            "http://public.example.invalid/mcp",
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "HTTPS or loopback HTTP" in captured.err
    assert "public.example.invalid" not in captured.err
    assert not output.exists()
