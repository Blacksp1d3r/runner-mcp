"""Synthetic /proc/self only: inode intersection, same namespace and races."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from runner_mcp.local_self_tcp_facts import read_current_self_tcp_listeners

_HEADER = "sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n"


def _table(inode: int, port: int, state: str = "0A", *, ipv6: bool = False) -> str:
    local = "0" * (32 if ipv6 else 8) + f":{port:04X}"
    return _HEADER + f"0: {local} 00000000:0000 {state} 0:0 0:0 0 0 0 {inode} 0\n"


def _fixture(tmp_path: Path, *, inode: int = 123, port: int = 8080) -> Path:
    (tmp_path / "self/fd").mkdir(parents=True)
    (tmp_path / "self/net").mkdir()
    (tmp_path / "self/fd/7").symlink_to(f"socket:[{inode}]")
    (tmp_path / "self/net/tcp").write_text(_table(inode, port), encoding="ascii")
    (tmp_path / "self/net/tcp6").write_text(_HEADER, encoding="ascii")
    return tmp_path


def test_only_own_tcp_listening_inode_is_returned(tmp_path: Path) -> None:
    proc = _fixture(tmp_path)
    with (proc / "self/net/tcp").open("a", encoding="ascii") as stream:
        stream.write(_table(999, 9999).splitlines()[1] + "\n")
    assert read_current_self_tcp_listeners(proc=proc) == (("tcp4", 8080),)


def test_two_process_namespaces_same_port_are_not_merged(tmp_path: Path) -> None:
    first = _fixture(tmp_path / "one", inode=101, port=8000)
    second = _fixture(tmp_path / "two", inode=102, port=8000)
    assert read_current_self_tcp_listeners(proc=first) == (("tcp4", 8000),)
    assert read_current_self_tcp_listeners(proc=second) == (("tcp4", 8000),)


def test_ipv6_only_socket_is_locally_observed(tmp_path: Path) -> None:
    proc = _fixture(tmp_path, inode=444)
    (proc / "self/net/tcp").write_text(_HEADER, encoding="ascii")
    (proc / "self/net/tcp6").write_text(_table(444, 443, ipv6=True), encoding="ascii")
    assert read_current_self_tcp_listeners(proc=proc) == (("tcp6", 443),)


@pytest.mark.parametrize("bad", ["socket:[0]", "socket:[abc]", "socket:[18446744073709551616]"])
def test_bad_socket_inode_fails_closed(tmp_path: Path, bad: str) -> None:
    proc = _fixture(tmp_path)
    (proc / "self/fd/7").unlink()
    (proc / "self/fd/7").symlink_to(bad)
    assert read_current_self_tcp_listeners(proc=proc) is None


def test_tcp_table_missing_or_incomplete_is_unknown(tmp_path: Path) -> None:
    proc = _fixture(tmp_path)
    (proc / "self/net/tcp6").unlink()
    assert read_current_self_tcp_listeners(proc=proc) is None


def test_tcp_nonlisten_is_not_observed_as_listener(tmp_path: Path) -> None:
    proc = _fixture(tmp_path)
    (proc / "self/net/tcp").write_text(_table(123, 8000, "01"), encoding="ascii")
    assert read_current_self_tcp_listeners(proc=proc) == ()


def test_socket_fd_changes_between_reads_are_unknown(tmp_path: Path, monkeypatch) -> None:
    proc = _fixture(tmp_path)
    original = os.readlink
    counts = {"read": 0}

    def changing_fd(path):
        counts["read"] += 1
        value = original(path)
        if counts["read"] == 1:
            (proc / "self/fd/7").unlink()
            (proc / "self/fd/7").symlink_to("socket:[124]")
        return value

    monkeypatch.setattr(os, "readlink", changing_fd)
    assert read_current_self_tcp_listeners(proc=proc) is None


def test_proc_tables_cannot_be_unbounded(tmp_path: Path) -> None:
    proc = _fixture(tmp_path)
    (proc / "self/net/tcp").write_text("X" * (512 * 1024 + 1), encoding="ascii")
    assert read_current_self_tcp_listeners(proc=proc) is None


def test_live_proc_self_fd_scan_handles_its_own_directory_fd() -> None:
    """Linux-only read-only regression for a transient scandir descriptor."""
    if not Path("/proc/self/fd").is_dir():
        pytest.skip("Linux procfs unavailable")
    from runner_mcp.local_self_tcp_facts import _own_socket_inodes

    assert _own_socket_inodes(Path("/proc")) is not None
