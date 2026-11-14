from __future__ import annotations

import hashlib
import hmac
import os
import re
import shlex
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .agent_bus_worker import agent_bus_worker_configured
from .autostart_activation import AutostartActivationPermit, require_clear_autostart_permit
from .completion_delivery import completion_notifier_status
from .fabric_agent_qualification import fabric_agent_qualification_configured
from .fabric_live_overview import fabric_live_overview_configured
from .github_mailbox import GITHUB_MAILBOX_ENV_KEYS
from .github_watcher import GitHubWatcherCursorStore, GitHubWatcherError
from .onboarding import (
    TunnelRestartConfigState,
    inspect_tunnel_restart_config,
    load_env_file,
    read_private_runtime,
)
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

MANAGED_MARKER = "# Managed by Runner MCP autostart."
SERVER_UNIT = "runner-mcp.service"
TUNNEL_UNIT = "runner-mcp-tunnel.service"
TOPOLOGY_HEARTBEAT_UNIT = "runner-mcp-topology-heartbeat.service"
GITHUB_WATCHER_UNIT = "runner-mcp-github-watcher.service"
COMPLETION_WATCHER_UNIT = "runner-mcp-completion-watcher.service"
AGENT_BUS_WORKER_UNIT = "runner-mcp-agent-bus-worker.service"
FABRIC_AGENT_QUALIFICATION_UNIT = "runner-mcp-fabric-agent-qualification.service"
FABRIC_LIVE_OVERVIEW_UNIT = "runner-mcp-fabric-live-overview.service"
KNOWN_UNITS = (
    SERVER_UNIT,
    TUNNEL_UNIT,
    TOPOLOGY_HEARTBEAT_UNIT,
    GITHUB_WATCHER_UNIT,
    COMPLETION_WATCHER_UNIT,
    AGENT_BUS_WORKER_UNIT,
    FABRIC_AGENT_QUALIFICATION_UNIT,
    FABRIC_LIVE_OVERVIEW_UNIT,
)


class AutostartError(RuntimeError):
    """Safe user-service packaging failure without private command output."""


@dataclass(frozen=True, slots=True)
class QualificationOverrideSwapPlan:
    """Private in-memory bytes only; neither rollback nor activation authority."""

    original_sha256: str
    candidate_sha256: str
    candidate_override: bytes
    original_override: bytes
    change_scope: str = "one_fixed_execstart_executable"
    activation_authorized: bool = False
    rollback_verified: bool = False


def _fixed_runner_mcp_launcher(value: str) -> bool:
    """Constrain both executable names without resolving or touching the host."""

    return (
        type(value) is str
        and value.startswith("/")
        and len(value) <= 1024
        and not any(part in (".", "..") for part in value.split("/"))
        and re.fullmatch(
            r"/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*/bin/runner-mcp", value
        ) is not None
        and str(PurePosixPath(value)) == value
    )


def plan_qualification_override_swap(
    *,
    original_override: bytes,
    expected_original_sha256: str,
    original_launcher: str,
    candidate_launcher: str,
) -> QualificationOverrideSwapPlan:
    """Plan an exact one-line change to an already-approved private override.

    No filesystem access, systemctl, write, implicit release admission or
    watchdog. A7 must independently attest real owner, paths, runtime, retained
    original bytes, protected rollback and same-client ACK before applying.
    """
    invalid = "fixed qualification override plan is unqualified"
    if (
        type(original_override) is not bytes
        or not 0 < len(original_override) <= 8192
        or type(expected_original_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", expected_original_sha256) is None
        or not _fixed_runner_mcp_launcher(original_launcher)
        or not _fixed_runner_mcp_launcher(candidate_launcher)
        or original_launcher == candidate_launcher
    ):
        raise AutostartError(invalid)
    original_digest = hashlib.sha256(original_override).hexdigest()
    if not hmac.compare_digest(original_digest, expected_original_sha256):
        raise AutostartError(invalid)
    try:
        data = original_override.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise AutostartError(invalid) from exc
    if not data.endswith("\n") or "\r" in data or "\x00" in data:
        raise AutostartError(invalid)
    lines = data.splitlines(keepends=True)
    effective = [
        (i, line[:-1])
        for i, line in enumerate(lines)
        if line.strip() and not line.lstrip().startswith(("#", ";"))
    ]
    if (
        len(effective) != 3
        or effective[0][1] != "[Service]"
        or effective[1][1] != "ExecStart="
    ):
        raise AutostartError(invalid)
    index, command = effective[2]
    prefix = "ExecStart=" + original_launcher
    if not command.startswith(prefix + " "):
        raise AutostartError(invalid)
    tail = command[len(prefix):]
    if (
        re.fullmatch(
            r" --config-dir /[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*"
            r" fabric-agent-qualification run",
            tail,
        ) is None
    ):
        raise AutostartError(invalid)
    lines[index] = "ExecStart=" + candidate_launcher + tail + "\n"
    candidate_override = "".join(lines).encode("utf-8")
    if candidate_override == original_override:
        raise AutostartError(invalid)
    # The exact one-path transformation MUST reverse byte for byte, including
    # harmless original comments and whitespace; the caller retains custody.
    lines[index] = "ExecStart=" + original_launcher + tail + "\n"
    if "".join(lines).encode("utf-8") != original_override:
        raise AutostartError(invalid)
    return QualificationOverrideSwapPlan(
        original_sha256=original_digest,
        candidate_sha256=hashlib.sha256(candidate_override).hexdigest(),
        candidate_override=candidate_override,
        original_override=original_override,
    )


@dataclass(frozen=True, slots=True)
class AutostartStatus:
    component: str
    installed: bool
    enabled: bool
    active: bool

    def public_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "installed": self.installed,
            "enabled": self.enabled,
            "active": self.active,
        }


