from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import uvicorn

from .config_manager import (
    ConfigManagerError,
    add_project,
    add_service_config,
    add_test_profile,
    list_projects,
    list_service_configs,
    list_test_profiles,
    remove_project,
    remove_service_config,
    remove_test_profile,
)
from .onboarding import (
    OnboardingError,
    default_config_dir,
    disable_operator_stop,
    enable_operator_stop,
    install_private_configuration,
    operator_stop_status,
    prompt_setup_answers,
    read_private_runtime,
    run_doctor,
)
from .server import create_app


def package_version() -> str:
    try:
        return version("runner-mcp")
    except PackageNotFoundError:
        return "development"


def _config_dir(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else default_config_dir()


def cmd_setup(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)
    print("Runner MCP setup")
    print()
    print("This wizard creates private local configuration.")
    print("No server-specific values are written to the public Git repository.")
    print()

    answers = prompt_setup_answers()

    print()
    print("Rollback and recovery retention")
    print(f"  Minimum releases kept : {answers.min_releases_to_keep}")
    print(f"  Minimum release age   : {answers.min_release_age_days} days")
    print(f"  Database PITR         : {answers.pitr_retention_days} days")
    print(f"  Pre-migration backups : {answers.pre_migration_backup_days} days")
    print()
    confirmation = input("Type YES to accept these retention settings: ").strip()
    if confirmation != "YES":
        print("Setup cancelled. No configuration was written.")
        return 1

    paths = install_private_configuration(
        config_dir=config_dir,
        answers=answers,
        overwrite=args.overwrite,
        rotate_token=args.rotate_token,
    )

    print()
    print("Configuration created successfully.")
    print("  Private configuration : ready")
    print("  Emergency stop        : inactive")
    print("  Retention policy      : confirmed")
    print("  Test job storage      : ready")
    print(f"  Project               : {answers.project_code}")
    print()
    print("The generated bearer token was stored privately and was not displayed.")
    print("Next: run runner-mcp doctor.")
    if args.show_config_location:
        print(f"Private config location: {paths.config_dir}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)
    _, settings, registry = read_private_runtime(config_dir)
    _, guard = operator_stop_status(config_dir)
    status = guard.status()

    print(f"Runner MCP {package_version()}")
    print(f"Mode: {status.mode}")
    print("Emergency stop: " + ("ACTIVE" if status.stop_active else "inactive"))
    print(
        "Retention confirmed: "
        + ("yes" if settings.retention_confirmed else "no")
    )
    print(
        "Retention: "
        f"{settings.retention_policy.min_releases_to_keep} releases / "
        f"{settings.retention_policy.min_release_age_days} days minimum"
    )
    print(f"PITR retention: {settings.retention_policy.pitr_retention_days} days")
    print(
        "Pre-migration backups: "
        f"{settings.retention_policy.pre_migration_backup_days} days"
    )
    print(
        "Test execution: "
        + ("configured" if settings.test_jobs_root is not None else "not configured")
    )
    print(f"Projects: {len(registry.projects)}")
    for code in sorted(registry.projects):
        project = registry.projects[code]
        print(f"  - {code}: {project.display_name}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = run_doctor(_config_dir(args.config_dir))
    width = max((len(check.name) for check in checks), default=10)

    print("Runner MCP doctor")
    print()
    for check in checks:
        print(f"{check.status:4}  {check.name:<{width}}  {check.detail}")

    failed = sum(check.failed for check in checks)
    warned = sum(check.status == "WARN" for check in checks)
    print()
    if failed:
        print(f"Doctor found {failed} failing check(s) and {warned} warning(s).")
        return 2
    print(f"Doctor found no failures ({warned} warning(s)).")
    return 0


def cmd_emergency_stop(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.stop_action == "on":
        enable_operator_stop(config_dir)
        print("Emergency stop is ACTIVE.")
        print(
            "New operator actions are blocked; "
            "read-only and cancel operations remain available."
        )
        return 0

    if args.stop_action == "status":
        _, guard = operator_stop_status(config_dir)
        status = guard.status()
        print("ACTIVE" if status.stop_active else "inactive")
        return 0

    if args.stop_action == "off":
        print("Clearing the emergency stop re-enables operator actions.")
        confirmation = input("Type UNLOCK to continue: ").strip()
        disable_operator_stop(config_dir, confirmation=confirmation)
        print("Emergency stop is inactive.")
        return 0

    raise OnboardingError("Unknown emergency-stop action")


def cmd_project(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.project_action == "list":
        projects = list_projects(config_dir)
        for project in projects:
            print(f"{project['code']}: {project['name']} ({project['repository']})")
        return 0

    if args.project_action == "add":
        display_name = args.name or input("Project display name: ").strip()
        repository = args.repository or input("Git repository (owner/name): ").strip()
        root_value = args.root or input("Project folder: ").strip()
        if not display_name or not repository or not root_value:
            raise ConfigManagerError("Project name, repository and folder are required")

        result = add_project(
            config_dir,
            code=args.code,
            display_name=display_name,
            repository=repository,
            root=Path(root_value),
        )
        print(f"Project added: {result['code']} ({result['name']})")
        return 0

    if args.project_action == "remove":
        expected = f"REMOVE {args.code}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Project removal cancelled")
        remove_project(config_dir, code=args.code)
        print(f"Project removed: {args.code}")
        return 0

    raise ConfigManagerError("Unknown project action")


def cmd_test_profile(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.profile_action == "list":
        profiles = list_test_profiles(config_dir, project=args.project)
        if not profiles:
            print("No test profiles configured.")
            return 0
        for profile in profiles:
            print(
                f"{profile['name']}: timeout={profile['timeout_seconds']}s, "
                f"log_limit={profile['max_log_bytes']} bytes"
            )
        return 0

    if args.profile_action == "add":
        executable = Path(args.executable) if args.executable else None
        result = add_test_profile(
            config_dir,
            project=args.project,
            name=args.name,
            preset=args.preset,
            executable=executable,
            arguments=args.arg,
            cwd=args.cwd,
            timeout_seconds=args.timeout,
            max_log_bytes=args.max_log_bytes,
            env_passthrough=args.env,
        )
        print(
            f"Test profile added: {result['name']} "
            f"(timeout {result['timeout_seconds']}s)"
        )
        return 0

    if args.profile_action == "remove":
        expected = f"REMOVE {args.name}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Test-profile removal cancelled")
        remove_test_profile(
            config_dir,
            project=args.project,
            name=args.name,
        )
        print(f"Test profile removed: {args.name}")
        return 0

    raise ConfigManagerError("Unknown test-profile action")


def cmd_service_config(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.service_config_action == "list":
        services = list_service_configs(config_dir, project=args.project)
        if not services:
            print("No services configured.")
            return 0
        for service in services:
            allowed = [
                action
                for action, enabled in (
                    ("start", service["can_start"]),
                    ("stop", service["can_stop"]),
                    ("restart", service["can_restart"]),
                )
                if enabled
            ]
            actions = ",".join(allowed) if allowed else "read-only"
            health = "health-check" if service["health_check"] else "no-health-check"
            print(f"{service['name']}: {actions}, {health}")
        return 0

    if args.service_config_action == "add":
        result = add_service_config(
            config_dir,
            project=args.project,
            name=args.name,
            unit=args.unit,
            health_url=args.health_url,
            allow_start=args.allow_start,
            allow_stop=args.allow_stop,
            allow_restart=args.allow_restart,
        )
        print(f"Service alias added: {result['name']}")
        return 0

    if args.service_config_action == "remove":
        expected = f"REMOVE {args.name}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Service removal cancelled")
        remove_service_config(
            config_dir,
            project=args.project,
            name=args.name,
        )
        print(f"Service alias removed: {args.name}")
        return 0

    raise ConfigManagerError("Unknown service-config action")


def cmd_serve(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)
    _, settings, registry = read_private_runtime(config_dir)

    bind_host = args.host
    if bind_host not in {"127.0.0.1", "::1", "localhost"} and not args.allow_public_bind:
        raise OnboardingError(
            "Non-loopback bind requires --allow-public-bind; prefer a TLS reverse proxy"
        )

    app = create_app(settings=settings, registry=registry)
    uvicorn.run(
        app,
        host=bind_host,
        port=args.port,
        log_level=args.log_level,
        access_log=False,
        proxy_headers=False,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runner-mcp",
        description="Secure, self-hosted MCP operations runner.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
    )
    parser.add_argument(
        "--config-dir",
        help="Private configuration directory. Defaults to the user config directory.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser(
        "setup",
        help="Create private Runner MCP configuration interactively.",
    )
    setup.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing private configuration.",
    )
    setup.add_argument(
        "--show-config-location",
        action="store_true",
        help="Show the local private configuration path after setup.",
    )
    setup.add_argument(
        "--rotate-token",
        action="store_true",
        help="Generate a new bearer credential while overwriting configuration.",
    )
    setup.set_defaults(func=cmd_setup)

    status = subparsers.add_parser(
        "status",
        help="Show a safe summary of Runner MCP configuration and safety state.",
    )
    status.set_defaults(func=cmd_status)

    doctor = subparsers.add_parser(
        "doctor",
        help="Validate private configuration, permissions, projects and safety settings.",
    )
    doctor.set_defaults(func=cmd_doctor)

    stop = subparsers.add_parser(
        "emergency-stop",
        help="Activate, inspect or clear the operator emergency stop.",
    )
    stop.add_argument("stop_action", choices=("on", "status", "off"))
    stop.set_defaults(func=cmd_emergency_stop)

    project = subparsers.add_parser(
        "project",
        help="List, add or remove configured projects without editing YAML.",
    )
    project_sub = project.add_subparsers(dest="project_action", required=True)

    project_list = project_sub.add_parser("list", help="List configured projects.")
    project_list.set_defaults(func=cmd_project)

    project_add = project_sub.add_parser("add", help="Add a project.")
    project_add.add_argument("code")
    project_add.add_argument("--name")
    project_add.add_argument("--repository")
    project_add.add_argument("--root")
    project_add.set_defaults(func=cmd_project)

    project_remove = project_sub.add_parser("remove", help="Remove a project.")
    project_remove.add_argument("code")
    project_remove.set_defaults(func=cmd_project)

    profile = subparsers.add_parser(
        "test-profile",
        help="List, add or remove predefined test profiles.",
    )
    profile_sub = profile.add_subparsers(dest="profile_action", required=True)

    profile_list = profile_sub.add_parser("list", help="List safe test-profile summaries.")
    profile_list.add_argument("project")
    profile_list.set_defaults(func=cmd_test_profile)

    profile_add = profile_sub.add_parser("add", help="Add a predefined test profile.")
    profile_add.add_argument("project")
    profile_add.add_argument("name")
    profile_add.add_argument(
        "--preset",
        choices=("pytest", "ruff", "custom"),
        default="pytest",
    )
    profile_add.add_argument("--executable")
    profile_add.add_argument(
        "--arg",
        action="append",
        default=[],
        help="Additional literal argument. Repeat for multiple arguments.",
    )
    profile_add.add_argument("--cwd", default=".")
    profile_add.add_argument("--timeout", type=int, default=300)
    profile_add.add_argument("--max-log-bytes", type=int, default=2_000_000)
    profile_add.add_argument(
        "--env",
        action="append",
        default=[],
        help="Explicit environment variable name to pass through.",
    )
    profile_add.set_defaults(func=cmd_test_profile)

    profile_remove = profile_sub.add_parser("remove", help="Remove a test profile.")
    profile_remove.add_argument("project")
    profile_remove.add_argument("name")
    profile_remove.set_defaults(func=cmd_test_profile)

    service_config = subparsers.add_parser(
        "service-config",
        help="List, add or remove private service aliases.",
    )
    service_sub = service_config.add_subparsers(
        dest="service_config_action",
        required=True,
    )

    service_list = service_sub.add_parser("list", help="List safe service summaries.")
    service_list.add_argument("project")
    service_list.set_defaults(func=cmd_service_config)

    service_add = service_sub.add_parser("add", help="Add a private service alias.")
    service_add.add_argument("project")
    service_add.add_argument("name")
    service_add.add_argument("--unit", required=True)
    service_add.add_argument("--health-url")
    service_add.add_argument("--allow-start", action="store_true")
    service_add.add_argument("--allow-stop", action="store_true")
    service_add.add_argument("--allow-restart", action="store_true")
    service_add.set_defaults(func=cmd_service_config)

    service_remove = service_sub.add_parser("remove", help="Remove a service alias.")
    service_remove.add_argument("project")
    service_remove.add_argument("name")
    service_remove.set_defaults(func=cmd_service_config)

    serve = subparsers.add_parser(
        "serve",
        help="Run Runner MCP using the private local configuration.",
    )
    serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host. Loopback is the safe default.",
    )
    serve.add_argument(
        "--port",
        type=int,
        default=8000,
        choices=range(1, 65536),
        metavar="PORT",
    )
    serve.add_argument(
        "--allow-public-bind",
        action="store_true",
        help="Explicitly allow a non-loopback bind. TLS termination is still required.",
    )
    serve.add_argument(
        "--log-level",
        choices=("critical", "error", "warning", "info"),
        default="info",
    )
    serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OnboardingError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
