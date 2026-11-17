"""Werkelijke systemd-user-gestuurde Runner-MCP upgrade/rollback in disposable CI.

De geregistreerde ServiceManager start/herstart één uitdrukkelijk test-owned
systemd-userunit. Na elke echte wheelwisseling blijven het oude PID en de oude
geladen versie zichtbaar tot systemd de service herstart. Dit verleent geen
service- of configuratiebevoegdheid aan een echte server.
"""

from __future__ import annotations

import json
import os
import re
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from qualify_manual_serving_roundtrip_ci import _private_ci_root, _start_ticks

UNIT = "runner-mcp-669-disposable-manual.service"
MARKER = "Description=Runner-MCP 669 disposable manual upgrade proof"


def _admit() -> None:
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
        or os.geteuid() == 0
        or Path("/proc/1/comm").read_text(encoding="ascii").strip() != "systemd"
        or os.environ.get("XDG_RUNTIME_DIR") != f"/run/user/{os.geteuid()}"
    ):
        raise RuntimeError("disposable nonroot GitHub-hosted systemd user manager required")


def _read_unit() -> dict[str, str]:
    result = subprocess.run(
        [
            "/usr/bin/systemctl", "--user", "show", UNIT,
            "--property=LoadState", "--property=ActiveState",
            "--property=MainPID", "--property=FragmentPath", "--no-pager",
        ],
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
             "XDG_RUNTIME_DIR": f"/run/user/{os.geteuid()}"},
        stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError("cannot read bounded CI user unit")
    return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)


def _health(port: int) -> tuple[str, str] | None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as r:
            if r.status != 200 or json.load(r) != {"status": "ok"}:
                raise RuntimeError("non-healthy systemd server")
            version = r.headers.get("X-Runner-MCP-Loaded-Version")
            instance = r.headers.get("X-Runner-MCP-Instance-ID")
            if not version or not instance or not re.fullmatch(r"[0-9a-f]{32}", instance):
                raise RuntimeError("missing loaded generation headers")
            return version, instance
    except (urllib.error.URLError, OSError, TimeoutError):
        return None


def _install_ci_fixture(work: Path, unit_file: Path, cli: Path) -> int:
    from runner_mcp.onboarding import SetupAnswers, install_private_configuration

    project = work / "systemd-project"
    project.mkdir(mode=0o700)
    home = work / "systemd-home"
    home.mkdir(mode=0o700)
    cfg = work / "systemd-private-config"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    install_private_configuration(
        config_dir=cfg,
        answers=SetupAnswers(
            resource_url=f"http://127.0.0.1:{port}/mcp",
            auth_issuer=f"http://127.0.0.1:{port}/",
            project_code="ci", project_name="CI",
            repository="example/ci", project_root=project,
        ),
    )
    if any(" " in str(path) or "\n" in str(path) for path in (work, home, cfg, cli)):
        raise RuntimeError("systemd CI paths cannot contain whitespace")
    unit_bytes = (
        "[Unit]\n" + MARKER + "\n"
        "[Service]\nType=exec\nRestart=no\n"
        f"WorkingDirectory={work}\nEnvironment=HOME={home}\n"
        f"ExecStart={cli} --config-dir {cfg} serve --host 127.0.0.1 "
        f"--port {port} --log-level warning\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(unit_file, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(unit_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    reload = subprocess.run(
        ["/usr/bin/systemctl", "--user", "daemon-reload"],
        env={"PATH": "/usr/bin:/bin", "XDG_RUNTIME_DIR": f"/run/user/{os.geteuid()}"},
        capture_output=True, text=True, timeout=10, check=False,
    )
    if reload.returncode:
        raise RuntimeError("disposable systemd daemon reload failed")
    (work / "systemd-port.txt").write_text(str(port), encoding="ascii")
    return port


def _manager(work: Path, port: int):
    from runner_mcp.config import ProjectConfig, ProjectRegistry, ServiceConfig
    from runner_mcp.operational_safety import OperatorSafetyGuard, RetentionPolicy
    from runner_mcp.service_manager import ServiceManager, SystemdUserBackend

    reg = ProjectRegistry(
        projects={"ci": ProjectConfig(
            display_name="CI", repository="example/ci", root=work,
            environment="staging",
            services={"server": ServiceConfig(
                unit=UNIT, health_url=f"http://127.0.0.1:{port}/healthz",
                allow_start=True, allow_restart=True,
            )},
        )}
    )
    return ServiceManager(
        registry=reg,
        safety=OperatorSafetyGuard(
            stop_file=work / "operator-stop", retention=RetentionPolicy(),
            retention_confirmed=True,
        ),
        backend=SystemdUserBackend(),
    )


def _attest_unit(unit_file: Path) -> dict[str, str]:
    info = unit_file.lstat()
    if (
        not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
        or (info.st_mode & 0o077) != 0
        or MARKER not in unit_file.read_text(encoding="utf-8").splitlines()
    ):
        raise RuntimeError("test unit changed or unowned")
    state = _read_unit()
    if state.get("LoadState") != "loaded" or state.get("FragmentPath") != str(unit_file):
        raise RuntimeError("systemd unit source does not match owned CI unit")
    return state