@dataclass(frozen=True, slots=True)
class AutostartMigrationPlan:
    """Bounded observation, never an activation permit or live provenance."""

    component: str
    state: str
    reason_code: str
    cron_installed: bool
    systemd_manager_reachable: bool
    systemd_units_absent: bool
    cutover_authorized: bool = False


def plan_cron_to_systemd(
    *,
    component: str,
    expected_hostname: str,
    expected_uid: int,
    observed_hostname: str,
    observed_uid: int,
    configured_components: tuple[str, ...],
    cron_managed: bool,
    cron_rows: tuple[object, ...],
    systemd_rows: tuple[AutostartStatus, ...],
    systemd_manager_reachable: bool,
) -> AutostartMigrationPlan:
    """Pure read-only decision from existing owner-local status observers.

    An exact source/host schedule is necessary, never sufficient to authorize
    cutover. Real process/wheel, boot, rollback and Fabric ACK require separate
    original-host qualification; this function intentionally cannot grant it.
    """
    from .cron_autostart import CRON_COMPONENTS

    if component not in CRON_COMPONENTS:
        raise AutostartError("unknown managed autostart component")

    cron_matches = [row for row in cron_rows if getattr(row, "component", None) == component]
    cron_ok = (
        cron_managed
        and component in configured_components
        and len(cron_matches) == 1
        and cron_matches[0].installed is True
        and cron_matches[0].enabled is True
        and len({getattr(row, "component", None) for row in cron_rows}) == len(cron_rows)
    )
    unit_names = [row.component for row in systemd_rows]
    units_absent = (
        len(systemd_rows) == len(KNOWN_UNITS)
        and len(set(unit_names)) == len(KNOWN_UNITS)
        and set(unit_names) == set(CRON_COMPONENTS)
        and all(
            row.installed is False and row.enabled is False and row.active is False
            for row in systemd_rows
        )
    )

    if (
        not expected_hostname
        or observed_hostname != expected_hostname
        or type(expected_uid) is not int
        or expected_uid <= 0
        or observed_uid != expected_uid
    ):
        state, reason = "WAIT", "host_or_uid_mismatch"
    elif not cron_ok:
        state, reason = "WAIT", "exact_owned_cron_role_unavailable"
    elif not units_absent:
        state, reason = "WAIT", "systemd_unit_conflict_or_unknown"
    elif not systemd_manager_reachable:
        state, reason = "WAIT", "systemd_user_manager_unreachable"
    else:
        state, reason = "PLAN_ONLY", "original_host_and_rollback_not_attested"
    return AutostartMigrationPlan(
        component=component,
        state=state,
        reason_code=reason,
        cron_installed=bool(cron_ok),
        systemd_manager_reachable=bool(systemd_manager_reachable),
        systemd_units_absent=bool(units_absent),
    )


def default_user_unit_dir() -> Path:
    return (Path.home() / ".config" / "systemd" / "user").resolve()


def _validate_executable(executable: Path) -> Path:
    try:
        resolved = executable.expanduser().resolve(strict=True)
    except OSError as exc:
        raise AutostartError("Runner MCP executable is unavailable") from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise AutostartError("Runner MCP executable is unavailable")
    return resolved


def _systemd_quote(value: str) -> str:
    if not value or any(char in value for char in "\r\n\x00"):
        raise AutostartError("autostart value contains unsupported characters")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _unit(
    *,
    description: str,
    executable: Path,
    config_dir: Path,
    arguments: tuple[str, ...],
    requires_server: bool,
) -> str:
    exec_parts = [
        _systemd_quote(str(executable)),
        "--config-dir",
        _systemd_quote(str(config_dir)),
        *(_systemd_quote(item) for item in arguments),
    ]
    dependency = ""
    if requires_server:
        dependency = (
            f"After=network-online.target {SERVER_UNIT}\n"
            f"Requires={SERVER_UNIT}\n"
        )
    else:
        dependency = "After=network-online.target\nWants=network-online.target\n"

    return (
        f"{MANAGED_MARKER}\n"
        "[Unit]\n"
        f"Description={description}\n"
        f"{dependency}"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={' '.join(exec_parts)}\n"
        "Restart=on-failure\n"
        "RestartSec=3\n"
        "NoNewPrivileges=true\n"
        "PrivateTmp=true\n"
        "\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def configured_autostart_components(config_dir: Path) -> tuple[str, ...]:
    config_dir = config_dir.expanduser().resolve()
    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)

    components = ["server"]
    tunnel_configured = (
        inspect_tunnel_restart_config(paths.config_dir)
        is TunnelRestartConfigState.COMPLETE
    )
    if tunnel_configured:
        components.append("tunnel")
    agent_bus_configured = agent_bus_worker_configured(config_dir)
    if tunnel_configured and agent_bus_configured:
        components.append("topology-heartbeat")
    mailbox_configured = all(
        values.get(key, "").strip() for key in GITHUB_MAILBOX_ENV_KEYS
    )
    if mailbox_configured:
        cursor = GitHubWatcherCursorStore(
            paths.config_dir / "github-mailbox-cursor.json"
        )
        try:
            cursor_head = cursor.read()
        except GitHubWatcherError as exc:
            raise AutostartError(
                "GitHub watcher bootstrap state is unavailable"
            ) from exc
        if cursor_head is None:
            raise AutostartError(
                "GitHub watcher is configured but not bootstrapped"
            )
        components.append("github-watcher")

    if fabric_agent_qualification_configured(config_dir):
        components.append("fabric-agent-qualification")
    if agent_bus_configured:
        components.append("agent-bus-worker")
    if fabric_live_overview_configured(config_dir):
        components.append("fabric-live-overview")

    notifier = completion_notifier_status(config_dir)
    if notifier["configured"]:
        if not notifier["initialized"]:
            raise AutostartError(
                "completion notifier is configured but not bootstrapped"
            )
        components.append("completion-watcher")
    return tuple(components)


