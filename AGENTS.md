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
