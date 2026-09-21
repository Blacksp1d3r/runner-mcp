# Five-minute local demo

This demo shows Runner MCP's core safety model on a Linux machine without publishing a server, adding a paid service or exposing a general-purpose shell.

It uses this repository itself as the sample project. All installation-specific values remain on your machine.

## What this demo proves

At the end you should have:

- a local Runner MCP installation;
- one allow-listed project;
- a healthy `runner-mcp doctor` result;
- a named predefined test profile;
- a working external emergency stop;
- no public endpoint and no arbitrary remote shell.

The demo intentionally does not configure a database, service, deployment target or production action.

## 1. Clone and install

```bash
git clone https://github.com/Blacksp1d3r/runner-mcp.git
cd runner-mcp
./install.sh
```

## 2. Prepare a trusted demo test environment

Runner MCP's pytest preset deliberately requires a project-local Python executable. Create one in this clone:

```bash
python3 -m venv --copies .venv
.venv/bin/python -m pip install -e '.[dev]'
```

The `--copies` flag is intentional: Runner MCP refuses symlink executables for predefined profiles, so the demo creates a regular project-local Python executable instead of the symlink that many `venv` installations use by default.

This environment is used only for the predefined demo test profile.

## 3. Run the setup wizard

```bash
runner-mcp setup
```

For this local demonstration:

- choose local mode;
- use a short project code such as `demo`;
- use a descriptive project name such as `Runner MCP demo`;
- use `Blacksp1d3r/runner-mcp` as the repository identifier;
- use the current clone as the project folder;
- review and explicitly confirm the proposed retention settings.

The setup wizard stores runtime configuration privately. Do not copy generated credentials or absolute local paths into issues, screenshots or public documentation.

## 4. Verify the safety baseline

```bash
runner-mcp doctor
runner-mcp status
runner-mcp guide
```

A healthy demo setup should not report a failing doctor check.

Normal status and guide output must not expose the configured project root, bearer credential or other private runtime values.

## 5. Add a predefined test profile

```bash
runner-mcp test-profile add demo unit --preset pytest
runner-mcp test-profile list demo
```

Runner MCP detects the project-local `.venv/bin/python` and stores an exact pytest argv internally.

The AI-facing model is intentionally narrow: a client may select the project `demo` and profile `unit`; it does not get to submit a shell command.

## 6. Exercise the emergency stop

```bash
runner-mcp emergency-stop on
runner-mcp emergency-stop status
```

With the stop active, new operator mutations are blocked.

Clear it only when you are ready:

```bash
runner-mcp emergency-stop off
```

Runner MCP requires the explicit `UNLOCK` confirmation before operator work resumes.

## 7. Start the local MCP service

```bash
runner-mcp serve
```

The safe default is loopback-only. This demo does not require an internet-facing listener.

To connect an AI client later, use a supported private MCP transport or the optional bounded GitHub mailbox bridge described in [GITHUB_MAILBOX_BRIDGE.md](GITHUB_MAILBOX_BRIDGE.md).

## What an AI client is allowed to request

With a configured project and test profile, the relevant bridge request is structurally equivalent to:

```json
{
  "protocol_version": 1,
  "request_id": "demo-001",
  "action": "run_tests",
  "project": "demo",
  "profile": "unit"
}
```

There is deliberately no `command`, `shell`, executable path, environment value or service name field in that request.

## Cleanup

If this was only an evaluation, stop the local Runner MCP process and remove the demo configuration using the normal CLI/configuration workflow. The project-local `.venv` can also be removed.

Never delete or loosen private configuration permissions merely to make cleanup easier.

## Next

For a real staging project, continue with [QUICKSTART.md](../QUICKSTART.md). Add only the capabilities you actually need: test profiles first, then optional service, database, migration and deployment configuration.
