from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


class FabricAgentRestartError(RuntimeError):
    """Bounded Fabric-agent restart failure without private detail leakage."""


def _validated_launcher(home: Path) -> Path:
    launcher = home / ".local" / "bin" / "runner-fabric"
    try:
        info = launcher.lstat()
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_launcher_unavailable") from exc
    if not stat.S_ISLNK(info.st_mode):
        raise FabricAgentRestartError("fabric_agent_launcher_unmanaged")
    try:
        resolved = launcher.resolve(strict=True)
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_launcher_unmanaged") from exc
    slots = (
        home
        / ".local"
        / "state"
        / "runner-fabric"
        / "control-plane-update"
        / "slots"
    )
    try:
        slots_root = slots.resolve(strict=True)
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_launcher_unmanaged") from exc
    if not resolved.is_relative_to(slots_root) or not os.access(resolved, os.X_OK):
        raise FabricAgentRestartError("fabric_agent_launcher_unmanaged")
    return launcher


def _health_url(resource_url: str) -> str:
    parsed = urlsplit(resource_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/mcp"
    ):
        raise FabricAgentRestartError("fabric_agent_resource_invalid")
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            "/healthz",
            "",
            "",
        )
    )


def _read_pid(pid_file: Path) -> int:
    try:
        raw = pid_file.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_pid_unavailable") from exc
    if not raw.isdecimal():
        raise FabricAgentRestartError("fabric_agent_pid_invalid")
    pid = int(raw)
    if not 2 <= pid <= 2_147_483_647:
        raise FabricAgentRestartError("fabric_agent_pid_invalid")
    return pid


def _same_user_process(pid: int) -> bool:
    status = Path(f"/proc/{pid}/status")
    cmdline = Path(f"/proc/{pid}/cmdline")
    try:
        status_text = status.read_text(encoding="utf-8")
        raw_cmd = cmdline.read_bytes()
    except OSError:
        return False

    uid_line = next(
        (line for line in status_text.splitlines() if line.startswith("Uid:")),
        "",
    )
    parts = uid_line.split()
    if len(parts) < 2 or not parts[1].isdecimal():
        return False
    if int(parts[1]) != os.geteuid():
        return False

    argv = [
        part.decode("utf-8", errors="strict")
        for part in raw_cmd.split(b"\x00")
        if part
    ]
    return (
        len(argv) >= 2
        and any("runner-fabric" in item for item in argv)
        and "agent-serve-qualification" in argv
    )


def _wait_process_exit(pid: int, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _same_user_process(pid):
            return True
        time.sleep(0.1)
    return not _same_user_process(pid)


def _wait_health(url: str, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "Runner-MCP-fabric-agent-restart"},
        )
        try:
            with urllib.request.urlopen(request, timeout=1.0) as response:
                if int(response.status) == 200:
                    raw = response.read(4097)
                    if len(raw) <= 4096:
                        try:
                            payload = json.loads(raw.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            payload = None
                        if payload == {"status": "ok"}:
                            return True
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ):
            pass
        time.sleep(0.2)
    return False


def restart_fabric_qualification_agent(
    *,
    config_dir: Path,
    resource_url: str,
    bearer_token: str,
    home: Path | None = None,
) -> dict[str, object]:
    if not config_dir.is_absolute():
        raise FabricAgentRestartError("fabric_agent_config_invalid")
    try:
        config_root = config_dir.resolve(strict=True)
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_config_invalid") from exc
    if (
        not isinstance(bearer_token, str)
        or len(bearer_token) < 32
        or len(bearer_token) > 4096
        or not bearer_token.isascii()
        or any(ord(char) < 33 or ord(char) == 127 for char in bearer_token)
    ):
        raise FabricAgentRestartError("fabric_agent_token_invalid")

    home_root = (home or Path.home()).expanduser().resolve()
    launcher = _validated_launcher(home_root)
    health_url = _health_url(resource_url)
    pid_file = config_root / "fabric-qualification.pid"
    log_file = config_root / "fabric-qualification.log"

    old_pid = _read_pid(pid_file)
    if not _same_user_process(old_pid):
        raise FabricAgentRestartError("fabric_agent_process_mismatch")

    try:
        os.kill(old_pid, signal.SIGTERM)
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_stop_failed") from exc
    if not _wait_process_exit(old_pid):
        raise FabricAgentRestartError("fabric_agent_stop_timeout")

    env = {
        "HOME": str(home_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "RUNNER_FABRIC_AGENT_RESOURCE_URL": resource_url,
        "RUNNER_FABRIC_AGENT_BEARER_TOKEN": bearer_token,
    }
    try:
        with log_file.open("ab", buffering=0) as log_handle:
            process = subprocess.Popen(
                (str(launcher), "agent-serve-qualification"),
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                cwd="/",
                env=env,
                close_fds=True,
            )
    except OSError as exc:
        raise FabricAgentRestartError("fabric_agent_start_failed") from exc

    try:
        pid_file.write_text(f"{process.pid}\n", encoding="ascii")
        pid_file.chmod(0o600)
    except OSError as exc:
        try:
            process.terminate()
        except OSError:
            pass
        raise FabricAgentRestartError("fabric_agent_pid_write_failed") from exc

    if process.pid == old_pid or not _wait_health(health_url):
        try:
            process.terminate()
        except OSError:
            pass
        raise FabricAgentRestartError("fabric_agent_health_failed")

    return {
        "state": "restarted",
        "pid_changed": True,
        "healthy": True,
    }
