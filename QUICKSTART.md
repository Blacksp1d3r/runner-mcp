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

### Configure staging deployment

Runner MCP deploys only projects marked as `staging`. First configure a restartable service alias with a health check, then create a private release location:

```bash
runner-mcp deployment-config add myproject \
  --release-root /path/to/private/staging \
  --service web \
  --require-test unit
```

Add `--run-migrations` only when the project already has database and migration configuration.

The release path remains private and is not shown by normal list/MCP output.

Deployment itself is exposed through MCP as a short asynchronous workflow:

- `plan_deploy(project)` performs read-only preflight;
- `deploy_staging(project)` starts a background deployment job;
- `deployment_status(job_id)` returns safe persisted status/result.

Runner MCP deploys only a clean Git HEAD. It does not accept an arbitrary branch/ref or shell command from the MCP client. If health fails after a deployment without migrations, one automatic code rollback may occur. After database migrations, health failure requires manual recovery and never triggers automatic database restore.

### Inspect and roll back releases

Release history is available through MCP with safe metadata only:

- `list_releases(project)` shows current/history/retention state;
- `rollback_plan(project)` resolves the direct previous release;
- `rollback_release(project)` starts one asynchronous rollback;
- `rollback_status(job_id)` reports its persisted result.

The client cannot choose a target release. One action moves at most one release back. A second step requires a new plan and a new action after health verification.

If the active release applied database migrations, code rollback is blocked. Runner MCP never automatically restores the database.

Retention protection combines minimum release count and minimum age. Automatic release deletion is not enabled yet.

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

For project-aware next steps, run runner-mcp guide. It reports only safe configuration summaries and suggested commands; it does not print private paths, service unit names or credentials.

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

The safe staging core now includes service aliases, PostgreSQL backups/migrations, staging deployment, one-step rollback and local approval gates.

The remaining onboarding gaps are mainly:

- service installation and automatic startup packaging;
- guided private-tunnel and HTTPS/reverse-proxy setup;
- optional graphical administration;
- stronger isolation for untrusted public-fork code;
- database restore/PITR orchestration and retention pruning.

Runner MCP remains a staging/development operations tool; production mutations are deliberately disabled.

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

## Project adapters

List built-in adapters:

```bash
runner-mcp adapter list
```

Inspect safe capabilities for a project:

```bash
runner-mcp adapter inspect myproject
```

A Python project can be added with `--adapter python`. Then `--preset auto` may select only an existing allow-listed preset such as pytest or Alembic when safe project-local tooling is detected. The generic adapter never guesses commands.

## Human approval for high-risk actions

Migration apply, staging deploy and code rollback use a two-step flow.

First request an approval plan through MCP with `request_action_approval(project, action)`. The action is one of `migration`, `deploy`, or `code_rollback`.

Then approve it locally on the controlled host:

```bash
runner-mcp approval status APPROVAL_ID
runner-mcp approval approve APPROVAL_ID
```

The local CLI shows the safe plan and asks for an explicit confirmation phrase. The MCP client has no tool that can approve its own request.

Finally call the corresponding MCP action with the approved `approval_id`. The approval is short-lived and single-use. Changes to the approved commit/rollback target invalidate the plan.

Production environments remain read-only.

## Private ChatGPT connection

For supported OpenAI products, prefer OpenAI Secure MCP Tunnel instead of exposing Runner MCP directly to the public internet. Run Runner MCP on loopback/private networking and run the tunnel client inside the network that can reach it. The tunnel is outbound HTTPS only.

A future public one-click hosted relay is optional and outside the current MVP.

## Extending Runner MCP

Most new projects should be added through configuration or a built-in adapter rather than by weakening the core safety model.

See docs/USING_AND_EXTENDING.md for the supported extension path and CONTRIBUTING.md for development and review rules.
