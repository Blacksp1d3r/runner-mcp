from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

_MIN_LIMIT_BYTES = 64
_MAX_LIMIT_BYTES = 16 * 1024 * 1024
_INPUT_TRUNCATED_MARKER = "\n[INPUT TRUNCATED BY RUNNER MCP]\n"
_OUTPUT_TRUNCATED_MARKER = "\n[OUTPUT TRUNCATED BY RUNNER MCP]\n"

_GENERIC_SECRET_RULES = (
    (
        re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?im)(\b(?:password|passwd|token|secret|api[_-]?key)\b"
            r"\s*[:=]\s*)([^\s,;]{8,})"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "[REDACTED]",
    ),
    (
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        "[REDACTED]",
    ),
)


class TextRedactionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RedactedText:
    text: str
    input_truncated: bool
    output_truncated: bool


def _validate_limit(value: int, *, label: str) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < _MIN_LIMIT_BYTES
        or value > _MAX_LIMIT_BYTES
    ):
        raise TextRedactionError(
            f"{label} must be between {_MIN_LIMIT_BYTES} and {_MAX_LIMIT_BYTES} bytes"
        )


def _encode(text: str) -> bytes:
    return text.encode("utf-8", errors="replace")


def _bounded_prefix(text: str, max_bytes: int) -> tuple[str, bool]:
    encoded = _encode(text)
    if len(encoded) <= max_bytes:
        return text, False
    return encoded[:max_bytes].decode("utf-8", errors="ignore"), True


def _unique_sensitive_values(
    values: Iterable[str],
    *,
    min_length: int,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for value in values
                if isinstance(value, str) and len(value) >= min_length
            },
            key=lambda item: (-len(item), item),
        )
    )


def _redact_boundary_partial(
    text: str,
    *,
    values: tuple[str, ...],
    replacement: str,
) -> str:
    if not text:
        return text
    best = 0
    for value in values:
        upper = min(len(value) - 1, len(text))
        for length in range(upper, 0, -1):
            if length <= best:
                break
            if text.endswith(value[:length]):
                best = length
                break
    if best:
        return text[:-best] + replacement
    return text


def _bound_output(text: str, max_bytes: int) -> tuple[str, bool]:
    encoded = _encode(text)
    if len(encoded) <= max_bytes:
        return text, False

    marker = _OUTPUT_TRUNCATED_MARKER.encode("utf-8")
    prefix_budget = max_bytes - len(marker)
    prefix = encoded[:prefix_budget].decode("utf-8", errors="ignore")
    bounded = prefix + _OUTPUT_TRUNCATED_MARKER
    while len(_encode(bounded)) > max_bytes and prefix:
        prefix = prefix[:-1]
        bounded = prefix + _OUTPUT_TRUNCATED_MARKER
    return bounded, True


def redact_bounded_text(
    text: str,
    *,
    secret_values: Iterable[str] = (),
    private_paths: Iterable[str] = (),
    max_input_bytes: int,
    max_output_bytes: int,
) -> RedactedText:
    """Redact known/private literals and common secret forms within explicit bounds."""
    if not isinstance(text, str):
        raise TextRedactionError("text must be a string")
    _validate_limit(max_input_bytes, label="max_input_bytes")
    _validate_limit(max_output_bytes, label="max_output_bytes")

    secrets = _unique_sensitive_values(secret_values, min_length=4)
    paths = _unique_sensitive_values(private_paths, min_length=1)

    redacted, input_truncated = _bounded_prefix(text, max_input_bytes)

    for value in secrets:
        redacted = redacted.replace(value, "[REDACTED]")
    for value in paths:
        redacted = redacted.replace(value, "[PRIVATE_PATH]")

    if input_truncated:
        redacted = _redact_boundary_partial(
            redacted,
            values=secrets,
            replacement="[REDACTED]",
        )
        redacted = _redact_boundary_partial(
            redacted,
            values=paths,
            replacement="[PRIVATE_PATH]",
        )

    for pattern, replacement in _GENERIC_SECRET_RULES:
        redacted = pattern.sub(replacement, redacted)

    if input_truncated:
        redacted += _INPUT_TRUNCATED_MARKER

    bounded, output_truncated = _bound_output(redacted, max_output_bytes)
    return RedactedText(
        text=bounded,
        input_truncated=input_truncated,
        output_truncated=output_truncated,
    )
