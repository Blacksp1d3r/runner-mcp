# Managed autostart

Runner MCP can install its own fixed non-root autostart without exposing a general service-control interface.

The preferred backend is a systemd user manager. When a host has no usable user systemd bus, `--backend auto` falls back to a managed user crontab block that supervises the same fixed Runner MCP components once per minute.

This packaging is for a host where Runner MCP is already installed and its private configuration is valid.

## What gets installed

The command:

```bash
runner-mcp autostart install
```

selects the backend automatically:

- systemd user services when the user's systemd manager is available;
- otherwise a managed crontab block, when `crontab` is available.

You can force the choice locally with `--backend systemd` or `--backend cron`.

Both backends always supervise the loopback-only Runner MCP server. They also supervise the fixed GitHub mailbox watcher when the mailbox is configured and explicitly bootstrapped, and the fixed completion watcher when completion delivery is configured and explicitly bootstrapped.

Generated unit files or crontab entries live only in local user state. They may contain local executable/configuration paths, so that generated state must not be copied into the public repository.

No bearer token, GitHub token, database credential or project command is placed in the generated autostart configuration.

## Safety boundaries

Autostart does not create a generic systemd control surface.

It:

- manages only the fixed server, GitHub-watcher and completion-watcher components;
- binds the MCP server to `127.0.0.1`;
- uses fixed `systemctl --user` argument arrays on the systemd backend;
- uses a marked crontab block plus a local lock-protected `cron-run` helper on the cron backend;
- the cron helper executes only fixed Runner MCP argv arrays and does not accept a shell command;
- refuses to overwrite/delete foreign systemd units or silently absorb unmanaged Runner MCP cron entries;
- requires watcher bootstrap before enabling either watcher;
- keeps bootstrap/replay state unchanged;
- never enables sudo or system-level services;
- is available only through the local CLI, not through the GitHub mailbox.

Changing the local server port is an explicit local installation choice:

```bash
runner-mcp autostart install --port 8000
```

## Dedicated service-user hosts

When Runner MCP is installed under a dedicated service account, qualify the runtime as that account. Do not inspect or execute the service account's private virtual environment directly from a different operator account, and do not relax private home/configuration permissions merely to make that possible.

From an authorized local operator account, prefer the existing delegated operator launcher installed by `install-operator.sh`. For direct local diagnosis where that launcher is not yet available, use the host's normal account-switching policy and run the public CLI as the service user, for example:

```bash
sudo -iu SERVICE_USER runner-mcp status
sudo -iu SERVICE_USER runner-mcp doctor
sudo -iu SERVICE_USER runner-mcp autostart preflight
```

Use the literal local service-account name in place of `SERVICE_USER`; never copy credentials or private configuration into the operator account.

Apply a capability/version fence before activation:

1. `runner-mcp status` must identify the intended installed runtime and must not report `development` for a packaged persistent install.
2. `runner-mcp --help` / `runner-mcp autostart --help` must expose the expected command surface. If `autostart preflight` is absent, treat the runtime as stale and update/bootstrap it before continuing.
3. `runner-mcp doctor` must complete against the same service-user runtime.
4. Only then run `runner-mcp autostart preflight`.
5. A blocked preflight remains a hard activation gate; do not bypass it by installing autostart manually.

For repository diagnostic scripts, invoke them explicitly with `bash scripts/diagnostics/...` when appropriate instead of relying on executable-bit state after checkout. Run any private-runtime probe in the service-user context it is intended to qualify.

## Before installing

Run:

```bash
runner-mcp doctor
runner-mcp autostart preflight
```

`autostart preflight` is read-only. It executes the same fresh activation checks used immediately before installation and returns only a bounded readiness category. A blocked result does not create unit files, call the managed backend installer, or alter crontab state.

If you use the GitHub mailbox, configure and bootstrap it first:

```bash
runner-mcp github-mailbox status
runner-mcp github-watcher bootstrap
```

Bootstrap is intentionally explicit. Autostart will not move or create the watcher cursor on your behalf.

If you use completion notifications:

```bash
runner-mcp completion-notifier status
runner-mcp completion-watcher bootstrap
```

Again, autostart will not reinterpret historical completions.

## Install and inspect

Confirm the activation gate first:

```bash
runner-mcp autostart preflight
```

Only a clear result is eligible for installation. Then install and start the applicable managed services:

```bash
runner-mcp autostart install
```

Check only safe component state:

```bash
runner-mcp autostart status
```

Status reports only the selected backend and whether the server, GitHub watcher and completion watcher are installed, enabled and active. It does not print unit-file paths, crontab contents, private configuration paths or credentials.

## Remove

To remove only autostart state managed by Runner MCP:

```bash
runner-mcp autostart remove
```

The CLI requires the explicit local confirmation phrase shown on screen. Foreign unit files and unrelated crontab entries are never removed.

On the systemd backend, removal disables and stops the managed units. On the cron backend, removal deletes the managed schedule so no future restart occurs; it deliberately does not send a blind process-kill signal to a currently running component. Stop or reboot that local account explicitly when immediate termination is required. This conservative behavior avoids killing a process whose identity cannot be proven from cron state alone.

## Headless hosts

Some Linux installations do not expose a usable systemd user manager to the Runner MCP account. In `auto` mode Runner MCP now falls back to a managed user crontab instead of requiring a system-level policy change.

The cron backend starts each fixed component through a per-component private lock. A new cron tick exits immediately while the component already owns its lock; after a crash, the next minute can start it again.

If an existing unmanaged Runner MCP cron setup is detected, installation fails closed instead of creating duplicate supervisors. The operator must remove or migrate those old entries explicitly before the managed cron backend is installed.

Runner MCP deliberately does not change login/session, system-level services or host privilege policy automatically.