def systemd_user_available(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    try:
        completed = _run_systemctl(
            ["show-environment"],
            runner=runner,
            check=False,
        )
    except AutostartError:
        return False
    return completed.returncode == 0


def has_managed_user_units(
    *,
    unit_dir: Path | None = None,
) -> bool:
    target = unit_dir or default_user_unit_dir()
    expanded = target.expanduser()
    if not expanded.exists():
        return False
    if expanded.is_symlink() or not expanded.is_dir():
        raise AutostartError("systemd user unit directory is unavailable")
    for unit_name in KNOWN_UNITS:
        path = expanded / unit_name
        if path.is_symlink():
            raise AutostartError("autostart unit path is unsafe")
        if not path.exists():
            continue
        if not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if content.startswith(MANAGED_MARKER + "\n"):
            return True
    return False


def render_user_units(
    *,
    config_dir: Path,
    executable: Path,
    port: int = 8000,
) -> dict[str, str]:
    if not 1 <= port <= 65535:
        raise AutostartError("autostart port must be between 1 and 65535")

    config_dir = config_dir.expanduser().resolve()
    executable = _validate_executable(executable)
    components = configured_autostart_components(config_dir)

    units = {
        SERVER_UNIT: _unit(
            description="Runner MCP loopback service",
            executable=executable,
            config_dir=config_dir,
            arguments=(
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ),
            requires_server=False,
        )
    }
    if "tunnel" in components:
        units[TUNNEL_UNIT] = _unit(
            description="Runner MCP Secure MCP Tunnel",
            executable=executable,
            config_dir=config_dir,
            arguments=("tunnel-run", "--port", str(port)),
            requires_server=True,
        )
    if "topology-heartbeat" in components:
        units[TOPOLOGY_HEARTBEAT_UNIT] = _unit(
            description="Runner MCP topology heartbeat",
            executable=executable,
            config_dir=config_dir,
            arguments=("topology-heartbeat", "run"),
            requires_server=True,
        )
    if "github-watcher" in components:
        units[GITHUB_WATCHER_UNIT] = _unit(
            description="Runner MCP GitHub mailbox watcher",
            executable=executable,
            config_dir=config_dir,
            arguments=("github-watcher", "run"),
            requires_server=True,
        )
    if "fabric-agent-qualification" in components:
        units[FABRIC_AGENT_QUALIFICATION_UNIT] = _unit(
            description="Runner Fabric qualification-only Agent MCP",
            executable=executable,
            config_dir=config_dir,
            arguments=("fabric-agent-qualification", "run"),
            requires_server=True,
        )
    if "agent-bus-worker" in components:
        units[AGENT_BUS_WORKER_UNIT] = _unit(
            description="Runner MCP AIfordable Agent Bus worker",
            executable=executable,
            config_dir=config_dir,
            arguments=("agent-bus-worker", "run"),
            requires_server=True,
        )
    if "fabric-live-overview" in components:
        units[FABRIC_LIVE_OVERVIEW_UNIT] = _unit(
            description="Runner Fabric read-only live overview",
            executable=executable,
            config_dir=config_dir,
            arguments=("fabric-live-overview", "run"),
            requires_server=True,
        )
    if "completion-watcher" in components:
        units[COMPLETION_WATCHER_UNIT] = _unit(
            description="Runner MCP completion watcher",
            executable=executable,
            config_dir=config_dir,
            arguments=("completion-watcher", "run"),
            requires_server=True,
        )
    return units



def render_inactive_cron_server_peer_unit(
    *,
    config_dir: Path,
    executable: Path,
    component: str,
    port: int = 8000,
) -> tuple[str, str]:
    """Maak één kandidaat-unit zonder bestaande cronserver mee te starten.

    Dit is uitsluitend een niet-activerende bronrenderer voor #866. De gewone
    installatie blijft de volledige systemd-grafiek met Requires=server eisen.
    De kandidaat bevat bewust GEEN [Install]-sectie en kan dus niet als normale
    automatisch ingeschakelde unit worden behandeld. In tegenstelling tot de
    gewone systemd-nevenunit voert deze kandidaat dezelfde 'autostart cron-run'
    uit als cron: de bestaande per-rol-flock blijft na execv overgeërfd.
    Bij lockbezetting eindigt de service zonder rolwerk of automatisch retry;
    de fysieke rolstatus, managerwissel en latere rollback blijven apart bewijs.
    """
    # Beperk het model tot bekende nevenrollen. De server zelf en de primaire
    # tunnel behoren aan een afzonderlijke fysieke cutover-/transportpoort.
    unit_name = f"runner-mcp-{component}.service"
    if component in ("server", "tunnel") or unit_name not in KNOWN_UNITS:
        raise AutostartError("unknown or control-path migration component")
    rendered = render_user_units(
        config_dir=config_dir, executable=executable, port=port,
    )
    ordinary = rendered.get(unit_name)
    if ordinary is None:
        raise AutostartError("requested migration component is not configured")

    # _unit() produceert deze vaste combinatie. Weigeren als de normale
    # renderer ooit verandert; niet stilzwijgend een Requires laten staan.
    original_dependency = (
        f"After=network-online.target {SERVER_UNIT}\n"
        f"Requires={SERVER_UNIT}\n"
    )
    install_suffix = "\n[Install]\nWantedBy=default.target\n"
    if ordinary.count(original_dependency) != 1 or not ordinary.endswith(install_suffix):
        raise AutostartError("expected original systemd dependency graph is unavailable")
    # Een gewone systemd-nevenunit omzeilt de flock van 'cron-run'. Gebruik
    # voor de INACTIEVE migratiekandidaat alleen het oorspronkelijke, vaste
    # argv-pad. Controleer eerst de volledige ExecStart-vorm; bij bronwijziging
    # stoppen we in plaats van stilzwijgend onbeschermde rollen te starten.
    direct_tail = f' {_systemd_quote(component)} {_systemd_quote("run")}\n'
    exec_lines = [
        line for line in ordinary.splitlines(keepends=True)
        if line.startswith("ExecStart=")
    ]
    if len(exec_lines) != 1 or not exec_lines[0].endswith(direct_tail):
        raise AutostartError("original peer launcher is not exact")
    guarded_exec = (
        exec_lines[0][:-len(direct_tail)]
        + f' {_systemd_quote("autostart")} {_systemd_quote("cron-run")}'
        + f' {_systemd_quote(component)}\n'
    )
    candidate = ordinary.replace(
        original_dependency,
        "After=network-online.target\nWants=network-online.target\n",
        1,
    ).removesuffix(install_suffix).replace(exec_lines[0], guarded_exec, 1)
    if candidate.count(guarded_exec) != 1:
        raise AutostartError("shared cron lock launcher is unavailable")
    if (
        f"Requires={SERVER_UNIT}" in candidate
        or f"After=network-online.target {SERVER_UNIT}" in candidate
        or "[Install]" in candidate
        or "WantedBy=default.target" in candidate
    ):
        raise AutostartError("inactive migration unit still requires control service")
    return unit_name, candidate



def render_boot_candidate_cron_peer_unit(
    *,
    config_dir: Path,
    executable: Path,
    component: str,
    port: int = 8000,
) -> tuple[str, str]:
    """Bereken een herstartbestendige nevenunit, zonder installatie of start.

    Alleen een apart bewezen M3-proces mag na cron-exclusiviteit, functionele
    ACK en onafhankelijke rollback deze bronbytes ooit activeren. De unit
    behoudt exact de bestaande cron-run/execv/flock-bescherming en verwijst
    niet naar de primaire Runner-MCP-server. Het enige verschil met de
    reeds geteste static-unit is een standaard default.target-installhaak.
    Dit is uitdrukkelijk GEEN productievergunning of geschreven unitbestand.
    """
    name, inactive = render_inactive_cron_server_peer_unit(
        config_dir=config_dir, executable=executable,
        component=component, port=port,
    )
    # De static renderer is de enige bron voor ExecStart en alle hardening.
    # Stop bij bronafwijking in plaats van een onbekende unit enablebaar te maken.
    if (
        not inactive.endswith("PrivateTmp=true\n")
        or "\n[Install]\n" in inactive
        or "WantedBy=default.target" in inactive
        or f"Requires={SERVER_UNIT}" in inactive
    ):
        raise AutostartError("boot candidate is not the exact locked static peer")
    candidate = inactive + "\n[Install]\nWantedBy=default.target\n"
    return name, candidate


@dataclass(frozen=True, slots=True)
class SinglePeerSystemdMigrationPreview:
    """Herstelbaar bronvoorstel, nooit een vergunning of transactiescript."""

    component: str
    original_crontab: str
    candidate_crontab: str
    rollback_crontab_sha256: str
    inactive_unit_name: str
    inactive_unit_contents: str
    # Exact dezelfde cron-flock-bron, met enkel de enablebare Install-haak.
    boot_unit_contents: str = ""
    cutover_authorized: bool = False


def plan_single_peer_systemd_migration(
    *,
    preflight: AutostartMigrationPlan,
    original_crontab: str,
    executable: Path,
    config_dir: Path,
    components: tuple[str, ...],
    component: str,
    port: int = 8000,
) -> SinglePeerSystemdMigrationPreview:
    """Koppel één cronuitsluiting aan één inactieve systemd-nevenunit.

    Deze samenstelling berekent uitsluitend bytes. De oorspronkelijke volledige
    crontab blijft het exacte rollbackobject. Zowel de bestaande read-only
    host/UID/manager-preflight als de oude cronrol en de nieuwe unit moeten
    eenduidig passen. Er is geen systemctl, crontab-write of procesactie.
    Tijdens de echte omschakeling zijn aparte PID/lock-, boot- en A7-proeven
    vereist; ook een perfect voorstel geeft nooit activeringsbevoegdheid.
    """
    from .cron_autostart import (
        CronAutostartError,
        plan_single_role_cron_exclusion,
    )

    expected = AutostartMigrationPlan(
        component=component,
        state="PLAN_ONLY",
        reason_code="original_host_and_rollback_not_attested",
        cron_installed=True,
        systemd_manager_reachable=True,
        systemd_units_absent=True,
    )
    if (
        type(preflight) is not AutostartMigrationPlan
        or preflight != expected
        or type(component) is not str
        or component in ("server", "tunnel")
    ):
        raise AutostartError("single-peer systemd preflight is not qualified")
    try:
        cron_plan = plan_single_role_cron_exclusion(
            original_crontab=original_crontab,
            executable=executable,
            config_dir=config_dir,
            components=components,
            component=component,
            port=port,
        )
    except CronAutostartError as exc:
        raise AutostartError("single-peer cron rollback is not qualified") from exc

    unit_name, unit_contents = render_inactive_cron_server_peer_unit(
        config_dir=config_dir,
        executable=executable,
        component=component,
        port=port,
    )
    # Bereken ook de reeds bewezen bootkandidaat; BEIDE blijven uitsluitend
    # geheugenbytes, zodat een installatie niet bij het plannen ontstaat.
    boot_name, boot_contents = render_boot_candidate_cron_peer_unit(
        config_dir=config_dir,
        executable=executable,
        component=component,
        port=port,
    )
    if (
        boot_name != unit_name
        or boot_contents != unit_contents + "\n[Install]\nWantedBy=default.target\n"
        or unit_name != f"runner-mcp-{component}.service"
        or not unit_contents.startswith(MANAGED_MARKER + "\n")
        or "Requires=" + SERVER_UNIT in unit_contents
        or "[Install]" in unit_contents
        or len([line for line in unit_contents.splitlines()
                if line.startswith("ExecStart=")]) != 1
        or not any(
            line.endswith(
                f' {_systemd_quote("autostart")} {_systemd_quote("cron-run")}'
                f' {_systemd_quote(component)}'
            )
            for line in unit_contents.splitlines()
            if line.startswith("ExecStart=")
        )
        or cron_plan.original_crontab == cron_plan.candidate_crontab
        or cron_plan.component != component
    ):
        raise AutostartError("single-peer systemd candidate is not isolated")
    # Enkel geheugenbytes: de unit mag zelfs uitgeschakeld NIET op de
    # bestaande managed systemd-user locatie worden geplaatst. Een beheerd
    # bestand daar kan de nog actieve cron-reconciler blokkeren.
    return SinglePeerSystemdMigrationPreview(
        component=component,
        original_crontab=cron_plan.original_crontab,
        candidate_crontab=cron_plan.candidate_crontab,
        rollback_crontab_sha256=hashlib.sha256(
            cron_plan.original_crontab.encode("utf-8")
        ).hexdigest(),
        inactive_unit_name=unit_name,
        inactive_unit_contents=unit_contents,
        boot_unit_contents=boot_contents,
    )


def _exact_single_role_cron_delta(
    preview: SinglePeerSystemdMigrationPreview,
) -> bool:
    """Controleer de ENIGE toegestane wijziging tussen beide cronbytes.

    Dit controleert de afleiding opnieuw uit het volledige originele blok:
    slechts één exact herkenbare, geselecteerde cron-run-regel mag verdwijnen.
    Alle andere regels, zelfs buiten het beheerde blok, zijn byte-identiek.
    De executable en config-directory van die regel moeten ook identiek zijn
    aan de ExecStart van de eerder gegenereerde lockende systemd-nevenunit.
    De validatie verricht geen host-I/O en is géén uitvoeringsbevoegdheid.
    """
    from .cron_autostart import CRON_BEGIN, CRON_COMPONENTS, CRON_END

    original = preview.original_crontab
    candidate = preview.candidate_crontab
    if (
        preview.component not in CRON_COMPONENTS
        or preview.component in ("server", "tunnel")
        or not original.endswith("\n")
        or not candidate.endswith("\n")
        or len(original) > 131072
        or "\r" in original + candidate
        or "\x00" in original + candidate
    ):
        return False
    lines = original.splitlines(keepends=True)
    begin, end = f"{CRON_BEGIN}\n", f"{CRON_END}\n"
    if lines.count(begin) != 1 or lines.count(end) != 1:
        return False
    first, last = lines.index(begin), lines.index(end)
    if first >= last:
        return False
    claims: list[tuple[int, list[str]]] = []
    for index in range(first + 1, last):
        line = lines[index]
        if not line.startswith("* * * * * "):
            continue
        try:
            tokens = shlex.split(line.rstrip("\n"))
        except ValueError:
            return False
        if len(tokens) >= 11 and tokens[8:11] == [
            "autostart", "cron-run", preview.component,
        ]:
            claims.append((index, tokens))
    if len(claims) != 1:
        return False
    index, tokens = claims[0]
    if (
        len(tokens) != 13
        or tokens[:5] != ["*"] * 5
        or not tokens[5].startswith("/")
        or tokens[6] != "--config-dir"
        or not tokens[7].startswith("/")
        or tokens[11:] != [">/dev/null", "2>&1"]
        or candidate != "".join((*lines[:index], *lines[index + 1 :]))
    ):
        return False
    expected_exec = (
        f"ExecStart={_systemd_quote(tokens[5])} --config-dir "
        f'{_systemd_quote(tokens[7])} "autostart" "cron-run" '
        f'{_systemd_quote(preview.component)}\n'
    )
    return expected_exec in preview.inactive_unit_contents


@dataclass(frozen=True, slots=True)
class SinglePeerMigrationCheckpoint:
    """Alleen-lezen oordeel over één M3-fase, NOOIT activeringsbevoegdheid."""

    phase: str
    consistent: bool
    reason_code: str
    next_action_authorized: bool = False


def assess_single_peer_migration_checkpoint(
    *,
    preview: SinglePeerSystemdMigrationPreview,
    phase: str,
    observed_crontab: str,
    observed_unit_contents: str | None,
    unit_enabled: bool,
    unit_active: bool,
    main_pid: int,
    role_lock_active: bool,
    new_function_ack: bool,
) -> SinglePeerMigrationCheckpoint:
    """Wijs een onjuiste stap vóór nieuwe cron-/systemd-mutaties af.

    Het oordeel gebruikt uitsluitend door de aanroeper verkregen observaties.
    Het voert GEEN crontab, systemctl, lock-/procesinspectie of bestandstoegang
    uit. Een PASS is alleen interne consistentie, niet een originele host-,
    wheel-/PID-, monitor-, ACK-custody- of A7-herstelattestatie. Een apart
    bevoegd operatorproces moet elke fysieke fase opnieuw bewijzen.
    """
    def wait(reason: str) -> SinglePeerMigrationCheckpoint:
        return SinglePeerMigrationCheckpoint(
            phase=phase if type(phase) is str else "UNKNOWN",
            consistent=False,
            reason_code=reason,
        )

    # Bescherm tegen een willekeurig verzonnen preview, ongeldige types en
    # unitbron die de verplichte cron-lock of Install-haak niet meer deelt.
    if (
        type(preview) is not SinglePeerSystemdMigrationPreview
        or preview.cutover_authorized is not False
        or type(preview.component) is not str
        or preview.component in ("server", "tunnel")
        or preview.inactive_unit_name != f"runner-mcp-{preview.component}.service"
        or type(preview.original_crontab) is not str
        or type(preview.candidate_crontab) is not str
        or type(preview.inactive_unit_contents) is not str
        or type(preview.boot_unit_contents) is not str
        or preview.boot_unit_contents != (
            preview.inactive_unit_contents + "\n[Install]\nWantedBy=default.target\n"
        )
        or not preview.inactive_unit_contents.startswith(MANAGED_MARKER + "\n")
        or preview.inactive_unit_contents.count("ExecStart=") != 1
        or f' "autostart" "cron-run" "{preview.component}"'
        not in preview.inactive_unit_contents
        or hashlib.sha256(preview.original_crontab.encode("utf-8")).hexdigest()
        != preview.rollback_crontab_sha256
        or preview.original_crontab == preview.candidate_crontab
        or not _exact_single_role_cron_delta(preview)
    ):
        return wait("preview_untrusted_or_drifted")

    if (
        type(observed_crontab) is not str
        or (observed_unit_contents is not None and type(observed_unit_contents) is not str)
        or type(unit_enabled) is not bool
        or type(unit_active) is not bool
        or type(main_pid) is not int
        or main_pid < 0
        or type(role_lock_active) is not bool
        or type(new_function_ack) is not bool
    ):
        return wait("observation_type_unqualified")

    # Alle versies van de preflight én de terugweg moeten hetzelfde volledige
    # crontabobject behouden: ook vreemde regels, spaties en lege regels.
    phase_states = {
        # phase: (cronvorm, unitvorm, enabled, active, positieve PID, lock, ACK)
        "before_exclusion": ("original", "absent", False, False, False, False, False),
        "ready_to_stage": ("candidate", "absent", False, False, False, False, False),
        "staged_inactive": ("candidate", "boot", False, False, False, False, False),
        "new_worker_ack": ("candidate", "boot", True, True, True, True, True),
        "rollback_ready": ("candidate", "absent", False, False, False, False, False),
        "rollback_confirmed": ("original", "absent", False, False, False, False, False),
    }
    if type(phase) is not str or phase not in phase_states:
        return wait("unknown_checkpoint_phase")
    cron_state, unit_state, enabled, active, has_pid, lock, ack = phase_states[phase]
    expected_cron = (
        preview.original_crontab if cron_state == "original"
        else preview.candidate_crontab
    )
    if observed_crontab != expected_cron:
        return wait("full_crontab_drift")
    expected_unit = preview.boot_unit_contents if unit_state == "boot" else None
    if observed_unit_contents != expected_unit:
        return wait("unit_source_drift")
    if unit_enabled != enabled or unit_active != active:
        return wait("supervisor_state_drift")
    if (main_pid > 0) != has_pid or role_lock_active != lock:
        return wait("worker_or_lock_drift")
    if new_function_ack != ack:
        return wait("functional_ack_unqualified")
    return SinglePeerMigrationCheckpoint(
        phase=phase,
        consistent=True,
        reason_code="checkpoint_consistent_not_authorized",
    )



@dataclass(frozen=True, slots=True)
class SinglePeerMixedBackendStatus:
    """Alleen-lezen M3-eigenaarschap; nooit een installer-/reconcilevergunning.

    Consistentie betekent uitsluitend dat de aangeleverde cron-/unitinventaris
    strookt met een eerder vastgelegd éénrolsbronvoorstel en fasecheckpoint.
    Het bewijst geen originele host, werkende taak, herstart of A7-herstel.
    """

    consistent: bool
    reason_code: str
    selected_systemd_role: str | None = None
    remaining_cron_roles: tuple[str, ...] = ()
    generic_reconcile_authorized: bool = False
    cutover_authorized: bool = False


def assess_single_peer_mixed_backend_status(
    *,
    preview: SinglePeerSystemdMigrationPreview,
    phase: str,
    observed_crontab: str,
    observed_unit_contents: str | None,
    unit_enabled: bool,
    unit_active: bool,
    main_pid: int,
    role_lock_active: bool,
    new_function_ack: bool,
    cron_rows: tuple[object, ...],
    systemd_rows: tuple[object, ...],
) -> SinglePeerMixedBackendStatus:
    """Controleer één systemd-peer naast de overige exact beheerde cronrollen.

    Hergebruik de bestaande volledige cron-/unitbron- en flockcheckpointcheck.
    Controleer aanvullend alle vaste rolclaims, niet alleen de geselecteerde
    rol. Deze functie leest geen host, crontab of filesystem en schrijft niets.
    De algemene install/reconcile/remove-actuatoren blijven expliciet verboden
    in mixed mode, ook na een intern consistent oordeel.
    """
    from .cron_autostart import (
        CRON_BEGIN,
        CRON_COMPONENTS,
        CRON_END,
        CronComponentStatus,
    )

    def wait(reason: str) -> SinglePeerMixedBackendStatus:
        return SinglePeerMixedBackendStatus(consistent=False, reason_code=reason)

    if phase not in ("staged_inactive", "new_worker_ack"):
        return wait("mixed_phase_not_observed")
    checkpoint = assess_single_peer_migration_checkpoint(
        preview=preview,
        phase=phase,
        observed_crontab=observed_crontab,
        observed_unit_contents=observed_unit_contents,
        unit_enabled=unit_enabled,
        unit_active=unit_active,
        main_pid=main_pid,
        role_lock_active=role_lock_active,
        new_function_ack=new_function_ack,
    )
    if not checkpoint.consistent:
        return wait(checkpoint.reason_code)

    # Het originele volledige cronblok is de enige rol-authority in dit
    # broncontract. Een los meegegeven rollenlijst zou vervalst kunnen zijn.
    original = preview.original_crontab.splitlines()
    if original.count(CRON_BEGIN) != 1 or original.count(CRON_END) != 1:
        return wait("original_managed_block_unqualified")
    first, last = original.index(CRON_BEGIN), original.index(CRON_END)
    if first >= last:
        return wait("original_managed_block_unqualified")
    roles: list[str] = []
    for line in original[first + 1:last]:
        if not line.startswith("* * * * * "):
            continue
        try:
            tokens = shlex.split(line)
        except ValueError:
            return wait("original_cron_role_unqualified")
        if (
            len(tokens) not in (13, 15)
            or tokens[:5] != ["*"] * 5
            or tokens[8:10] != ["autostart", "cron-run"]
            or tokens[10] not in CRON_COMPONENTS
            or tokens[-2:] != [">/dev/null", "2>&1"]
        ):
            return wait("original_cron_role_unqualified")
        roles.append(tokens[10])
    if (
        len(roles) < 2
        or len(roles) != len(set(roles))
        or preview.component not in roles
    ):
        return wait("original_cron_roles_unqualified")

    # Beide inventarissen zijn volledig: elke vaste rol moet exact één keer
    # voorkomen. Extra units, dubbele rolclaims of een verdwenen cronpeer
    # mogen niet worden verdoezeld door alleen positieve regels te filteren.
    expected = set(CRON_COMPONENTS)
    if type(cron_rows) is not tuple or type(systemd_rows) is not tuple:
        return wait("backend_inventory_type_unqualified")
    if (
        len(cron_rows) != len(expected)
        or len(systemd_rows) != len(expected)
        or any(type(row) is not CronComponentStatus for row in cron_rows)
        or any(type(row) is not AutostartStatus for row in systemd_rows)
    ):
        return wait("backend_inventory_unqualified")
    cron_by_role = {row.component: row for row in cron_rows}
    systemd_by_role = {row.component: row for row in systemd_rows}
    if set(cron_by_role) != expected or set(systemd_by_role) != expected:
        return wait("backend_role_claims_unqualified")

    remaining = tuple(role for role in roles if role != preview.component)
    for role in CRON_COMPONENTS:
        cron = cron_by_role[role]
        systemd = systemd_by_role[role]
        cron_expected = role in remaining
        systemd_expected = role == preview.component
        if (
            cron.installed is not cron_expected
            or cron.enabled is not cron_expected
            or (not cron_expected and cron.active is not False)
            or systemd.installed is not systemd_expected
            or (not systemd_expected and (systemd.enabled or systemd.active))
        ):
            return wait("mixed_supervisor_claims_conflict")
        if systemd_expected and (
            systemd.enabled is not unit_enabled
            or systemd.active is not unit_active
        ):
            return wait("mixed_peer_state_drift")

    return SinglePeerMixedBackendStatus(
        consistent=True,
        reason_code="mixed_source_consistent_not_authorized",
        selected_systemd_role=preview.component,
        remaining_cron_roles=remaining,
    )


def _safe_unit_dir(unit_dir: Path) -> Path:
    expanded = unit_dir.expanduser()
    # Installing must not traverse a symlinked parent to another unit tree.
    if any(parent.is_symlink() for parent in (expanded, *expanded.parents)):
        raise AutostartError("systemd user unit directory must not be a symlink")
    if expanded.exists() and expanded.is_symlink():
        raise AutostartError("systemd user unit directory must not be a symlink")
    try:
        expanded.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AutostartError("systemd user unit directory is unavailable") from exc
    if expanded.is_symlink() or not expanded.is_dir():
        raise AutostartError("systemd user unit directory is unavailable")
    try:
        return expanded.resolve(strict=True)
    except OSError as exc:
        raise AutostartError("systemd user unit directory is unavailable") from exc


def _write_managed_unit(path: Path, content: str) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not existing.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to replace a user service not managed by Runner MCP"
            )
    try:
        atomic_replace_private(path, content.encode("utf-8"))
    except PrivateAtomicWriteError as exc:
        raise AutostartError("autostart unit could not be written") from exc


