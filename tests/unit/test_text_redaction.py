import pytest

from runner_mcp.text_redaction import TextRedactionError, redact_bounded_text


def redact(
    text: str,
    *,
    secret_values: list[str] | None = None,
    private_paths: list[str] | None = None,
    max_input_bytes: int = 4096,
    max_output_bytes: int = 4096,
):
    return redact_bounded_text(
        text,
        secret_values=secret_values or [],
        private_paths=private_paths or [],
        max_input_bytes=max_input_bytes,
        max_output_bytes=max_output_bytes,
    )


def test_known_secret_embedded_in_ordinary_text_is_redacted() -> None:
    secret = "private-secret-value-1234"
    result = redact(
        f"customer context before {secret} after",
        secret_values=[secret, secret],
    )

    assert secret not in result.text
    assert result.text == "customer context before [REDACTED] after"
    assert result.input_truncated is False
    assert result.output_truncated is False


def test_known_private_path_embedded_in_text_is_redacted() -> None:
    path = "/srv/private/example/project"
    result = redact(
        f"trace points to {path}/module.py",
        private_paths=[path, "", path],
    )

    assert path not in result.text
    assert result.text == "trace points to [PRIVATE_PATH]/module.py"


@pytest.mark.parametrize(
    ("raw", "literal"),
    [
        (
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",
            "abcdefghijklmnopqrstuvwxyz123456",
        ),
        ("password=super-secret-value", "super-secret-value"),
        ("token:abcdefghijklmnop", "abcdefghijklmnop"),
        ("ghp_abcdefghijklmnopqrstuvwxyz1234", "ghp_abcdefghijklmnopqrstuvwxyz1234"),
        (
            "github_pat_abcdefghijklmnopqrstuvwxyz_123456",
            "github_pat_abcdefghijklmnopqrstuvwxyz_123456",
        ),
    ],
)
def test_generic_secret_forms_are_redacted(raw: str, literal: str) -> None:
    result = redact(raw)

    assert literal not in result.text
    assert "[REDACTED]" in result.text


def test_short_known_secret_preserves_existing_test_runner_behavior() -> None:
    result = redact("value=abc", secret_values=["abc"])

    assert result.text == "value=abc"


def test_input_truncation_redacts_partial_known_secret_at_boundary() -> None:
    secret = "very-secret-value-that-must-not-leak"
    text = ("x" * 60) + secret

    result = redact(
        text,
        secret_values=[secret],
        max_input_bytes=68,
        max_output_bytes=256,
    )

    assert result.input_truncated is True
    assert "very-sec" not in result.text
    assert "[REDACTED]" in result.text
    assert "[INPUT TRUNCATED BY RUNNER MCP]" in result.text


def test_input_truncation_redacts_partial_private_path_at_boundary() -> None:
    path = "/very/private/application/path"
    text = ("x" * 60) + path

    result = redact(
        text,
        private_paths=[path],
        max_input_bytes=68,
        max_output_bytes=256,
    )

    assert result.input_truncated is True
    assert "/very/pr" not in result.text
    assert "[PRIVATE_PATH]" in result.text


def test_output_truncation_is_deterministic_and_bounded() -> None:
    first = redact(
        "x" * 1000,
        max_input_bytes=128,
        max_output_bytes=96,
    )
    second = redact(
        "x" * 1000,
        max_input_bytes=128,
        max_output_bytes=96,
    )

    assert first == second
    assert first.input_truncated is True
    assert first.output_truncated is True
    assert len(first.text.encode("utf-8")) <= 96
    assert "[OUTPUT TRUNCATED BY RUNNER MCP]" in first.text


def test_multibyte_text_is_never_cut_into_invalid_utf8() -> None:
    result = redact(
        "é" * 100,
        max_input_bytes=65,
        max_output_bytes=128,
    )

    assert result.input_truncated is True
    result.text.encode("utf-8")


@pytest.mark.parametrize(
    ("input_limit", "output_limit"),
    [
        (63, 128),
        (128, 63),
        (16 * 1024 * 1024 + 1, 128),
        (128, 16 * 1024 * 1024 + 1),
    ],
)
def test_invalid_limits_fail_with_bounded_error(
    input_limit: int,
    output_limit: int,
) -> None:
    with pytest.raises(TextRedactionError, match="must be between"):
        redact_bounded_text(
            "safe",
            max_input_bytes=input_limit,
            max_output_bytes=output_limit,
        )


def test_configured_redaction_literals_do_not_appear_in_output() -> None:
    secret = "never-return-this-secret"
    path = "/never/return/this/path"
    result = redact(
        f"{secret} {path} password=another-private-value",
        secret_values=[secret],
        private_paths=[path],
    )

    assert secret not in result.text
    assert path not in result.text
    assert "another-private-value" not in result.text
