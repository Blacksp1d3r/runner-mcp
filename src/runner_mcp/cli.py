from __future__ import annotations

import argparse
import getpass
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import uvicorn

from .approval_manager import ApprovalError, ApprovalManager
from .autostart import (
    AutostartError,
    install_user_services,
    remove_user_services,
    user_service_status,
)
from .completion_delivery import (
    CompletionDeliveryError,
    CompletionNotifierRuntime,
    completion_notifier_status,
    configure_github_issue_notifier,
    remove_completion_notifier,
)
from .config_manager import (
    ConfigManagerError,
    add_database_config,
    add_deployment_config,
    add_migration_config,
    add_project,
    add_service_config,
    add_test_profile,
    configure_github_mailbox,
    configure_project_test_capacity,
    github_mailbox_config_status,
    list_database_configs,
    list_deployment_configs,
    list_project_adapters,
    list_projects,
    list_service_configs,
    list_test_profiles,
    project_capabilities,
    remove_database_config,
    remove_deployment_config,
    remove_github_mailbox,
    remove_migration_config,
    remove_project,
    remove_service_config,
    remove_test_profile,
)
from .github_runtime import (
    DEFAULT_HEARTBEAT_SECONDS,
    DEFAULT_POLL_SECONDS,
    GitHubWatcherRuntime,
)
from .onboarding import (
    OnboardingError,
    default_config_dir,
    disable_operator_stop,
    enable_operator_stop,
    install_private_configuration,
    load_env_file,
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


def cmd_guide(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)
    _, _, registry = read_private_runtime(config_dir)
    _, guard = operator_stop_status(config_dir)
    stop_active = guard.status().stop_active

    databases = {row["project"]: row for row in list_database_configs(config_dir)}
    deployments = {row["project"]: row for row in list_deployment_configs(config_dir)}

    print("Runner MCP guide")
    print()
    if stop_active:
        print("Emergency stop is ACTIVE; mutating actions are currently blocked.")
        print()

    print("Configured projects:")
    for code in sorted(registry.projects):
        project = registry.projects[code]
        profiles = list_test_profiles(config_dir, project=code)
        services = list_service_configs(config_dir, project=code)
        database = databases.get(code, {})
        deployment = deployments.get(code, {})

        print(f"- {code}: {project.display_name}")
        print(f"  adapter: {project.adapter}")

        if profiles:
            names = ", ".join(profile["name"] for profile in profiles)
            print(f"  test profiles: {names}")
        elif project.adapter == "python":
            print("  test profiles: not configured")
            print(f"    next: runner-mcp test-profile add {code} unit --preset auto")
        else:
            print("  test profiles: not configured")
            print(
                "    next: runner-mcp test-profile add "
                f"{code} NAME --preset custom --executable /absolute/path/to/tool"
            )

        if services:
            aliases = ", ".join(service["name"] for service in services)
            print(f"  staging services: {aliases}")
        else:
            print("  staging services: not configured (optional)")
            print(
                "    next: runner-mcp service-config add "
                f"{code} ALIAS --unit USER.service"
            )

        if database.get("configured"):
            migration_state = (
                "configured"
                if database.get("migrations_configured")
                else "not configured"
            )
            print(f"  PostgreSQL: configured; migrations: {migration_state}")
        else:
            print("  PostgreSQL: not configured (optional)")
            print(f"    next: runner-mcp database-config add {code}")

        if deployment.get("configured"):
            print("  staging deployment: configured")
        elif services:
            service_alias = services[0]["name"]
            print("  staging deployment: not configured (optional)")
            print(
                "    next: runner-mcp deployment-config add "
                f"{code} --release-root /private/path --service {service_alias}"
            )
        else:
            print("  staging deployment: not configured (optional)")

    print()
    print("Before serving: runner-mcp doctor")
    print("Start locally: runner-mcp serve")
    print(
        "High-risk migration/deploy/rollback actions require a short-lived "
        "approval that is approved locally."
    )
    print("More help: QUICKSTART.md and docs/USING_AND_EXTENDING.md")
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
            adapter = project.get("adapter", "generic")
            print(
                f"{project['code']}: {project['name']} "
                f"({project['repository']}), adapter={adapter}"
            )
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
            adapter=args.adapter,
        )
        print(f"Project added: {result['code']} ({result['name']})")
        return 0

    if args.project_action == "capacity":
        result = configure_project_test_capacity(
            config_dir,
            project=args.code,
            max_parallel_tests=args.max_parallel_tests,
            max_queued_tests=args.max_queued_tests,
        )
        print(
            f"Project test capacity updated: {result['project']} "
            f"(parallel={result['max_parallel_tests']}, "
            f"queued={result['max_queued_tests']})"
        )
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


