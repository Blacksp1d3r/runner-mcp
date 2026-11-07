"""Synthetic kernel fixtures; no calls to the real service or procfs."""

from pathlib import Path

import pytest

from runner_mcp.local_process_facts import (
    LocalProcessFactsUnavailable,
    read_current_linux_process,
)

BOOT = "12345678-1234-1234-1234-123456789abc"


def fake_proc(tmp_path: Path, *, pid: int = 437, boot: str = BOOT,
              start_ticks: str = "92847", name: str = "python worker") -> Path:
    path = tmp_path / "proc"
    (path / "sys/kernel/random").mkdir(parents=True)
    (path / "sys/kernel/random/boot_id").write_text(boot, encoding="ascii")
    (path / str(pid)).mkdir()
    # Fields 3-21 contain 19 tokens. Field 22 is the 20th token.
    stat = f"{pid} ({name}) S " + "1 " * 18 + f"{start_ticks} 0 0\n"
    (path / str(pid) / "stat").write_text(stat, encoding="ascii")
    return path


def test_linux_reader_collects_boot_pid_start_generation(tmp_path):
    proc = fake_proc(tmp_path, name="strange ) process")
    fact = read_current_linux_process(proc=proc, getpid=lambda: 437)
    assert fact.boot_id == BOOT
    assert fact.process_id == 437
    assert fact.start_ticks == 92847
    assert fact.generation == f"{BOOT}:437:92847"
    assert fact.platform == "linux"


def test_pid_reuse_and_reboot_change_generation(tmp_path):
    proc = fake_proc(tmp_path)
    first = read_current_linux_process(proc=proc, getpid=lambda: 437)
    (proc / "437/stat").write_text("437 (python) S " + "1 " * 18 + "92848 0 0\n")
    next_process = read_current_linux_process(proc=proc, getpid=lambda: 437)
    assert first.generation != next_process.generation
    (proc / "sys/kernel/random/boot_id").write_text(
        "87654321-1234-1234-1234-123456789abc"
    )
    after_boot = read_current_linux_process(proc=proc, getpid=lambda: 437)
    assert after_boot.generation != next_process.generation


@pytest.mark.parametrize("bad_stat", [
    "437 (bad)",
    "12 (wrong) S " + "1 " * 19,
    "437 (bad) S " + "1 " * 18 + "0",
])
def test_invalid_process_stats_fail_closed(tmp_path, bad_stat):
    proc = fake_proc(tmp_path)
    (proc / "437/stat").write_text(bad_stat)
    with pytest.raises(LocalProcessFactsUnavailable):
        read_current_linux_process(proc=proc, getpid=lambda: 437)


def test_missing_boot_or_stat_fails_closed(tmp_path):
    proc = fake_proc(tmp_path)
    (proc / "sys/kernel/random/boot_id").unlink()
    with pytest.raises(LocalProcessFactsUnavailable):
        read_current_linux_process(proc=proc, getpid=lambda: 437)


def test_invalid_pid_not_scanned(tmp_path):
    proc = fake_proc(tmp_path)
    with pytest.raises(LocalProcessFactsUnavailable):
        read_current_linux_process(proc=proc, getpid=lambda: 0)
