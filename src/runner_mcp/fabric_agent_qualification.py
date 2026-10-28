from __future__ import annotations

import os
import stat
from collections.abc import Callable
from pathlib import Path

from .agent_bus_worker import (
    _fixed_runner_fabric_executable,
    _valid_secret,
    _validate_agent_mcp_endpoint,
)
from .onboarding import load_env_file, read_private_runtime

_RESOURCE_URL_KEY = "RUNNER_FABRIC_AGENT_RESOURCE_URL"
_BEARER_TOKEN_KEY = "RUNNER_FABRIC_AGENT_BEARER_TOKEN"
_EXTERNAL_TARGET_CONFIG_KEY = "RUNNER_FABRIC_EXTERNAL_TARGET_CONFIG"
# One separately custodied, preauthorized ORIGINAL SQL relay issuer. The
# worker credential and the general Runner-MCP private environment MUST NOT
# accidentally enable a Control Center command publisher.
_AF585_ISSUER_FILE = "af585-control-issuer.env"
_AF585_ISSUER_KEYS = frozenset({
    "RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE",
    "RUNNER_FABRIC_CONTROL_RELAY_ORIGIN",
    "RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL",
})
_AF585_CANONICAL_ORIGIN = "https://staging.fiscero.com"
_KEYS = (_RESOURCE_URL_KEY, _BEARER_TOKEN_KEY)
_RUNNER_MCP_KEYS = (
    "RUNNER_FABRIC_RUNNER_MCP_ENDPOINT",
    "RUNNER_FABRIC_RUNNER_MCP_BEARER_TOKEN",
)
_A6_EXCLUSIVE_KEYS = (
    "RUNNER_FABRIC_UPDATE_JOURNAL_ROOT",
    "RUNNER_FABRIC_UPDATE_JOURNAL_STORAGE_DOMAIN",
    "RUNNER_FABRIC_UPDATE_TARGET_STORAGE_DOMAIN",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_ID",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_TARGET_SUBJECT",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_EXPECTED_REVISION",
    "RUNNER_FABRIC_SYNTHETIC_PROBE_INTERVAL_SECONDS",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_ROOT",
    "RUNNER_FABRIC_AGENT_BUS_EVIDENCE_REVISION",
)
_A6_KEYS = (*_A6_EXCLUSIVE_KEYS, *_RUNNER_MCP_KEYS)
_WORKER_QUALIFICATION_EXCLUSIVE_KEYS = (
    "RUNNER_FABRIC_WORKER_QUALIFICATION_WORKER_ID",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_GENERATION",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_NETWORK_PROFILE",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_CPU_UNITS",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_MEMORY_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_HARD_DISK_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_CPU_UNITS",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_SOFT_RESERVE_MEMORY_MIB",
    "RUNNER_FABRIC_WORKER_QUALIFICATION_POLICY_EXPIRES_AT",
)
_WORKER_QUALIFICATION_KEYS = (
    *_WORKER_QUALIFICATION_EXCLUSIVE_KEYS,
    *_RUNNER_MCP_KEYS,
)

# Fixed correct-host Q7 private configuration. Never inherit the ambient
# process environment or auto-enable Q7 on a legacy qualification agent.
_Q7_MODE_KEY = "RUNNER_FABRIC_AGENT_QUALIFICATION_MODE"
_Q7_MODE = "subscription-coding-q7-v1"
_Q7_KEYS = (
    "RUNNER_FABRIC_CODING_Q7_PROJECT_ID",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT",
    "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT",
    "RUNNER_FABRIC_CODING_Q7_WORKER_URL",
    "RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN",
)
_Q7_FIXED_VALUES = {
    "RUNNER_FABRIC_CODING_Q7_PROJECT_ID": "aifordable",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_PROVIDER": "github",
    "RUNNER_FABRIC_CODING_Q7_SOURCE_REPOSITORY": "Blacksp1d3r/AIfordable",
    "RUNNER_FABRIC_CODING_Q7_WORKER_URL": "http://127.0.0.1:8030/mcp",
}
_Q7_PATH_KEYS = (
    "RUNNER_FABRIC_CODING_Q7_SOURCE_CHECKOUT",
    "RUNNER_FABRIC_CODING_Q7_WORKSPACE_ROOT",
)


class FabricAgentQualificationError(RuntimeError):
    """Safe fixed Runner Fabric qualification-agent wrapper failure."""


