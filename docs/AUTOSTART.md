# Managed user-service autostart

Runner MCP can install its own fixed user-level systemd services without root and without exposing a general service-control interface.

This packaging is for a host where Runner MCP is already installed and its private configuration is valid.

## What gets installed

The command:

```bash
runner-mcp autostart install
```

always installs a loopback-only Runner MCP server service.

It also installs the fixed GitHub mailbox watcher when the mailbox is configured and explicitly bootstrapped, and the fixed completion watcher when completion delivery is configured and explicitly bootstrapped.

The generated service files live only in the local user's systemd configuration. They may contain local executable/configuration paths, so those generated files are private host state and must not be copied into the public repository.

No bearer token, GitHub token, database credential or project command is placed in the unit files.

## Safety boundaries

Autostart does not create a generic systemd control surface.

It:

- manages only the three fixed Runner MCP unit names;
- binds the MCP server to `127.0.0.1`;
- calls `systemctl --user` with fixed argument arrays and no shell;
- refuses to overwrite or delete an existing unit it did not create;
- requires watcher bootstrap before enabling either watcher;
- keeps bootstrap/replay state unchanged;
- never enables sudo or system-level services;
- is available only through the local CLI, not through the GitHub mailbox.

Changing the local server port is an explicit local installation choice:

```bash
runner-mcp autostart install --port 8000
```

## Before installing

Run:

```bash
runner-mcp doctor
```

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

Install and start the applicable managed services:

```bash
runner-mcp autostart install
```

Check only safe component state:

```bash
runner-mcp autostart status
```

Status reports only whether the server, GitHub watcher and completion watcher are installed, enabled and active. It does not print unit-file paths, private configuration paths or credentials.

## Remove

To stop and remove only unit files managed by Runner MCP:

```bash
runner-mcp autostart remove
```

The CLI requires the explicit local confirmation phrase shown on screen. Foreign unit files are never removed.

## Headless hosts

User services require a functioning systemd user manager. Some Linux installations stop the user manager after logout unless the administrator has configured the account for persistent user services.

Runner MCP deliberately does not change login/session or system-level policies automatically. If `autostart install` reports that the user manager is unavailable, configure the host's user-service lifecycle according to your Linux distribution or administrator policy, then retry.

This keeps host-level privilege decisions outside Runner MCP.
