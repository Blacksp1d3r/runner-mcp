"""Echte Runner-MCP-servicegeneratie bij een offline pip-upgrade in disposable CI.

De bestaande private setup en CLI starten per versie één werkelijke Uvicorn-
service op 127.0.0.1. De health-response bewijst de binnen dat proces geladen
versie en instance-ID. Het proces wordt gestopt en de listener gesloten vóór
de daaropvolgende pakkettransitie. Geen externe host of update-API is betrokken.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _private_ci_root(raw: str) -> Path:
    """Accepteer uitsluitend de eigen private Runner-Temp-werkmap."""
    if os.geteuid() == 0 or os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("alleen de niet-root disposable GitHub-runner is toegelaten")
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Python 3.12 is verplicht")
    base = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    work = Path(raw).resolve(strict=True)
    if work == base or base not in work.parents:
        raise RuntimeError("testwerkmap valt buiten RUNNER_TEMP")
    mode = work.stat().st_mode & 0o777
    if mode & 0o077:
        raise RuntimeError("testwerkmap heeft onveilige rechten")
    return work


def _fixed_private_configuration(work: Path) -> int:
    """Maak eenmaal een lokale CI-fixture met een eigen tijdelijk token."""
    config = work / "private-config"
    port_file = work / "serving-port.txt"
    if config.exists() != port_file.exists():
        raise RuntimeError("onvolledige bestaande testconfiguratie")
    if config.exists():
        port = int(port_file.read_text(encoding="ascii"))
        if not 1024 < port < 65536:
            raise RuntimeError("testpoort ongeldig")
        return port

    from runner_mcp.onboarding import SetupAnswers, install_private_configuration

    project = work / "fixture-project"
    project.mkdir(mode=0o700)
    (work / "test-home").mkdir(mode=0o700)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    install_private_configuration(
        config_dir=config,
        answers=SetupAnswers(
            resource_url=f"http://127.0.0.1:{port}/mcp",
            auth_issuer=f"http://127.0.0.1:{port}/",
            project_code="ci",
            project_name="Disposable CI",
            repository="example/ci",
            project_root=project,
        ),
    )
    port_file.write_text(str(port), encoding="ascii")
    return port


def _start_ticks(pid: int) -> int:
    """Lees de werkelijke Linux-starttijd uit /proc in plaats van alleen PID."""
    line = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii")
    end = line.rfind(") ")
    if end < 0:
        raise RuntimeError("ongeldige kernel-procesidentiteit")
    return int(line[end + 2 :].split()[19])


def _wait_healthy(proc: subprocess.Popen[bytes], port: int, expected: str) -> str:
    """Controleer de geladen versie uit de HTTP-header van DEZE servergeneratie."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("Runner-MCP-server stopte vóór gezonde health")
        try:
            with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                body = json.load(response)
                reported = response.headers.get("X-Runner-MCP-Loaded-Version")
                instance_id = response.headers.get("X-Runner-MCP-Instance-ID")
                if (
                    response.status != 200
                    or body != {"status": "ok"}
                    or reported != expected
                    or not isinstance(instance_id, str)
                    or re.fullmatch(r"[0-9a-f]{32}", instance_id) is None
                ):
                    raise RuntimeError("gezonde server meldt onjuiste geladen generatie")
                return instance_id
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            time.sleep(0.2)
    raise RuntimeError("echte Runner-MCP-server bereikte geen gezonde toestand")


def _socket_closed(port: int) -> bool:
    """Een oude luistersocket mag niet overblijven vóór de volgende start."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("0.1.88", "0.1.174", "0.1.175"):
        raise RuntimeError("alleen de twee vaste pakketversies zijn toegelaten")
    expected = sys.argv[1]
    work = _private_ci_root(sys.argv[2])
    if not (work / "runtime" / "bin" / "python").is_file():
        raise RuntimeError("gekwalificeerde Python-venv ontbreekt")

    cli = work / "runtime" / "bin" / "runner-mcp"
    if not cli.is_file() or cli.is_symlink():
        raise RuntimeError("echte geïnstalleerde Runner-MCP-CLI ontbreekt")
    config = work / "private-config"
    port = _fixed_private_configuration(work)
    if not _socket_closed(port):
        raise RuntimeError("testpoort is vooraf reeds bezet")

    previous_file = work / "previous-serving.json"
    previous = json.loads(previous_file.read_text(encoding="ascii")) if previous_file.exists() else None

    # Alleen de disposable CI-eigenaar start zijn eigen echte CLI; geen root,
    # shell, service-unit of private serverconfiguratie wordt aangesproken.
    child_env = {
        "HOME": str(work / "test-home"),
        "PATH": "/usr/bin:/bin",
        "PYTHONUNBUFFERED": "1",
        "NO_PROXY": "127.0.0.1,localhost",
        "RUNNER_MCP_CONFIG_DIR": str(config),
    }
    log_path = work / f"serving-{expected}.log"
    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            [
                str(cli), "--config-dir", str(config), "serve",
                "--host", "127.0.0.1", "--port", str(port),
                "--log-level", "warning",
            ],
            cwd=work,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            instance_id = _wait_healthy(proc, port, expected)
            ticks = _start_ticks(proc.pid)
            exe = Path("/proc") / str(proc.pid) / "exe"
            if not os.path.samefile(exe, sys.executable):
                raise RuntimeError("live server gebruikt verkeerde Python-interpreter")
            if previous is not None and (
                previous.get("pid") == proc.pid
                or previous.get("instance_id") == instance_id
                or previous.get("start_ticks") == ticks
            ):
                raise RuntimeError("oude servicegeneratie is niet vervangen")
            print(f"MCP_DISPOSABLE_SERVING_LOADED_VERSION={expected}")
            print("MCP_DISPOSABLE_SERVING_LOOPBACK_HEALTH=PASS")
            if previous is not None:
                print("MCP_DISPOSABLE_SERVING_NEW_KERNEL_GENERATION=PASS")
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
                raise RuntimeError("service beëindigde niet binnen de grens")
    if not _socket_closed(port):
        raise RuntimeError("oude Runner-MCP-listener blijft actief na stop")
    previous_file.write_text(
        json.dumps({"pid": proc.pid, "start_ticks": ticks, "instance_id": instance_id}),
        encoding="ascii",
    )
    print("MCP_DISPOSABLE_PREVIOUS_LISTENER_CLOSED=PASS")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"DISPOSABLE_SERVING_STOP: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