def cmd_adapter(args: argparse.Namespace) -> int:
    if args.adapter_action == "list":
        for adapter in list_project_adapters():
            tests = ",".join(adapter["test_presets"]) or "none"
            migrations = ",".join(adapter["migration_presets"]) or "none"
            print(
                f"{adapter['id']}: {adapter['name']}; "
                f"tests={tests}; migrations={migrations}"
            )
        return 0

    if args.adapter_action == "inspect":
        result = project_capabilities(
            _config_dir(args.config_dir),
            project=args.project,
        )
        print(f"Project: {result['project']}")
        print(f"Adapter: {result['adapter']} ({result['adapter_name']})")
        print("Test presets: " + ", ".join(result["test_presets"]))
        print("Migration presets: " + ", ".join(result["migration_presets"]))
        inspection = result["inspection"]
        for key in sorted(inspection):
            print(f"{key}: {inspection[key]}")
        return 0

    raise ConfigManagerError("Unknown adapter action")


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
                f"log_limit={profile['max_log_bytes']} bytes, "
                f"parallel_safe={str(profile['parallel_safe']).lower()}"
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
            parallel_safe=args.parallel_safe,
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


def cmd_database_config(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.database_action == "list":
        rows = list_database_configs(config_dir)
        for row in rows:
            state = "configured" if row["configured"] else "not-configured"
            migrations = (
                "migrations" if row["migrations_configured"] else "no-migrations"
            )
            engine = row["engine"] or "-"
            print(f"{row['project']}: {state}, {engine}, {migrations}")
        return 0

    if args.database_action == "add":
        dsn = getpass.getpass("PostgreSQL connection string (hidden): ").strip()
        result = add_database_config(
            config_dir,
            project=args.project,
            dsn=dsn,
        )
        print(f"Database configured for {result['project']}; credential stored privately.")
        return 0

    if args.database_action == "remove":
        expected = f"REMOVE DATABASE {args.project}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Database removal cancelled")
        remove_database_config(config_dir, project=args.project)
        print(f"Database configuration removed: {args.project}")
        return 0

    raise ConfigManagerError("Unknown database-config action")


def cmd_migration_config(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.migration_action == "add":
        status_executable = (
            Path(args.status_executable) if args.status_executable else None
        )
        apply_executable = (
            Path(args.apply_executable) if args.apply_executable else None
        )
        result = add_migration_config(
            config_dir,
            project=args.project,
            preset=args.preset,
            dsn_target_env=args.dsn_target_env,
            status_executable=status_executable,
            status_arguments=args.status_arg,
            apply_executable=apply_executable,
            apply_arguments=args.apply_arg,
            cwd=args.cwd,
            timeout_seconds=args.timeout,
        )
        print(
            f"Migration profile configured for {result['project']} "
            f"({result['preset']})."
        )
        return 0

    if args.migration_action == "remove":
        expected = f"REMOVE MIGRATIONS {args.project}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Migration-profile removal cancelled")
        remove_migration_config(config_dir, project=args.project)
        print(f"Migration profile removed: {args.project}")
        return 0

    raise ConfigManagerError("Unknown migration-config action")


