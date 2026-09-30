from __future__ import annotations

import datetime
import json
import subprocess

import pytest

from runner_mcp.host_integrity import FatalProcessClass, HostDiagnosticError
from runner_mcp.host_integrity_linux import (
    JOURNALCTL_MAX_BYTES,
    JOURNALCTL_MAX_RECORDS,
    LinuxJournalDiagnosticAdapter,
)

NOW = datetime.datetime(2026, 9, 30, 12, 0, tzinfo=datetime.UTC)
SINCE = NOW - datetime.timedelta(minutes=30)


class FakeRunner:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
        kernel_stdout: bytes = b"",
        kernel_stderr: bytes = b"",
        kernel_returncode: int = 0,
    ) -> None:
        self.completed = (
            subprocess.CompletedProcess(
                args=[],
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            ),
            subprocess.CompletedProcess(
                args=[],
                returncode=kernel_returncode,
                stdout=kernel_stdout,
                stderr=kernel_stderr,
            ),
        )
        self.calls = []

    def __call__(self, argv, **kwargs):
        call_index = len(self.calls)
        self.calls.append((argv, kwargs))
        return self.completed[min(call_index, 1)]


def row(executable: str, observed_at: datetime.datetime) -> bytes:
    micros = int(observed_at.timestamp() * 1_000_000)
    return (
        json.dumps({"_EXE": executable, "__REALTIME_TIMESTAMP": str(micros)}) + "\n"
    ).encode()


def kernel_row(
    message: object,
    observed_at: datetime.datetime,
    *,
    transport: object = "kernel",
) -> bytes:
    micros = int(observed_at.timestamp() * 1_000_000)
    return (
        json.dumps(
            {
                "_TRANSPORT": transport,
                "MESSAGE": message,
                "__REALTIME_TIMESTAMP": str(micros),
            }
        )
        + "\n"
    ).encode()


def test_fixed_queries_classify_python_without_exposing_path() -> None:
    runner = FakeRunner(stdout=row("/usr/bin/python3.12", NOW - datetime.timedelta(minutes=2)))
    adapter = LinuxJournalDiagnosticAdapter(runner=runner)

    result = adapter.recent_fatal_process_classes(since=SINCE, until=NOW)

    assert len(result) == 1
    assert result[0].process_class == FatalProcessClass.PYTHON_RUNTIME
    process_argv, process_kwargs = runner.calls[0]
    assert process_argv[:5] == [
        "journalctl",
        "--no-pager",
        "--output=json",
        "--output-fields=_EXE,__REALTIME_TIMESTAMP",
        "--priority=0..3",
    ]
    assert process_kwargs["timeout"] == 5
    assert process_kwargs["check"] is False
    assert "shell" not in process_kwargs

    kernel_argv, kernel_kwargs = runner.calls[1]
    assert kernel_argv[:5] == [
        "journalctl",
        "--no-pager",
        "--output=json",
        "--output-fields=__REALTIME_TIMESTAMP,_TRANSPORT,MESSAGE",
        "--priority=0..4",
    ]
    assert kernel_argv[-1] == "_TRANSPORT=kernel"
    assert kernel_kwargs["timeout"] == 5
    assert kernel_kwargs["check"] is False
    assert "shell" not in kernel_kwargs


def test_irrelevant_executable_and_kernel_message_are_ignored() -> None:
    runner = FakeRunner(
        stdout=row("/usr/bin/example-safe-process", NOW),
        kernel_stdout=kernel_row("kernel: ordinary informational message", NOW),
    )
    assert LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
        since=SINCE, until=NOW
    ) == ()


def test_process_record_without_executable_is_ignored() -> None:
    micros = int(NOW.timestamp() * 1_000_000)
    payload = (
        json.dumps({"__REALTIME_TIMESTAMP": str(micros)}) + "\n"
    ).encode()
    runner = FakeRunner(stdout=payload)

    assert LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
        since=SINCE, until=NOW
    ) == ()


@pytest.mark.parametrize(
    "message",
    [
        "mce: [Hardware Error]: CPU 0: Machine Check",
        "[Hardware Error]: Processor context corrupt",
    ],
)
def test_machine_check_messages_map_to_hardware_class(message: str) -> None:
    secret = "host-secret serial-1234"
    runner = FakeRunner(kernel_stdout=kernel_row(f"{message} {secret}", NOW))

    result = LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
        since=SINCE, until=NOW
    )

    assert len(result) == 1
    assert result[0].process_class == FatalProcessClass.HARDWARE_MACHINE_CHECK
    assert secret not in repr(result)


@pytest.mark.parametrize(
    "message",
    [
        "EDAC MC0: 1 UE memory error on DIMM secret-dimm",
        "Memory failure: uncorrected error at private-host-address",
    ],
)
def test_memory_fault_messages_map_to_memory_class(message: str) -> None:
    runner = FakeRunner(kernel_stdout=kernel_row(message, NOW))

    result = LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
        since=SINCE, until=NOW
    )

    assert len(result) == 1
    assert result[0].process_class == FatalProcessClass.MEMORY_ERROR
    assert "secret-dimm" not in repr(result)
    assert "private-host-address" not in repr(result)