def _run_systemctl(
    arguments: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = runner(
            ["systemctl", "--user", *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AutostartError("systemd user manager is unavailable") from exc
    if check and completed.returncode != 0:
        raise AutostartError("systemd user service operation failed")
    return completed


def install_user_services(
    config_dir: Path,
    *,
    executable: Path,
    port: int = 8000,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    activation_permit: AutostartActivationPermit | None = None,
) -> list[str]:
    try:
        require_clear_autostart_permit(activation_permit)
    except PermissionError as exc:
        raise AutostartError("autostart activation is blocked") from exc
    # Direct Python callers must not bypass the CLI's duplicate-supervisor
    # guard. This check reads the owner's crontab without changing it.
    from .cron_autostart import CronAutostartError, cron_available, has_managed_cron

    if cron_available():
        try:
            if has_managed_cron():
                raise AutostartError(
                    "managed cron autostart exists; refuse parallel systemd activation"
                )
        except CronAutostartError as exc:
            raise AutostartError("managed cron status is unavailable") from exc

    # Verify a user manager before touching service files.
    _run_systemctl(["show-environment"], runner=runner)
    units = render_user_units(
        config_dir=config_dir,
        executable=executable,
        port=port,
    )
    target = _safe_unit_dir(unit_dir or default_user_unit_dir())

    # A foreign or unsafe obsolete unit must be discovered BEFORE replacing
    # an existing managed server unit. Otherwise a denied installation leaves
    # partially rewritten files despite never reaching daemon-reload.
    for unit_name in KNOWN_UNITS:
        path = target / unit_name
        if path.is_symlink():
            raise AutostartError("autostart unit path is unsafe")
        if not path.exists():
            continue
        if not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not existing.startswith(MANAGED_MARKER + "\n"):
            operation = "replace" if unit_name in units else "remove"
            raise AutostartError(
                f"refusing to {operation} a user service not managed by Runner MCP"
            )

    for unit_name, content in units.items():
        _write_managed_unit(target / unit_name, content)

    # Remove obsolete optional units only if Runner MCP created them.
    for unit_name in KNOWN_UNITS:
        if unit_name in units:
            continue
        path = target / unit_name
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not existing.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to remove a user service not managed by Runner MCP"
            )
        _run_systemctl(["disable", "--now", unit_name], runner=runner, check=False)
        path.unlink()

    _run_systemctl(["daemon-reload"], runner=runner)
    ordered = [name for name in KNOWN_UNITS if name in units]
    _run_systemctl(["enable", "--now", *ordered], runner=runner)
    return ordered



def restart_managed_server_unit(
    *,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Handoff ONLY to the already installed, uniquely pinned server unit.

    The A7 supervisor must independently qualify recovery and own the
    restart marker; this helper never clears a marker or approves rollout.
    """
    root = (unit_dir or default_user_unit_dir()).expanduser()
    if any(parent.is_symlink() for parent in (root, *root.parents)):
        raise AutostartError("managed server unit directory is unsafe")
    path = root / SERVER_UNIT
    if not hasattr(os, "O_NOFOLLOW"):
        raise AutostartError("managed server unit nofollow support unavailable")
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or before.st_nlink != 1
            or before.st_mode & 0o022
            or not 0 < before.st_size <= 16_384
        ):
            raise AutostartError("managed server unit identity unavailable")
        with os.fdopen(
            os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb",
        ) as stream:
            opened = os.fstat(stream.fileno())
            data = stream.read(16_385)
            after = os.fstat(stream.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise AutostartError("managed server unit readback unavailable") from exc
    def identity(meta: os.stat_result) -> tuple[int, ...]:
        return (
            meta.st_dev, meta.st_ino, meta.st_mode, meta.st_uid,
            meta.st_gid, meta.st_nlink, meta.st_size,
            meta.st_mtime_ns, meta.st_ctime_ns,
        )
    if (
        identity(before) != identity(opened)
        or identity(before) != identity(after)
        or identity(before) != identity(path_after)
        or len(data) != before.st_size
        or not data.startswith((MANAGED_MARKER + "\n").encode("utf-8"))
    ):
        raise AutostartError("managed server unit changed or foreign")
    _run_systemctl(["restart", SERVER_UNIT], runner=runner)


def user_service_status(
    *,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[AutostartStatus]:
    # A read-only status/dry-run must not create a systemd unit directory.
    # _safe_unit_dir() is reserved for the explicit install/remove paths.
    target = (unit_dir or default_user_unit_dir()).expanduser()
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise AutostartError("systemd user unit directory is unavailable")
    results: list[AutostartStatus] = []
    names = (
        ("server", SERVER_UNIT),
        ("tunnel", TUNNEL_UNIT),
        ("topology-heartbeat", TOPOLOGY_HEARTBEAT_UNIT),
        ("github-watcher", GITHUB_WATCHER_UNIT),
        ("completion-watcher", COMPLETION_WATCHER_UNIT),
        ("agent-bus-worker", AGENT_BUS_WORKER_UNIT),
        ("fabric-agent-qualification", FABRIC_AGENT_QUALIFICATION_UNIT),
        ("fabric-live-overview", FABRIC_LIVE_OVERVIEW_UNIT),
    )
    # Installed unit files do not prove that the caller can reach the user's
    # systemd manager. In particular, `sudo -iu <service-user>` can omit
    # XDG_RUNTIME_DIR / the user session bus. Without this guard, a failed
    # `systemctl --user is-active` silently becomes `active=no` for every
    # service, even while the real systemd units are healthy.
    if any((target / unit_name).exists() for _, unit_name in names):
        manager = _run_systemctl(
            ["show-environment"],
            runner=runner,
            check=False,
        )
        if manager.returncode != 0:
            raise AutostartError(
                "systemd user manager is unreachable from this session; "
                "check XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS"
            )
    for component, unit_name in names:
        path = target / unit_name
        # A dangling symlink does not .exist(), but is still an unsafe
        # installed unit claim for a migration plan or status observer.
        if path.is_symlink():
            raise AutostartError("autostart unit path is unsafe")
        installed = path.exists() and path.is_file()
        enabled = False
        active = False
        if installed:
            enabled = (
                _run_systemctl(
                    ["is-enabled", unit_name],
                    runner=runner,
                    check=False,
                ).returncode
                == 0
            )
            active = (
                _run_systemctl(
                    ["is-active", unit_name],
                    runner=runner,
                    check=False,
                ).returncode
                == 0
            )
        results.append(
            AutostartStatus(
                component=component,
                installed=installed,
                enabled=enabled,
                active=active,
            )
        )
    return results


def remove_user_services(
    *,
    unit_dir: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[str]:
    # Removal is a no-op when no owner unit directory exists. Never create it.
    target = (unit_dir or default_user_unit_dir()).expanduser()
    # Do not follow a symlinked ancestor to an unrelated unit directory.
    # Removal must not modify directories outside the original owner tree.
    if any(parent.is_symlink() for parent in (target, *target.parents)):
        raise AutostartError("systemd user unit directory is unavailable")
    if target.exists() and not target.is_dir():
        raise AutostartError("systemd user unit directory is unavailable")
    if not target.exists():
        return []
    _run_systemctl(["show-environment"], runner=runner)
    # Validate every known target before disabling or removing any unit.
    # An unsafe later peer must not leave a partially removed service set.
    for unit_name in KNOWN_UNITS:
        path = target / unit_name
        if path.is_symlink():
            raise AutostartError("autostart unit path is unsafe")
        if not path.exists():
            continue
        if not path.is_file():
            raise AutostartError("autostart unit path is unsafe")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AutostartError("autostart unit could not be inspected") from exc
        if not content.startswith(MANAGED_MARKER + "\n"):
            raise AutostartError(
                "refusing to remove a user service not managed by Runner MCP"
            )
    removed: list[str] = []
    for unit_name in KNOWN_UNITS:
        path = target / unit_name
        if not path.exists():
            continue
        _run_systemctl(["disable", "--now", unit_name], runner=runner)
        try:
            path.unlink()
        except OSError as exc:
            raise AutostartError("autostart unit could not be removed") from exc
        removed.append(unit_name)
    _run_systemctl(["daemon-reload"], runner=runner)
    return removed
