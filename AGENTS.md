# AGENTS.md

## Mission

Build Runner MCP as a small, auditable, deny-by-default operations interface. Prefer narrow capabilities over generic remote execution.

## Non-negotiable security rules

1. Never commit real server or infrastructure details to this public repository.
2. Never commit secrets, tokens, credentials, private keys, database dumps, or environment files.
3. Never expose arbitrary shell execution as a normal MCP tool.
4. Never use `shell=True` in normal execution paths.
5. Validate every project against an explicit allow-list.
6. Return only safe operational summaries; do not return private config values.
7. Treat deploys, migrations, restores, and production actions as high risk.
8. Production actions are out of scope until explicit approval gates exist.
9. All operational actions must be auditable.
10. Security tests are part of the definition of done.

## First-party control path — hard rule

Routine AI-assisted operations must prefer AIfordable-owned bounded control surfaces over broad
remote-control tooling.

Canonical order:
1. Runner Fabric coarse work-unit operations through Runner MCP / Agent Bus when available;
2. bounded Runner MCP capabilities for operations Runner MCP itself owns;
3. direct GitHub connector/mailbox only as bootstrap, source integration or fallback while a required
   first-party capability is unavailable;
4. broad remote-host tools such as Desktop Commander only as break-glass for a recovery/diagnostic
   action that the bounded first-party path genuinely cannot perform.

A blocked or absent Runner MCP/Fabric capability must never be bypassed by substituting generic
shell, filesystem, process, database, package-manager or remote-control authority. Record the missing
bounded capability and implement/review that capability instead.

Do not consume broad remote-tool quota for normal repository inspection, code changes, CI
reconciliation, runner scheduling, Agent Bus operations or Fabric work that can be expressed through
the first-party path.

## External discovery and independence — hard rule

Runner MCP must remain installable, operable, updateable and supportable without any secondary MCP directory, marketplace, gateway or hosted catalog.

Canonical authority is limited to:
- source and releases: `Blacksp1d3r/runner-mcp` on GitHub;
- Python distribution: `aifordable-runner-mcp` on PyPI;
- official MCP identity: `io.github.Blacksp1d3r/runner-mcp`;
- first-party documentation and security policy in this repository.

Glama, Smithery, mcp.so, AllMCPs, getmcp, MCP Find and similar services are optional discovery/marketing surfaces only. They are never runtime dependencies, release gates, sources of truth, required gateways, required hosting providers or reasons to change package identity, authentication, transport, security boundaries or the self-hosted architecture.

Do not add a public hosted endpoint, third-party gateway, alternate package identity, alternate registry identity, provider-specific runtime integration, paid listing/boost, or special deployment mode merely to satisfy an external directory. If a directory changes requirements, becomes unavailable or cannot index the canonical self-hosted project as-is, skip or remove that listing and keep Runner MCP unchanged.

A future first-party AIfordable discovery page may mirror canonical metadata, releases, hashes, install instructions and supported clients, but it must also point back to the canonical sources above and must not become required for runtime operation.

## Public examples

Use environment-variable placeholders and reserved example domains. Do not publish actual paths, ports, service names, database names, usernames, hostnames, or network addresses.

## Git workflow

Use small branches and pull requests. Update `handover/CURRENT_STATE.md` after meaningful milestones. Keep core code project-agnostic; project-specific behavior belongs in adapters/configuration.

## CI safety

This repository is public. Never run untrusted fork or public pull-request code on a privileged persistent self-hosted runner. Use trusted/manual gates or an isolated disposable runner.

## Mandatory session bootstrap and handoff

Before material work, every ChatGPT/Claude/other-agent session must read and reconcile in this order:

1. `AGENTS.md`
2. `roadmap/ROADMAP.md`
3. `roadmap/DEPENDENCIES.md` when present
4. `handover/CURRENT_STATE.md`
5. `handover/SESSION_HANDOFF.md`
6. `handover/AGENT_EXCHANGE.md`
7. `decisions/DECISIONS.md`
8. current GitHub PRs, issues and CI/workflow state

GitHub current state wins if a handoff file is stale. Reconcile first; do not continue from stale assumptions.

Project-wide agent reviews, blockers, assignments and handoffs belong in `handover/AGENT_EXCHANGE.md`; code-specific review comments stay on the PR. Newest exchange entries go first and must not contain secrets, customer data or full test logs.

Feature/code work remains branch -> PR -> review/tests. Handoff/coordination files may be updated on the agreed documentation/coordination surface without a separate feature PR for every message.

An AI assignment is complete only when relevant tests/evidence are terminal and green or the blocker is explicitly recorded, and the next agent has a clear handoff. “Claude says done” or “ChatGPT says done” is not acceptance by itself.

Before closing a chat after material state changed, update `handover/SESSION_HANDOFF.md`, `handover/CURRENT_STATE.md` and, when agent coordination changed, `handover/AGENT_EXCHANGE.md`.

## Multi-agent availability and task takeover

Claude/other-agent availability is a parallel accelerator, not a project dependency. A rate/usage limit is not by itself a blocker.

When a persistent agent queue exists at `claude_feedback/CURRENT_ASSIGNMENT.md`:
- the agent starting a task records a claim/status plus branch/PR when known;
- before taking over another agent's task, reconcile GitHub branches, PRs and CI and inspect any work already pushed;
- if the user confirms the previous agent is unavailable or the task is otherwise blocking progress, ChatGPT may take over rather than wait;
- never duplicate an active conflicting branch/PR; continue/review existing useful work when safe;
- a resumed agent must re-read the queue and skip tasks already claimed by another agent or completed.

This takeover rule does not weaken branch/PR/review/test requirements.

If `claude_feedback/CURRENT_ASSIGNMENT.md` exists, read it after GitHub reconciliation before claiming parallel work; its task claim/takeover status prevents duplicate agent work.

## AI source-control identity — hard rule

AI assistants may edit files, run tests, review changes, and prepare branches or pull requests, but an AI provider identity must never be recorded as source-control authorship or repository branding.

The following are prohibited:
- Git author or committer identities named `Claude`, `Claude Code`, or another Claude-branded identity.
- Git author or committer email addresses at `anthropic.com`, including `noreply@anthropic.com`.
- `Co-Authored-By` trailers that identify Claude or Anthropic.
- `Claude-Session:` trailers or Claude Code session URLs in commit metadata.
- Provider-branded branch prefixes such as `claude/` or `anthropic/`.
- Automatic pull-request footers such as `Generated with Claude Code` / `Generated by Claude Code`.

AI tools must not change Git author/committer configuration to an AI/provider identity. In owner-operated environments, commits prepared by an AI must be committed under the repository owner's configured maintainer identity; other human/service identities require explicit repository-owner approval.

Before every push, remove prohibited attribution metadata. Do not bypass, weaken, skip, rename, or disable the repository commit-attribution policy check. If an AI tool attempts to add prohibited attribution automatically, strip it before committing or pushing.