@pytest.mark.parametrize(
    "message",
    [
        "nvme nvme0: I/O timeout, resetting controller serial-secret",
        "EXT4-fs error (device nvme0n1p2): metadata corruption private-device",
        "Buffer I/O error on dev nvme0n1, logical block 1234",
    ],
)
def test_storage_fault_messages_map_to_storage_class(message: str) -> None:
    runner = FakeRunner(kernel_stdout=kernel_row(message, NOW))

    result = LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
        since=SINCE, until=NOW
    )

    assert len(result) == 1
    assert result[0].process_class == FatalProcessClass.STORAGE_IO_OR_FILESYSTEM
    assert "serial-secret" not in repr(result)
    assert "private-device" not in repr(result)
    assert "nvme0n1" not in repr(result)


@pytest.mark.parametrize("returncode", [1, 127])
def test_nonzero_process_journalctl_fails_closed_without_stderr(returncode: int) -> None:
    secret = b"/private/host/path token-super-secret"
    runner = FakeRunner(stderr=secret, returncode=returncode)
    with pytest.raises(HostDiagnosticError) as caught:
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )
    assert "private" not in str(caught.value)
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("returncode", [1, 127])
def test_nonzero_kernel_journalctl_fails_closed_without_stderr(returncode: int) -> None:
    secret = b"/private/device token-super-secret"
    runner = FakeRunner(kernel_stderr=secret, kernel_returncode=returncode)
    with pytest.raises(HostDiagnosticError) as caught:
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )
    assert "private" not in str(caught.value)
    assert "secret" not in str(caught.value)


def test_spawn_exception_fails_closed_without_detail() -> None:
    def fail(*_args, **_kwargs):
        raise OSError("/private/host/path token-super-secret")

    with pytest.raises(HostDiagnosticError) as caught:
        LinuxJournalDiagnosticAdapter(runner=fail).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )
    assert str(caught.value) == "host diagnostics unavailable"
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    ("stdout", "kernel_stdout"),
    [
        (b"x" * (JOURNALCTL_MAX_BYTES + 1), b""),
        (b"", b"x" * (JOURNALCTL_MAX_BYTES + 1)),
    ],
)
def test_oversized_output_fails_closed(stdout: bytes, kernel_stdout: bytes) -> None:
    runner = FakeRunner(stdout=stdout, kernel_stdout=kernel_stdout)
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


@pytest.mark.parametrize(
    ("stdout", "kernel_stdout"),
    [
        (b"{}\n" * (JOURNALCTL_MAX_RECORDS + 1), b""),
        (b"", b"{}\n" * (JOURNALCTL_MAX_RECORDS + 1)),
    ],
)
def test_too_many_records_fail_closed(stdout: bytes, kernel_stdout: bytes) -> None:
    runner = FakeRunner(stdout=stdout, kernel_stdout=kernel_stdout)
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json\n",
        b'{"_EXE":123,"__REALTIME_TIMESTAMP":"1"}\n',
        b'{"_EXE":"/usr/bin/python3","__REALTIME_TIMESTAMP":"not-a-time"}\n',
        b"\xff\n",
    ],
)
def test_malformed_process_output_fails_closed(payload: bytes) -> None:
    runner = FakeRunner(stdout=payload)
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json\n",
        kernel_row(123, NOW),
        kernel_row("MCE: hardware error", NOW, transport="userspace"),
        b'{"_TRANSPORT":"kernel","MESSAGE":"MCE: hardware error"}\n',
        b"\xff\n",
    ],
)
def test_malformed_kernel_output_fails_closed(payload: bytes) -> None:
    runner = FakeRunner(kernel_stdout=payload)
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


def test_future_process_event_fails_closed() -> None:
    runner = FakeRunner(stdout=row("/usr/bin/python3", NOW + datetime.timedelta(seconds=1)))
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


def test_future_kernel_event_fails_closed() -> None:
    runner = FakeRunner(
        kernel_stdout=kernel_row(
            "MCE: hardware error",
            NOW + datetime.timedelta(seconds=1),
        )
    )
    with pytest.raises(HostDiagnosticError):
        LinuxJournalDiagnosticAdapter(runner=runner).recent_fatal_process_classes(
            since=SINCE, until=NOW
        )


def test_naive_or_reversed_window_fails_closed_without_running() -> None:
    runner = FakeRunner()
    adapter = LinuxJournalDiagnosticAdapter(runner=runner)
    with pytest.raises(HostDiagnosticError):
        adapter.recent_fatal_process_classes(
            since=SINCE.replace(tzinfo=None),
            until=NOW,
        )
    with pytest.raises(HostDiagnosticError):
        adapter.recent_fatal_process_classes(since=NOW, until=SINCE)
    assert runner.calls == []