def fabric_agent_qualification_configured(config_dir: Path) -> bool:
    """Return whether the private qualification-agent bridge is fully configured."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    present = tuple(bool(values.get(key, "").strip()) for key in _KEYS)
    if any(present) and not all(present):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is incomplete"
        )
    if not all(present):
        return False
    try:
        _validate_agent_mcp_endpoint(values[_RESOURCE_URL_KEY].strip())
    except RuntimeError as exc:
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is invalid"
        ) from exc
    if not _valid_secret(values[_BEARER_TOKEN_KEY]):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent configuration is invalid"
        )
    return True


def qualification_agent_environment_additions(
    config_dir: Path,
) -> dict[str, str]:
    """Return only fixed optional Fabric qualification bindings."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    additions: dict[str, str] = {}
    additions.update(_af585_private_issuer_additions(paths.config_dir))

    external_target_config = values.get(_EXTERNAL_TARGET_CONFIG_KEY, "").strip()
    if external_target_config:
        if (
            "\x00" in external_target_config
            or "\n" in external_target_config
            or "\r" in external_target_config
            or not Path(external_target_config).is_absolute()
        ):
            raise FabricAgentQualificationError(
                "Runner Fabric qualification agent configuration is invalid"
            )
        additions[_EXTERNAL_TARGET_CONFIG_KEY] = external_target_config

    a6_triggered = any(
        bool(values.get(key, "").strip()) for key in _A6_EXCLUSIVE_KEYS
    )
    if a6_triggered:
        if not all(bool(values.get(key, "").strip()) for key in _A6_KEYS):
            raise FabricAgentQualificationError(
                "Runner Fabric A6 qualification configuration is incomplete"
            )
        _forward_private_values(
            values,
            additions,
            _A6_KEYS,
            invalid_message="Runner Fabric A6 qualification configuration is invalid",
        )

    worker_triggered = any(
        bool(values.get(key, "").strip())
        for key in _WORKER_QUALIFICATION_EXCLUSIVE_KEYS
    )
    if worker_triggered:
        if not all(
            bool(values.get(key, "").strip())
            for key in _WORKER_QUALIFICATION_KEYS
        ):
            raise FabricAgentQualificationError(
                "Runner Fabric worker qualification configuration is incomplete"
            )
        _forward_private_values(
            values,
            additions,
            _WORKER_QUALIFICATION_KEYS,
            invalid_message=(
                "Runner Fabric worker qualification configuration is invalid"
            ),
        )
    # Build and validate a complete Q7 group BEFORE modifying the launch
    # environment. No token values are ever included in failure messages.
    additions.update(_q7_private_environment_additions(values, paths.config_dir))
    return additions


def _q7_staged_owner_file(config_dir: Path) -> Path | None:
    """Only the already staged SAME-OWNER Q7 leaf for default MCP config.

    A custom --config-dir never gains implicit access to another user's
    systemd or Fabric files. This merely locates an existing file; never
    creates, copies, chmods, or enables anything.
    """
    home_config = Path.home() / ".config"
    if config_dir != home_config / "runner-mcp":
        return None
    return (
        home_config / "systemd" / "user"
        / "runner-mcp-fabric-agent-qualification.service.d" / "q7-private.env"
    )


