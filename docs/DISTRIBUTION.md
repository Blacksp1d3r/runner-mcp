# Distribution and discovery

Runner MCP is packaged as a Python project and uses the official MCP Registry as its primary MCP discovery surface.

## Release identity

- PyPI project: `aifordable-runner-mcp`
- primary CLI: `runner-mcp`
- PyPI/Registry launcher alias: `aifordable-runner-mcp`
- MCP Registry name: `io.github.blacksp1d3r/runner-mcp`
- source repository: `Blacksp1d3r/runner-mcp`
- release workflow: `.github/workflows/publish.yml`
- protected GitHub Environment: `pypi`

The README contains the exact `mcp-name` marker required for PyPI ownership verification by the MCP Registry.

## One-time PyPI setup

PyPI Trusted Publishing is deliberately tokenless. Before the first package publication, create a **pending GitHub publisher** in the maintainer's PyPI account with exactly:

- PyPI project name: `aifordable-runner-mcp`
- owner: `Blacksp1d3r`
- repository: `runner-mcp`
- workflow: `publish.yml`
- environment: `pypi`

Create the matching GitHub `pypi` environment and require a human approval for release publication.

No long-lived PyPI API token belongs in GitHub secrets.

## Release flow

The release workflow is human-triggered from `main`.

It:

1. verifies the requested version exactly matches `pyproject.toml` and `server.json`;
2. runs the full local release check;
3. builds wheel and sdist artifacts;
4. publishes those exact artifacts to PyPI using GitHub OIDC Trusted Publishing;
5. waits until that exact version is visible from PyPI;
6. installs a pinned, checksum-verified `mcp-publisher`;
7. publishes `server.json` to the official MCP Registry using GitHub OIDC;
8. creates the matching Git tag and GitHub pre-release only after both external publications succeed.

If any publication step fails, the workflow stops. It does not silently create a GitHub release that claims a registry publication succeeded.

## Why Registry installation still needs setup

Runner MCP is not a zero-configuration stdio utility. It is a self-hosted operations boundary with private local project configuration and authentication.

The Registry package metadata launches the safe default local server at `127.0.0.1:8000` and requires the bearer token created by local setup. Follow `QUICKSTART.md` before connecting a client. This preserves the existing security boundary rather than weakening authentication for marketplace convenience.

## Secondary directories

After the official MCP Registry entry is live, downstream MCP directories can point to the canonical Registry/GitHub identity rather than maintaining divergent installation metadata.

Directory copy should use `docs/LAUNCH_COPY.md`. Never publish private infrastructure screenshots, hostnames, paths, tokens or project/customer names.
