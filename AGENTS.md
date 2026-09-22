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
