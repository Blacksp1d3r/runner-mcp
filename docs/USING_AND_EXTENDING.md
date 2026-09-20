# Using and extending Runner MCP

Runner MCP is designed so you can start as a user and only become a developer when you actually need to.

## Use it without changing source code

For a normal installation:

~~~bash
git clone https://github.com/Blacksp1d3r/runner-mcp.git
cd runner-mcp
./install.sh
runner-mcp setup
runner-mcp doctor
runner-mcp guide
runner-mcp serve
~~~

The private configuration created by setup belongs on the machine running Runner MCP. Do not copy real infrastructure values into the public repository.

The normal path is:

1. add a project;
2. inspect its adapter capabilities;
3. add one or more predefined test profiles;
4. optionally add a staging service alias;
5. optionally configure PostgreSQL backup/migrations;
6. optionally configure staging deployment;
7. use local human approval for migration, deployment and rollback.

Runner MCP intentionally does not expose a general remote shell.

## Add projects without changing Runner MCP

Most projects should require configuration, not core-code changes.

~~~bash
runner-mcp project add myapp   --name "My App"   --repository owner/repository   --root /private/path/to/myapp   --adapter python

runner-mcp adapter inspect myapp
runner-mcp test-profile add myapp unit --preset auto
runner-mcp guide
~~~

The generic adapter never guesses commands. The Python adapter may detect only allow-listed local capabilities.

## Extend Runner MCP safely

Prefer these extension levels, in order.

### Level A — configuration

Use existing project, test, service, database, migration and deployment configuration when the current safety model already covers the task.

### Level B — built-in adapter

Add a new adapter when a project family needs safe capability detection or safe preset selection.

Adapters must:

- be registered in code;
- have a stable identifier;
- return only safe capability metadata;
- never return private filesystem paths;
- never dynamically import code named by configuration;
- never accept arbitrary shell command strings;
- resolve only to allow-listed presets.

Keep private/company-specific adapters out of the public repository when their implementation would reveal private infrastructure or deployment details.

### Level C — new bounded capability

Add a core capability only when an adapter or configuration cannot solve the problem.

A new mutating capability should normally include:

- a narrow input model;
- deny-by-default permissions;
- project/environment scoping;
- no arbitrary shell;
- bounded time and output;
- secret/path scrubbing;
- audit records;
- emergency-stop behavior;
- a human approval gate when the risk class requires it;
- unit and integration tests.

Do not weaken existing safety checks simply to make a new use case easier.

## Local development

Create a virtual environment and install development dependencies:

~~~bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
~~~

Use trusted code only on a persistent self-hosted runner. Public pull-request code should not automatically execute with privileged host access.

## Public-repository hygiene

Never commit real IP addresses, hostnames, internal domains, usernames, private endpoints or ports, absolute deployment paths, database endpoints, credentials, tokens, private keys, dumps or backups.

Use placeholders in examples. Real values belong in private local configuration or an appropriate secret store.

## Keep extensions understandable

When adding something reusable, update the user-facing documentation, security notes when the trust boundary changes, the roadmap/current-state files, and tests that prove the safe behavior.

The goal is that another person can install Runner MCP, understand what it will do, and extend it without needing access to the original developer's infrastructure.
