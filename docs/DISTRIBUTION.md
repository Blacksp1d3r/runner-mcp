# Distribution and discovery

Runner MCP is packaged as a Python project and uses the official MCP Registry as its primary MCP discovery surface.

## Release identity

- PyPI project: `aifordable-runner-mcp`
- primary CLI: `runner-mcp`
- PyPI/Registry launcher alias: `aifordable-runner-mcp`
- MCP Registry name: `io.github.Blacksp1d3r/runner-mcp`
- source repository: `Blacksp1d3r/runner-mcp`
- release workflow: `.github/workflows/publish.yml`
- protected GitHub Environment: `pypi`

The README contains the exact `mcp-name` marker required for PyPI ownership verification by the MCP Registry. GitHub-backed Registry namespaces are case-sensitive in the publish authorization path, so the `io.github.Blacksp1d3r/*` prefix must preserve the account casing returned by GitHub authentication.

## Published state

PyPI `0.1.1` was published successfully, but the first MCP Registry publication attempt was rejected because the server metadata used a lowercase GitHub namespace while Registry OIDC authorized `io.github.Blacksp1d3r/*`. PyPI release files are immutable, including the README ownership marker embedded in package metadata.

Release `0.1.2` was the first fully aligned cross-registry publication.

Current published release `0.1.3` was released on 2026-10-02 through protected workflow run `36962568072`:

- PyPI: `aifordable-runner-mcp==0.1.3` via GitHub OIDC Trusted Publishing;
- official MCP Registry: `io.github.Blacksp1d3r/runner-mcp` version `0.1.3`;
- GitHub pre-release: `v0.1.3` with wheel and source distribution;
- Git tag and release target: exact validated commit `0aa013c279128e22fbd53be32c35bced3ae26834`;
- the workflow verified exact version metadata and ran the complete release check before any publication.

Canonical public links:

- repository: https://github.com/Blacksp1d3r/runner-mcp
- PyPI: https://pypi.org/project/aifordable-runner-mcp/
- official MCP Registry search: https://registry.modelcontextprotocol.io/?q=io.github.Blacksp1d3r%2Frunner-mcp
- GitHub releases: https://github.com/Blacksp1d3r/runner-mcp/releases

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

## Canonical directory submission packet

Use this exact identity when a directory requires manually entered metadata:

- name: `Runner MCP`;
- product signature: `Runner MCP — an AIfordable project`;
- AIfordable tagline: `Secure software. Built with AI. Fairly priced.`;
- short tagline: `Controlled self-hosted AI operations without a general-purpose remote shell.`;
- description: `Security-first self-hosted MCP for configured development and staging operations. Runner MCP exposes bounded project, test, service, database, deployment and rollback capabilities with audit, emergency-stop and approval controls instead of arbitrary remote shell input.`;
- primary category: `Developer Tools`;
- useful secondary categories: `CI/CD & DevOps`, `Security`;
- tags: `mcp`, `devops`, `self-hosted`, `security`, `python`;
- repository: `https://github.com/Blacksp1d3r/runner-mcp`;
- PyPI package: `aifordable-runner-mcp`;
- official Registry identity: `io.github.Blacksp1d3r/runner-mcp`;
- install: `uv tool install aifordable-runner-mcp`;
- primary CLI: `runner-mcp`;
- authentication: local bearer token created by `runner-mcp setup`;
- license/pricing: MIT, open-source, self-hosted;
- hosting model: self-hosted software, not a hosted SaaS service.

Do not substitute `aifordable-runner-mcp` for the Runner MCP product name and do not create a second Registry identity.

## Secondary discovery — optional only

The official MCP Registry, PyPI and GitHub are the canonical public sources. Everything else is optional discovery/marketing and must be treated as replaceable.

A secondary directory may index or link Runner MCP only if it can preserve the canonical project unchanged:

- product: `Runner MCP`;
- package: `aifordable-runner-mcp`;
- official MCP identity: `io.github.Blacksp1d3r/runner-mcp`;
- repository: `Blacksp1d3r/runner-mcp`;
- hosting: self-hosted;
- existing authentication, transport and security boundaries.

Secondary services must never become runtime dependencies, launch gates, release gates or sources of install/auth truth. Do not route normal Runner MCP traffic through their gateways or hosting merely to obtain a listing.

Directory policy:

1. Glama — optional listing only. It may point at the canonical public repository and read repository metadata. Do not use Glama hosting/gateway as a Runner MCP requirement.
2. Smithery — optional and non-blocking. Publish/list only if its current flow accepts the canonical self-hosted project without inventing a public endpoint, MCPB bundle, alternate package identity or provider-specific deployment. Otherwise skip it.
3. mcp.so — optional free community discovery only; never pay merely for expedited indexing or backlinks.
4. AllMCPs — optional normal review path only; skip if it requires unnecessary identity, hosting or paid-placement changes.
5. getmcp, MCP Find and similar indexes — passive discovery is welcome, but no product change is justified for indexing.

If any external directory changes its rules, disappears, delists Runner MCP or conflicts with this policy, Runner MCP must continue to install, run, update and be supported normally from the canonical sources. The correct response is to update or drop the external listing, not to redesign Runner MCP around it.

Avoid bulk-submission services, backlink schemes, duplicated listings and low-quality catalogs whose main value is paid SEO rather than developer discovery.

Directory copy should use `docs/LAUNCH_COPY.md` and the canonical packet above. Never publish private infrastructure screenshots, hostnames, paths, tokens or project/customer names.