def _load_q7_staged_owner_file(path: Path) -> dict[str, str]:
    """Require same UID, safe ancestor directories, exact 0600 regular leaf."""
    invalid = "Runner Fabric Q7 qualification configuration is invalid"
    config_root = Path.home() / ".config"
    parents = (
        config_root,
        config_root / "systemd",
        config_root / "systemd" / "user",
        path.parent,
    )
    try:
        for directory in parents:
            info = directory.lstat()
            if (
                not stat.S_ISDIR(info.st_mode)
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o022
            ):
                raise FabricAgentQualificationError(invalid)
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
        ):
            raise FabricAgentQualificationError(invalid)
        staged = load_env_file(path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise FabricAgentQualificationError(invalid) from exc
    if set(staged) != {*_Q7_KEYS, _Q7_MODE_KEY}:
        raise FabricAgentQualificationError(invalid)
    return staged


def _q7_private_environment_additions(
    values: dict[str, str], config_dir: Path,
) -> dict[str, str]:
    """Forward the complete Q7 group, never a staged token automatically.

    A pre-existing same-owner q7-private.env can be consumed WITHOUT copying
    its bearer only when the default Runner-MCP private config explicitly
    opts in via the exact Q7 mode. Staging alone keeps legacy mode inactive.
    """
    invalid = "Runner Fabric Q7 qualification configuration is invalid"
    if any(
        key.startswith("RUNNER_FABRIC_CODING_Q7_") and key not in _Q7_KEYS
        for key in values
    ):
        raise FabricAgentQualificationError(invalid)
    q7_fields_present = any(key in values for key in _Q7_KEYS)
    if not q7_fields_present and values.get(_Q7_MODE_KEY) != _Q7_MODE:
        return {}

    staged_path = _q7_staged_owner_file(config_dir)
    staged_exists = False
    if staged_path is not None:
        try:
            staged_path.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise FabricAgentQualificationError(invalid) from exc
        else:
            staged_exists = True
    if staged_exists:
        # Never choose between two bearer sources by priority.
        if q7_fields_present:
            raise FabricAgentQualificationError(invalid)
        staged = _load_q7_staged_owner_file(staged_path)
        if staged[_Q7_MODE_KEY] != _Q7_MODE:
            raise FabricAgentQualificationError(invalid)
        values = staged

    if not all(values.get(key, "").strip() for key in _Q7_KEYS):
        raise FabricAgentQualificationError(
            "Runner Fabric Q7 qualification configuration is incomplete"
        )
    if _Q7_MODE_KEY in values and values[_Q7_MODE_KEY] != _Q7_MODE:
        raise FabricAgentQualificationError(invalid)
    if any(values[key] != expected for key, expected in _Q7_FIXED_VALUES.items()):
        raise FabricAgentQualificationError(invalid)
    if any(
        len(values[key]) > 4096
        or not Path(values[key]).is_absolute()
        or ".." in Path(values[key]).parts
        for key in _Q7_PATH_KEYS
    ):
        raise FabricAgentQualificationError(invalid)
    if not _valid_secret(values["RUNNER_FABRIC_CODING_Q7_WORKER_TOKEN"]):
        raise FabricAgentQualificationError(invalid)

    candidate: dict[str, str] = {}
    _forward_private_values(values, candidate, _Q7_KEYS, invalid_message=invalid)
    if _Q7_MODE_KEY in values:
        candidate[_Q7_MODE_KEY] = _Q7_MODE
    return candidate


def _af585_private_issuer_additions(config_dir: Path) -> dict[str, str]:
    """Forward only the existing original machine issuer's isolated 0600 file.

    This never creates, mints, or copies a credential. The optional file has
    one fixed owner-private location and a fixed HTTPS origin; an invalid
    present file aborts the existing agent instead of silently changing roles.
    """
    # Legacy qualification remains supported in the existing Runner-MCP config.
    # The ORIGINAL publisher may already custody its independent 0600 issuer
    # alongside that config, under the same owner's runner-fabric directory.
    # Accept this sibling ONLY for the owner's default Runner-MCP config root:
    # no arbitrary path setting, worker token, host alias or credential copy.
    paths = [config_dir / _AF585_ISSUER_FILE]
    home_config = Path.home() / ".config"
    if config_dir == home_config / "runner-mcp":
        issuer_dir = home_config / "runner-fabric"
        sibling = issuer_dir / _AF585_ISSUER_FILE
        try:
            sibling.lstat()
        except FileNotFoundError:
            # Optional issuer stays absent, even if this sibling directory
            # happens to be used for unrelated, non-private Fabric data.
            pass
        except OSError as exc:
            raise FabricAgentQualificationError(
                "Runner Fabric original issuer configuration is invalid"
            ) from exc
        else:
            try:
                directory = issuer_dir.lstat()
            except OSError as exc:
                raise FabricAgentQualificationError(
                    "Runner Fabric original issuer configuration is invalid"
                ) from exc
            if (
                not stat.S_ISDIR(directory.st_mode)
                or directory.st_uid != os.geteuid()
                or stat.S_IMODE(directory.st_mode) != 0o700
            ):
                raise FabricAgentQualificationError(
                    "Runner Fabric original issuer configuration is invalid"
                )
            paths.append(sibling)

    selected: Path | None = None
    for candidate in paths:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise FabricAgentQualificationError(
                "Runner Fabric original issuer configuration is invalid"
            ) from exc
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
            or selected is not None
        ):
            # Two competing publisher files must never be chosen by priority.
            raise FabricAgentQualificationError(
                "Runner Fabric original issuer configuration is invalid"
            )
        selected = candidate

    if selected is None:
        return {}
    path = selected

    try:
        values = load_env_file(path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise FabricAgentQualificationError(
            "Runner Fabric original issuer configuration is invalid"
        ) from exc
    if (
        set(values) != _AF585_ISSUER_KEYS
        or values["RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE"]
        != "machine_control_credential"
        or values["RUNNER_FABRIC_CONTROL_RELAY_ORIGIN"]
        != _AF585_CANONICAL_ORIGIN
        or not _valid_secret(values["RUNNER_FABRIC_CONTROL_RELAY_CREDENTIAL"])
    ):
        raise FabricAgentQualificationError(
            "Runner Fabric original issuer configuration is invalid"
        )
    return values


def _forward_private_values(
    values: dict[str, str],
    additions: dict[str, str],
    keys: tuple[str, ...],
    *,
    invalid_message: str,
) -> None:
    for key in keys:
        value = values[key]
        if "\x00" in value or "\n" in value or "\r" in value:
            raise FabricAgentQualificationError(invalid_message)
        additions[key] = value


def run_fabric_agent_qualification_process(
    config_dir: Path,
    *,
    execve: Callable[[str, list[str], dict[str, str]], object] = os.execve,
) -> int:
    """Exec only the fixed qualification-only Runner Fabric Agent MCP."""

    paths, _settings, _registry = read_private_runtime(config_dir)
    values = load_env_file(paths.env_file)
    if not fabric_agent_qualification_configured(paths.config_dir):
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent is not configured"
        )

    endpoint = values[_RESOURCE_URL_KEY].strip()
    token = values[_BEARER_TOKEN_KEY]
    additions = qualification_agent_environment_additions(paths.config_dir)
    executable = _fixed_runner_fabric_executable()
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        _RESOURCE_URL_KEY: endpoint,
        _BEARER_TOKEN_KEY: token,
    }
    environment.update(additions)

    try:
        execve(
            str(executable),
            [str(executable), "agent-serve-qualification"],
            environment,
        )
    except OSError as exc:
        raise FabricAgentQualificationError(
            "Runner Fabric qualification agent could not start"
        ) from exc
    return 0