def cmd_deployment_config(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.deployment_action == "list":
        rows = list_deployment_configs(config_dir)
        for row in rows:
            state = "configured" if row["configured"] else "not-configured"
            tests = ",".join(row["required_tests"]) or "no-required-tests"
            migrations = "migrations" if row["run_migrations"] else "no-migrations"
            service = row["service"] or "-"
            print(f"{row['project']}: {state}, service={service}, {tests}, {migrations}")
        return 0

    if args.deployment_action == "add":
        result = add_deployment_config(
            config_dir,
            project=args.project,
            release_root=Path(args.release_root),
            service=args.service,
            required_tests=args.require_test,
            run_migrations=args.run_migrations,
            activation_timeout_seconds=args.activation_timeout,
        )
        print(f"Staging deployment configured for {result['project']}.")
        return 0

    if args.deployment_action == "remove":
        expected = f"REMOVE DEPLOYMENT {args.project}"
        confirmation = input(f"Type {expected} to continue: ").strip()
        if confirmation != expected:
            raise ConfigManagerError("Deployment configuration removal cancelled")
        remove_deployment_config(config_dir, project=args.project)
        print(
            f"Deployment configuration removed: {args.project}. "
            "Existing release data was preserved."
        )
        return 0

    raise ConfigManagerError("Unknown deployment-config action")


def _approval_manager(config_dir: Path) -> ApprovalManager:
    _, settings, _ = read_private_runtime(config_dir)
    if settings.approval_root is None:
        raise ApprovalError("Human approval storage is not configured")
    return ApprovalManager(
        root=settings.approval_root,
        ttl_seconds=settings.approval_ttl_seconds,
    )


def _print_approval(plan: dict) -> None:
    print(f"Approval: {plan['approval_id']}")
    print(f"Action: {plan['action']}")
    print(f"Project: {plan['project']}")
    print(f"State: {plan['state']}")
    print(f"Expires: {plan['expires_at']}")
    summary = plan.get("summary") or {}
    if summary:
        print("Summary:")
        for key in sorted(summary):
            print(f"  {key}: {summary[key]}")


def cmd_approval(args: argparse.Namespace) -> int:
    approvals = _approval_manager(_config_dir(args.config_dir))

    if args.approval_action == "list":
        plans = approvals.list_recent(limit=args.limit)
        if not plans:
            print("No approval plans found.")
            return 0
        for plan in plans:
            print(
                f"{plan['approval_id']}  {plan['state']}  "
                f"{plan['action']}  {plan['project']}  expires={plan['expires_at']}"
            )
        return 0

    if args.approval_action == "status":
        _print_approval(approvals.status(args.approval_id))
        return 0

    if args.approval_action == "approve":
        plan = approvals.status(args.approval_id)
        if plan["state"] != "pending":
            raise ApprovalError("Approval is not pending")
        _print_approval(plan)
        phrase = f"APPROVE {args.approval_id[:8]}"
        print()
        confirmation = input(f"Type {phrase} to approve this one action: ").strip()
        if confirmation != phrase:
            raise ApprovalError("Approval cancelled")
        approved = approvals.approve(args.approval_id)
        print(f"Approved until {approved['expires_at']}. This approval is single-use.")
        return 0

    raise ApprovalError("Unknown approval action")


def cmd_autostart(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.autostart_action == "status":
        for item in user_service_status():
            print(
                f"{item.component}: "
                f"installed={'yes' if item.installed else 'no'}, "
                f"enabled={'yes' if item.enabled else 'no'}, "
                f"active={'yes' if item.active else 'no'}"
            )
        return 0

    if args.autostart_action == "install":
        executable = (Path(sys.executable).parent / "runner-mcp").resolve()
        installed = install_user_services(
            config_dir,
            executable=executable,
            port=args.port,
        )
        print("Runner MCP user services installed and started.")
        for unit_name in installed:
            component = unit_name.removeprefix("runner-mcp-").removesuffix(".service")
            if unit_name == "runner-mcp.service":
                component = "server"
            print(f"  - {component}")
        print("No private configuration values were written to the public repository.")
        return 0

    if args.autostart_action == "remove":
        confirmation = input(
            "Type REMOVE RUNNER MCP AUTOSTART to continue: "
        ).strip()
        if confirmation != "REMOVE RUNNER MCP AUTOSTART":
            raise AutostartError("autostart removal cancelled")
        removed = remove_user_services()
        print(f"Removed {len(removed)} Runner MCP user service(s).")
        return 0

    raise AutostartError("unknown autostart action")


def cmd_completion_notifier(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.completion_notifier_action == "status":
        result = completion_notifier_status(config_dir)
        print("configured" if result["configured"] else "not configured")
        if result["configured"]:
            print("initialized" if result["initialized"] else "not initialized")
        return 0

    if args.completion_notifier_action == "configure":
        repository = args.repository or input(
            "Private GitHub notification repository (owner/name): "
        ).strip()
        if not repository:
            raise CompletionDeliveryError(
                "completion notification repository is required"
            )
        mention = args.mention
        if mention is None:
            entered = input(
                "GitHub login to mention for notification (optional): "
            ).strip()
            mention = entered or None
        if args.token_stdin:
            token = sys.stdin.readline(4098).strip()
        else:
            token = getpass.getpass("GitHub notification token: ").strip()
        if not token:
            raise CompletionDeliveryError(
                "completion notification GitHub token is required"
            )
        configure_github_issue_notifier(
            config_dir,
            repository=repository,
            issue_number=args.issue,
            mention=mention,
            token=token,
        )
        print("Completion notifier configured.")
        print("The token and destination were stored privately and were not displayed.")
        print("Next: runner-mcp completion-watcher bootstrap")
        return 0

    if args.completion_notifier_action == "remove":
        confirmation = input(
            "Type REMOVE COMPLETION NOTIFIER to continue: "
        ).strip()
        if confirmation != "REMOVE COMPLETION NOTIFIER":
            raise CompletionDeliveryError("completion notifier removal cancelled")
        remove_completion_notifier(config_dir)
        print("Completion notifier configuration removed.")
        return 0

    raise CompletionDeliveryError("unknown completion notifier action")


def cmd_completion_watcher(args: argparse.Namespace) -> int:
    runtime = CompletionNotifierRuntime.from_private_config(
        _config_dir(args.config_dir)
    )

    if args.completion_watcher_action == "bootstrap":
        runtime.bootstrap()
        print("Completion notifier initialized at the current time.")
        print("Historical test completions were not replayed.")
        return 0

    if args.completion_watcher_action == "once":
        outcome = runtime.run_once()
        print(
            "state="
            f"{'healthy' if outcome.healthy else 'degraded'} "
            f"discovered={outcome.discovered_events} "
            f"delivered={outcome.delivered_events} "
            f"reconciled={outcome.reconciled_events} "
            f"already_delivered={outcome.already_delivered_events} "
            f"failures={outcome.delivery_failures}"
        )
        return 0 if outcome.healthy else 2

    if args.completion_watcher_action == "run":
        print("Runner MCP completion watcher running.")
        try:
            runtime.run_forever(poll_seconds=args.poll_seconds)
        except KeyboardInterrupt:
            print("Runner MCP completion watcher stopped.")
            return 0

    raise CompletionDeliveryError("unknown completion watcher action")


def cmd_github_mailbox(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)

    if args.github_mailbox_action == "status":
        result = github_mailbox_config_status(config_dir)
        print("configured" if result["configured"] else "not configured")
        return 0

    if args.github_mailbox_action == "configure":
        repository = args.repository or input(
            "Private GitHub mailbox repository (owner/name): "
        ).strip()
        if not repository:
            raise ConfigManagerError("GitHub mailbox repository is required")
        if args.token_stdin:
            token = sys.stdin.readline(4098).strip()
        else:
            token = getpass.getpass("GitHub mailbox token: ").strip()
        if not token:
            raise ConfigManagerError("GitHub mailbox token is required")
        configure_github_mailbox(
            config_dir,
            repository=repository,
            request_ref=args.request_ref,
            result_ref=args.result_ref,
            token=token,
        )
        print("GitHub mailbox configured.")
        print("The token was stored privately and was not displayed.")
        return 0

    if args.github_mailbox_action == "remove":
        confirmation = input(
            "Type REMOVE GITHUB MAILBOX to continue: "
        ).strip()
        if confirmation != "REMOVE GITHUB MAILBOX":
            raise ConfigManagerError("GitHub mailbox removal cancelled")
        remove_github_mailbox(config_dir)
        print("GitHub mailbox configuration removed.")
        return 0

    raise ConfigManagerError("Unknown GitHub mailbox configuration action")


def cmd_github_watcher(args: argparse.Namespace) -> int:
    runtime = GitHubWatcherRuntime.from_private_config(
        _config_dir(args.config_dir)
    )

    if args.github_watcher_action == "bootstrap":
        runtime.bootstrap()
        print("GitHub watcher initialized at the current request head.")
        print("Historical mailbox requests were not replayed.")
        return 0

    if args.github_watcher_action == "once":
        outcome = runtime.run_once()
        print(
            "state="
            f"{outcome.state.value} "
            f"discovered={outcome.discovered_requests} "
            f"processed={outcome.processed_requests} "
            f"reconciled={outcome.reconciled_requests} "
            f"attention={outcome.recovery_attention}"
        )
        return 0 if outcome.state.value in {"idle", "processed"} else 2

    if args.github_watcher_action == "run":
        print("Runner MCP GitHub watcher running.")
        try:
            runtime.run_forever(
                poll_seconds=args.poll_seconds,
                heartbeat_seconds=args.heartbeat_seconds,
            )
        except KeyboardInterrupt:
            print("Runner MCP GitHub watcher stopped.")
            return 0

    raise RuntimeError("Unknown GitHub watcher action")


def cmd_serve(args: argparse.Namespace) -> int:
    config_dir = _config_dir(args.config_dir)
    paths, settings, registry = read_private_runtime(config_dir)
    secret_values = load_env_file(paths.env_file)

    bind_host = args.host
    if bind_host not in {"127.0.0.1", "::1", "localhost"} and not args.allow_public_bind:
        raise OnboardingError(
            "Non-loopback bind requires --allow-public-bind; prefer a TLS reverse proxy"
        )

    app = create_app(
        settings=settings,
        registry=registry,
        secret_values=secret_values,
    )
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

    guide = subparsers.add_parser(
        "guide",
        help="Show safe, project-aware next steps without exposing private values.",
    )
    guide.set_defaults(func=cmd_guide)

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
    project_add.add_argument(
        "--adapter",
        choices=("generic", "python"),
        default="generic",
    )
    project_add.set_defaults(func=cmd_project)

    project_capacity = project_sub.add_parser(
        "capacity",
        help="Set bounded per-project test concurrency and queue limits.",
    )
    project_capacity.add_argument("code")
    project_capacity.add_argument("--max-parallel-tests", type=int, required=True)
    project_capacity.add_argument("--max-queued-tests", type=int, default=16)
    project_capacity.set_defaults(func=cmd_project)

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
        choices=("auto", "pytest", "ruff", "custom"),
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
        "--parallel-safe",
        action="store_true",
        help="Allow this profile to overlap with other explicitly parallel-safe profiles.",
    )
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

    database = subparsers.add_parser(
        "database-config",
        help="Configure private PostgreSQL credentials without editing YAML.",
    )
    database_sub = database.add_subparsers(dest="database_action", required=True)
    database_list = database_sub.add_parser("list", help="List safe database summaries.")
    database_list.set_defaults(func=cmd_database_config)
    database_add = database_sub.add_parser("add", help="Add a private PostgreSQL connection.")
    database_add.add_argument("project")
    database_add.set_defaults(func=cmd_database_config)
    database_remove = database_sub.add_parser("remove", help="Remove a database configuration.")
    database_remove.add_argument("project")
    database_remove.set_defaults(func=cmd_database_config)

    migration = subparsers.add_parser(
        "migration-config",
        help="Configure fixed migration status/apply commands.",
    )
    migration_sub = migration.add_subparsers(dest="migration_action", required=True)
    migration_add = migration_sub.add_parser("add", help="Add a migration profile.")
    migration_add.add_argument("project")
    migration_add.add_argument("--preset", choices=("auto", "alembic", "custom"), default="auto")
    migration_add.add_argument("--dsn-target-env", default="DATABASE_URL")
    migration_add.add_argument("--status-executable")
    migration_add.add_argument("--status-arg", action="append", default=[])
    migration_add.add_argument("--apply-executable")
    migration_add.add_argument("--apply-arg", action="append", default=[])
    migration_add.add_argument("--cwd", default=".")
    migration_add.add_argument("--timeout", type=int, default=600)
    migration_add.set_defaults(func=cmd_migration_config)
    migration_remove = migration_sub.add_parser("remove", help="Remove a migration profile.")
    migration_remove.add_argument("project")
    migration_remove.set_defaults(func=cmd_migration_config)

    deployment = subparsers.add_parser(
        "deployment-config",
        help="Configure staging releases without editing YAML.",
    )
    deployment_sub = deployment.add_subparsers(
        dest="deployment_action",
        required=True,
    )
    deployment_list = deployment_sub.add_parser(
        "list",
        help="List safe staging deployment summaries.",
    )
    deployment_list.set_defaults(func=cmd_deployment_config)
    deployment_add = deployment_sub.add_parser(
        "add",
        help="Add a staging deployment configuration.",
    )
    deployment_add.add_argument("project")
    deployment_add.add_argument("--release-root", required=True)
    deployment_add.add_argument("--service", required=True)
    deployment_add.add_argument("--require-test", action="append", default=[])
    deployment_add.add_argument("--run-migrations", action="store_true")
    deployment_add.add_argument("--activation-timeout", type=int, default=60)
    deployment_add.set_defaults(func=cmd_deployment_config)
    deployment_remove = deployment_sub.add_parser(
        "remove",
        help="Remove deployment configuration without deleting releases.",
    )
    deployment_remove.add_argument("project")
    deployment_remove.set_defaults(func=cmd_deployment_config)

    adapter = subparsers.add_parser(
        "adapter",
        help="List built-in project adapters or inspect project capabilities.",
    )
    adapter_sub = adapter.add_subparsers(dest="adapter_action", required=True)
    adapter_list = adapter_sub.add_parser("list", help="List built-in adapters.")
    adapter_list.set_defaults(func=cmd_adapter)
    adapter_inspect = adapter_sub.add_parser(
        "inspect",
        help="Inspect safe adapter capabilities for one project.",
    )
    adapter_inspect.add_argument("project")
    adapter_inspect.set_defaults(func=cmd_adapter)

    approval = subparsers.add_parser(
        "approval",
        help="List, inspect or locally approve short-lived high-risk action plans.",
    )
    approval_sub = approval.add_subparsers(dest="approval_action", required=True)
    approval_list = approval_sub.add_parser("list", help="List recent approval plans.")
    approval_list.add_argument("--limit", type=int, default=20)
    approval_list.set_defaults(func=cmd_approval)
    approval_status = approval_sub.add_parser("status", help="Inspect one approval plan.")
    approval_status.add_argument("approval_id")
    approval_status.set_defaults(func=cmd_approval)
    approval_approve = approval_sub.add_parser(
        "approve",
        help="Approve one pending plan locally after explicit confirmation.",
    )
    approval_approve.add_argument("approval_id")
    approval_approve.set_defaults(func=cmd_approval)

    autostart = subparsers.add_parser(
        "autostart",
        help="Install, inspect or remove safe systemd user services.",
    )
    autostart_sub = autostart.add_subparsers(
        dest="autostart_action",
        required=True,
    )
    autostart_status = autostart_sub.add_parser(
        "status",
        help="Show safe Runner MCP user-service state.",
    )
    autostart_status.set_defaults(func=cmd_autostart)
    autostart_install = autostart_sub.add_parser(
        "install",
        help="Install and start managed loopback Runner MCP user services.",
    )
    autostart_install.add_argument(
        "--port",
        type=int,
        default=8000,
        choices=range(1, 65536),
        metavar="PORT",
    )
    autostart_install.set_defaults(func=cmd_autostart)
    autostart_remove = autostart_sub.add_parser(
        "remove",
        help="Stop and remove only user services managed by Runner MCP.",
    )
    autostart_remove.set_defaults(func=cmd_autostart)

    completion_notifier = subparsers.add_parser(
        "completion-notifier",
        help="Configure a private idempotent GitHub issue completion notifier.",
    )
    completion_notifier_sub = completion_notifier.add_subparsers(
        dest="completion_notifier_action",
        required=True,
    )
    completion_notifier_status_parser = completion_notifier_sub.add_parser(
        "status",
        help="Show whether completion notification is configured and initialized.",
    )
    completion_notifier_status_parser.set_defaults(func=cmd_completion_notifier)
    completion_notifier_configure = completion_notifier_sub.add_parser(
        "configure",
        help="Configure a private GitHub issue notification destination.",
    )
    completion_notifier_configure.add_argument("--repository")
    completion_notifier_configure.add_argument("--issue", type=int, required=True)
    completion_notifier_configure.add_argument("--mention")
    completion_notifier_configure.add_argument(
        "--token-stdin",
        action="store_true",
        help="Read the GitHub token from standard input instead of prompting.",
    )
    completion_notifier_configure.set_defaults(func=cmd_completion_notifier)
    completion_notifier_remove = completion_notifier_sub.add_parser(
        "remove",
        help="Remove completion notification destination configuration.",
    )
    completion_notifier_remove.set_defaults(func=cmd_completion_notifier)

    completion_watcher = subparsers.add_parser(
        "completion-watcher",
        help="Deliver terminal test completion notifications without rerunning tests.",
    )
    completion_watcher_sub = completion_watcher.add_subparsers(
        dest="completion_watcher_action",
        required=True,
    )
    completion_watcher_bootstrap = completion_watcher_sub.add_parser(
        "bootstrap",
        help="Ignore historical completions and notify only future terminal tests.",
    )
    completion_watcher_bootstrap.set_defaults(func=cmd_completion_watcher)
    completion_watcher_once = completion_watcher_sub.add_parser(
        "once",
        help="Process one completion-notification cycle.",
    )
    completion_watcher_once.set_defaults(func=cmd_completion_watcher)
    completion_watcher_run = completion_watcher_sub.add_parser(
        "run",
        help="Continuously watch terminal test jobs and deliver notifications.",
    )
    completion_watcher_run.add_argument(
        "--poll-seconds",
        type=float,
        default=5.0,
    )
    completion_watcher_run.set_defaults(func=cmd_completion_watcher)

    github_mailbox = subparsers.add_parser(
        "github-mailbox",
        help="Configure the private GitHub mailbox transport.",
    )
    github_mailbox_sub = github_mailbox.add_subparsers(
        dest="github_mailbox_action",
        required=True,
    )
    github_mailbox_status = github_mailbox_sub.add_parser(
        "status",
        help="Show whether the private GitHub mailbox is configured.",
    )
    github_mailbox_status.set_defaults(func=cmd_github_mailbox)
    github_mailbox_configure = github_mailbox_sub.add_parser(
        "configure",
        help="Configure the private GitHub mailbox without exposing its token.",
    )
    github_mailbox_configure.add_argument("--repository")
    github_mailbox_configure.add_argument(
        "--request-ref",
        default="runner-control",
    )
    github_mailbox_configure.add_argument(
        "--result-ref",
        default="runner-results",
    )
    github_mailbox_configure.add_argument(
        "--token-stdin",
        action="store_true",
        help="Read the GitHub token from standard input instead of prompting.",
    )
    github_mailbox_configure.set_defaults(func=cmd_github_mailbox)
    github_mailbox_remove = github_mailbox_sub.add_parser(
        "remove",
        help="Remove the private GitHub mailbox configuration.",
    )
    github_mailbox_remove.set_defaults(func=cmd_github_mailbox)

    github_watcher = subparsers.add_parser(
        "github-watcher",
        help="Run the private GitHub mailbox watcher.",
    )
    github_watcher_sub = github_watcher.add_subparsers(
        dest="github_watcher_action",
        required=True,
    )
    github_watcher_bootstrap = github_watcher_sub.add_parser(
        "bootstrap",
        help="Start after the current request head without replaying history.",
    )
    github_watcher_bootstrap.set_defaults(func=cmd_github_watcher)
    github_watcher_once = github_watcher_sub.add_parser(
        "once",
        help="Process one incremental mailbox cycle.",
    )
    github_watcher_once.set_defaults(func=cmd_github_watcher)
    github_watcher_run = github_watcher_sub.add_parser(
        "run",
        help="Continuously poll the mailbox with a slower heartbeat cadence.",
    )
    github_watcher_run.add_argument(
        "--poll-seconds",
        type=float,
        default=DEFAULT_POLL_SECONDS,
    )
    github_watcher_run.add_argument(
        "--heartbeat-seconds",
        type=float,
        default=DEFAULT_HEARTBEAT_SECONDS,
    )
    github_watcher_run.set_defaults(func=cmd_github_watcher)

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