def _new_generation(port: int, version: str, previous: dict | None) -> dict:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = _read_unit()
        raw_pid = state.get("MainPID", "")
        if state.get("ActiveState") == "active" and raw_pid.isdecimal() and int(raw_pid) > 0:
            pid = int(raw_pid)
            if not Path(f"/proc/{pid}/stat").is_file():
                time.sleep(0.2)
                continue
            response = _health(port)
            if response:
                loaded, instance = response
                if loaded != version:
                    raise RuntimeError("the server is not serving the installed version")
                ticks = _start_ticks(pid)
                if previous and (
                    pid == previous["pid"] or ticks == previous["ticks"]
                    or instance == previous["instance"]
                ):
                    raise RuntimeError("the previous process generation was reused")
                return {"pid": pid, "ticks": ticks, "instance": instance, "version": loaded}
        time.sleep(0.2)
    raise RuntimeError("the systemd-managed service never became healthy")


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in ("0.1.88", "0.1.174", "0.1.175"):
        raise RuntimeError("only two fixed CI versions are supported")
    version = sys.argv[1]
    work = _private_ci_root(sys.argv[2])
    _admit()
    unit_file = Path(sys.argv[3])
    expected_file = Path.home() / ".config/systemd/user" / UNIT
    if unit_file != expected_file or not unit_file.parent.is_dir():
        raise RuntimeError("cannot address a non-owned CI unit path")
    cli = work / "runtime/bin/runner-mcp"
    if not cli.is_file() or cli.is_symlink():
        raise RuntimeError("fixed virtualenv launcher missing")

    previous_file = work / "systemd-previous.json"
    previous = json.loads(previous_file.read_text(encoding="utf-8")) if previous_file.exists() else None
    if previous is None:
        if unit_file.exists() or unit_file.is_symlink():
            raise RuntimeError("test unit already exists")
        port = _install_ci_fixture(work, unit_file, cli)
        action = "start"
    else:
        port = int((work / "systemd-port.txt").read_text(encoding="ascii"))
        if not 1024 < port < 65536:
            raise RuntimeError("invalid private CI port")
        current = _attest_unit(unit_file)
        if (
            current.get("ActiveState") != "active"
            or current.get("MainPID") != str(previous["pid"])
            or _start_ticks(previous["pid"]) != previous["ticks"]
            or _health(port) != (previous["version"], previous["instance"])
        ):
            raise RuntimeError("prior actual running generation must remain active")
        print("MCP_DISPOSABLE_SYSTEMD_OLD_LOADED_VERSION_PRESERVED=PASS")
        action = "restart"

    _attest_unit(unit_file)
    if version in ("0.1.88", "0.1.174"):
        # Beide historische baselines 0.1.88 en 0.1.174 missen de nieuwe user-busfix.
        # De bestaande systemd-user-manager mag in deze wegwerp-runner alleen
        # DEZE vaste testunit starten/herstarten; geen production fallback of
        # wijziging van de historische 0.1.174-broncode is toegestaan.
        legacy = subprocess.run(
            ["/usr/bin/systemctl", "--user", action, UNIT],
            env={"PATH": "/usr/bin:/bin",
                 "XDG_RUNTIME_DIR": f"/run/user/{os.geteuid()}"},
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=10, check=False,
        )
        if legacy.returncode != 0:
            raise RuntimeError("fixed disposable legacy systemd action failed")
        print("MCP_DISPOSABLE_SYSTEMD_LEGACY_TEST_ONLY_CONTROL=PASS")
    else:
        # Dit is de ECHTE, nieuwe 0.1.175-ServiceManager uit het geïnstalleerde
        # kandidaatwheel, met geregistreerde alias en operatorstop.
        manager = _manager(work, port)
        from runner_mcp.service_manager import ServiceManagerError, SystemdUserBackend

        try:
            actual = manager.action("ci", "server", action)
        except ServiceManagerError:
            snapshot = _read_unit()
            for key in ("LoadState", "ActiveState", "MainPID"):
                value = snapshot.get(key, "missing")
                if key == "MainPID":
                    value = "positive" if value.isdecimal() and int(value) > 0 else "zero_or_missing"
                print(f"MCP_DISPOSABLE_SYSTEMD_DIAG_{key.upper()}={value}", flush=True)
            try:
                SystemdUserBackend().status(UNIT)
            except ServiceManagerError:
                print("MCP_DISPOSABLE_SYSTEMD_DIAG_STATUS_READ=FAILED", flush=True)
            else:
                print("MCP_DISPOSABLE_SYSTEMD_DIAG_STATUS_READ=PASS", flush=True)
            raise
        if actual.get("action") != action or actual.get("service") != "server":
            raise RuntimeError("existing service manager did not execute registered action")
        print("MCP_DISPOSABLE_SYSTEMD_REGISTERED_MANAGER_ACTION=PASS")
    result = _new_generation(port, version, previous)
    if version == "0.1.175":
        safe = manager.status("ci", "server")
        if safe.get("active_state") != "active" or safe.get("health") != "healthy":
            raise RuntimeError("new service manager did not confirm real health")
    elif _read_unit().get("ActiveState") != "active":
        raise RuntimeError("legacy disposable systemd unit not active")
    if _read_unit().get("MainPID") != str(result["pid"]):
        raise RuntimeError("systemd main PID is unstable")
    previous_file.write_text(json.dumps(result), encoding="ascii")
    print(f"MCP_DISPOSABLE_SYSTEMD_SERVING_VERSION={version}")
    if previous:
        print("MCP_DISPOSABLE_SYSTEMD_FRESH_GENERATION=PASS")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        print(f"DISPOSABLE_SYSTEMD_STOP: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(2) from None
