# Runner MCP Quickstart

This guide is for people who want to use Runner MCP without reading the Python source code.

Runner MCP gives an AI client a limited, auditable interface to your own development or staging environment. It is intentionally not a general remote shell.

## What you need

- a Linux machine you control;
- Python 3.12 or newer;
- Git;
- one existing project folder;
- the Git repository name for that project in `owner/name` form.

You do not need to know Python to complete the basic setup.

## 1. Get Runner MCP

Clone this repository and enter the folder:

```bash
git clone https://github.com/Blacksp1d3r/runner-mcp.git
cd runner-mcp
```

## 2. Install it

Run:

```bash
./install.sh
```

The installer uses a private Python virtual environment under your user account. It does not require root access.

If your shell cannot find `runner-mcp` afterwards, add your user-local bin directory to `PATH`.

## 3. Run the setup wizard

Run:

```bash
runner-mcp setup
```

The wizard first asks for a setup mode.

### Local mode

Choose `local` when you are evaluating Runner MCP on the same machine.

Runner MCP automatically uses a loopback-only MCP URL. You do not need to configure public DNS or TLS yet.

### Public mode

Choose `public` only when you already have an HTTPS endpoint and understand the reverse-proxy requirements.

The public endpoint must use HTTPS. Real hostnames, private server paths and credentials belong only in your private runtime configuration and must never be committed to this repository.

## 4. Choose rollback retention

The wizard asks how much history you want to protect.

The proposed defaults are:

- keep at least 20 code releases;
- keep code releases for at least 90 days;
- keep PostgreSQL point-in-time recovery history for 30 days;
- keep pre-migration backups for 180 days.

A release may be cleaned up only after both the minimum-count and minimum-age rules allow it.

The wizard requires explicit confirmation before future operator actions can be enabled.

## 5. Add the first project

The wizard asks for:

- a short project code;
- a display name;
- the Git repository in `owner/name` form;
- the existing project folder on your machine.

Those values are stored only in your private local configuration.

The generated bearer credential is stored privately and is not printed to the terminal. Re-running setup with `--overwrite` keeps the existing credential by default. Use `--rotate-token` only when you intentionally want a new credential.

### Add more projects later

List projects:

```bash
runner-mcp project list
```

Add another project without editing YAML:

```bash
runner-mcp project add second --name "Second Project" --repository owner/repository --root /path/to/project
```

The real project path is stored only in the private configuration. Normal list/status output does not print it.

### Add a test profile

For a Python project with a `.venv` or `venv` folder, Runner MCP can detect the project Python executable and create a pytest profile:

```bash
runner-mcp test-profile add myproject unit --preset pytest
```

For Ruff:

```bash
runner-mcp test-profile add myproject lint --preset ruff
```

List the safe profile summaries:

```bash
runner-mcp test-profile list myproject
```

Executable paths and argument arrays remain private and are not shown in the normal list output. Custom profiles are available for advanced setups.

### Add a staging service alias

Runner MCP currently supports allow-listed `systemd --user` services. System-level services and generic sudo execution are deliberately not enabled.

Add a read-only alias first:

```bash
runner-mcp service-config add myproject web --unit my-staging.service
```

To allow only restart:

```bash
runner-mcp service-config add myproject web --unit my-staging.service --allow-restart
```

`start`, `stop` and `restart` permissions are separate and default to off. Normal list and MCP output show only the alias, never the private unit name.

### Configure a PostgreSQL database

List database configuration status:

```bash
runner-mcp database-config list
```

Add the PostgreSQL connection for a project:

```bash
runner-mcp database-config add myproject
```

Runner MCP asks for the connection string using a hidden prompt. Do not put a database password on the command line. The credential is stored only in the private runtime file and is not written to project YAML.

The setup-created database-backup directory is private. Backups themselves are never returned through MCP; only safe metadata is returned.

### Configure migrations

For an Alembic project with a project-local `.venv/bin/alembic` or `venv/bin/alembic`:

```bash
runner-mcp migration-config add myproject --preset alembic
```

A custom profile is also possible, but it still uses fixed executables and literal argument arrays rather than a shell command string.

Before Runner MCP applies a migration, it creates a PostgreSQL pre-migration backup and checks the emergency stop again. A failed migration does not trigger an automatic database restore.

Database restore and PostgreSQL PITR/WAL orchestration are not implemented yet.

## 6. Verify the installation

Run:

```bash
runner-mcp doctor
```

A healthy basic setup should report no failing checks.

Then run:

```bash
runner-mcp status
```

The status output intentionally does not print private project paths or credentials.

## 7. Test the emergency stop

Activate it:

```bash
runner-mcp emergency-stop on
```

Check it:

```bash
runner-mcp emergency-stop status
```

While the emergency stop is active, new operator actions are blocked. Read-only inspection and cancellation remain available.

To clear it:

```bash
runner-mcp emergency-stop off
```

Runner MCP requires you to type `UNLOCK` before operator actions can resume.

## 8. Start Runner MCP locally

For a local evaluation:

```bash
runner-mcp serve
```

The safe default is loopback-only. Runner MCP refuses a public bind unless you explicitly override that protection.

For internet-facing use, put Runner MCP behind a properly configured HTTPS reverse proxy. Public deployment packaging is still being hardened and should be treated as an advanced setup for now.

## Controlled tests

Runner MCP can run tests only through predefined test profiles.

An AI client can select a project and a profile name. It cannot submit an arbitrary shell command.

Profiles define:

- the exact executable;
- exact arguments;
- working directory;
- timeout;
- maximum log size;
- explicitly allowed environment variables.

Test jobs support status checks, paged scrubbed logs, cancellation, timeouts and the external emergency stop.

Do not run untrusted public-fork code on a privileged persistent runner. Running tests still executes project code with the permissions of the Runner MCP operating-system account.

## What is not one-click yet

The following areas are still being built:

- service installation and automatic startup;
- staging service management;
- database backup and migration workflows;
- staging deploys;
- release rollback;
- a guided public HTTPS/reverse-proxy setup;
- optional graphical administration.

Until those phases are complete, Runner MCP should be considered an actively developed staging/development operations tool rather than a finished production appliance.

## Where to look when something is wrong

Run:

```bash
runner-mcp doctor
```

If you are worried that an operation should stop immediately:

```bash
runner-mcp emergency-stop on
```

You do not need to inspect the source code to use either command.
