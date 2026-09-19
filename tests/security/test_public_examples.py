from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_env_example_contains_no_bearer_secret() -> None:
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    token_line = next(line for line in lines if line.startswith("RUNNER_MCP_BEARER_TOKEN="))
    assert token_line == "RUNNER_MCP_BEARER_TOKEN="


def test_project_example_uses_runtime_placeholders_for_private_values() -> None:
    text = (ROOT / "config" / "projects.example.yml").read_text(encoding="utf-8")

    private_fields = ("root:", "health_url:", "database_alias:")
    for field in private_fields:
        line = next(line for line in text.splitlines() if line.strip().startswith(field))
        assert "${RUNNER_MCP_" in line

    service_line = next(
        line for line in text.splitlines() if "RUNNER_MCP_EXAMPLE_STAGING_SERVICE" in line
    )
    assert "${RUNNER_MCP_" in service_line
