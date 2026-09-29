from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import ProjectRegistry
from .text_redaction import TextRedactionError, redact_bounded_text

MAX_JOURNAL_LINES = 100
MAX_JOURNAL_RAW_BYTES = 32 * 1024
MAX_JOURNAL_OUTPUT_BYTES = 32 * 1024
_JOURNAL_READ_CHUNK = 4096
_FIXED_ENV = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
}


class ServiceJournalError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class JournalCapture:
    text: str
    truncated: bool


class JournalBackend(Protocol):
    def tail(self, unit: str, *, lines: int) -> JournalCapture: ...


def _valid_executable(path: Path) -> bool:
    return (
        path.is_absolute()
        and path.exists()
        and path.is_file()
        and not path.is_symlink()
        and os.access(path, os.X_OK)
    )


def _detect_journalctl() -> Path:
    for candidate in (Path("/usr/bin/journalctl"), Path("/bin/journalctl")):
        if _valid_executable(candidate):
            return candidate
    raise ServiceJournalError("journalctl is unavailable")


def _run_bounded_stdout(
    arguments: list[str],
    *,
    timeout_seconds: float,
) -> JournalCapture:
    try:
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=_FIXED_ENV,
        )
    except OSError as exc:
        raise ServiceJournalError("Service journal command failed") from exc

    if process.stdout is None:
        process.kill()
        process.wait()
        raise ServiceJournalError("Service journal command failed")

    retained = bytearray()
    truncated = False
    reader_failed = False

    def drain_stdout() -> None:
        nonlocal truncated, reader_failed
        try:
            while True:
                chunk = process.stdout.read(_JOURNAL_READ_CHUNK)
                if not chunk:
                    return
                remaining = MAX_JOURNAL_RAW_BYTES - len(retained)
                if remaining > 0:
                    retained.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
        except OSError:
            reader_failed = True

    reader = threading.Thread(
        target=drain_stdout,
        name="runner-mcp-service-journal-reader",
        daemon=True,
    )
    reader.start()

    try:
        return_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        reader.join(timeout=1)
        process.stdout.close()
        raise ServiceJournalError("Service journal command timed out") from exc

    reader.join(timeout=1)
    process.stdout.close()
    if reader.is_alive() or reader_failed:
        raise ServiceJournalError("Service journal command failed")
    if return_code != 0:
        raise ServiceJournalError("Service journal command failed")

    return JournalCapture(
        text=bytes(retained).decode("utf-8", errors="replace"),
        truncated=truncated,
    )


class SystemdJournalBackend:
    def __init__(
        self,
        *,
        executable: Path | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        selected = executable if executable is not None else _detect_journalctl()
        if not _valid_executable(selected):
            raise ServiceJournalError("journalctl is unavailable")
        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or not 0 < float(timeout_seconds) <= 10
        ):
            raise ValueError("journal timeout must be greater than zero and at most 10 seconds")
        self.executable = selected
        self.timeout_seconds = float(timeout_seconds)

    def tail(self, unit: str, *, lines: int) -> JournalCapture:
        if (
            not isinstance(lines, int)
            or isinstance(lines, bool)
            or not 1 <= lines <= MAX_JOURNAL_LINES
        ):
            raise ServiceJournalError("Journal line limit must be between 1 and 100")
        return _run_bounded_stdout(
            [
                str(self.executable),
                "--user",
                "--unit",
                unit,
                "--no-pager",
                "--output=cat",
                f"--lines={lines}",
            ],
            timeout_seconds=self.timeout_seconds,
        )


class ServiceJournalReader:
    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        secret_values: Iterable[str] = (),
        private_paths: Iterable[str] = (),
        backend: JournalBackend | None = None,
    ) -> None:
        self.registry = registry
        self.secret_values = tuple(
            value for value in secret_values if isinstance(value, str) and value
        )
        self.private_paths = tuple(
            value for value in private_paths if isinstance(value, str) and value
        )
        self.backend = backend

    def _backend(self) -> JournalBackend:
        if self.backend is None:
            self.backend = SystemdJournalBackend()
        return self.backend

    def tail(
        self,
        project: str,
        service_alias: str,
        *,
        lines: int = 50,
    ) -> dict[str, object]:
        if (
            not isinstance(lines, int)
            or isinstance(lines, bool)
            or not 1 <= lines <= MAX_JOURNAL_LINES
        ):
            raise ServiceJournalError("Journal line limit must be between 1 and 100")

        project_config = self.registry.projects.get(project)
        if project_config is None:
            raise ServiceJournalError("Unknown or disabled project")
        service = project_config.services.get(service_alias)
        if service is None:
            raise ServiceJournalError("Unknown or disabled service")
        if not service.allow_log_read:
            raise ServiceJournalError("Service journal read is not allowed")

        capture = self._backend().tail(service.unit, lines=lines)

        secret_values = list(self.secret_values)
        secret_values.append(service.unit)
        if service.health_url is not None:
            health_url = str(service.health_url)
            secret_values.append(health_url)
            stripped_health_url = health_url.rstrip("/")
            if stripped_health_url:
                secret_values.append(stripped_health_url)

        private_paths = list(self.private_paths)
        private_paths.append(str(project_config.root))
        if project_config.deployment is not None:
            private_paths.append(str(project_config.deployment.release_root))

        redaction_input_limit = MAX_JOURNAL_RAW_BYTES
        if capture.truncated:
            redaction_input_limit -= 1

        try:
            redacted = redact_bounded_text(
                capture.text,
                secret_values=secret_values,
                private_paths=private_paths,
                max_input_bytes=redaction_input_limit,
                max_output_bytes=MAX_JOURNAL_OUTPUT_BYTES,
            )
        except TextRedactionError as exc:
            raise ServiceJournalError("Service journal content could not be redacted") from exc

        content = redacted.text
        return {
            "project": project,
            "service": service_alias,
            "line_count": len(content.splitlines()),
            "truncated": (
                capture.truncated
                or redacted.input_truncated
                or redacted.output_truncated
            ),
            "content": content,
        }
