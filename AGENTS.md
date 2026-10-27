## Evidence-first diagnostics: session startup and reuse

Before a new task, consult the current canonical AIfordable infrastructure registry and scoped Runner-MCP #669 operator receipts, in addition to AGENTS, roadmap, topology, CURRENT_STATE and SESSION_HANDOFF. Classify each fact as REUSE (stable mapping already known), REFRESH_TARGETED (expired or changed process generation, imported wheel or completion result), or WAIT (authority missing). Only ask for a new measurement when a scoped fact is actually missing. Do not repeat already qualified archive and cron checks merely because a new conversation starts.

Original github-runner uses Fabric command 'agent-bus-run' for the Agent Bus role, and 'agent-serve-qualification' for Fabric qualification. The narrow Runner-MCP '*-worker run' and 'fabric-agent-qualification run' patterns are not the sole accepted commands. See existing central AF-HOST-0001 / AF-SVC-0010 and #669 for owner, historical PID/startticks and different Fabric slots. Short cron tasks need run-result proof; older PID alone never proves new live bytes or loaded-wheel identity.

Missing or conflicting original host, service, executable/source or recovery proof still forbids mutations. Any truly new check is read-only, original-host-scoped and labelled with host/terminal/user. Record qualified evidence in the existing registry/handover, never a second inventory or controller.

## Mandatory physical topology + exact serving-runtime preflight (owner decision 2026-10-22)

**Before generating an executable host script, giving a host-specific terminal
command, calling a mutating host tool, installing/updating software, or claiming
a live end-to-end result, perform this gate for the EXACT physical target.**
This applies at each new session, after a handover, after a deployment/restart,
and whenever target host, user, runtime or connection changes. A prior chat
summary is never current host evidence.

1. **Read the existing topology and current authority first:** this repository's
   `AGENTS.md`, canonical diagnostic/infrastructure topology, current handover,
   relevant issue/PR and actual private AIfordable infrastructure/credential
   metadata authority. GitHub topology is an *expected logical map*, NOT proof
   of a currently installed version, actual reachability or mutation authority.
   Do not create a second topology source or copy private coordinates into Git.
2. **Resolve target host and scope:** distinguish physical host, VM/container,
   SSH/tunnel alias, authenticated first-party endpoint, service manager
   (`system` vs `user`), service owner UID, and exact service/listener
   being changed or tested. Different instances of the same named project
   are DIFFERENT deployments. A connected MCP/Fabric peer attests only its
   OWN serving endpoint, never an unrelated host's installed runtime.
3. **Attest what is REALLY SERVING on that same target:** through an existing
   authorized bounded read-only first-party capability, correlate host identity,
   service unit, MainPID, port/listener owner, resolved live executable and
   installation slot, interpreter/imported module, trusted wheel/source identity,
   and any relevant database/credential owner and rollback state. Distinguish
   `GitHub source` vs `locally installed slot` vs `process actually serving`;
   source merges, passing CI, successful installation and bridge readiness
   are NOT interchangeable or cross-host evidence.
4. **STOP ON MISMATCH OR UNKNOWN:** if owner/host/source/slot/process/port
   mapping is stale, conflicting, inaccessible, or unverified, perform only
   bounded non-secret, read-only diagnosis. Do NOT infer, retry a mutating
   script, suggest alternate host addresses, select a different launcher,
   switch releases, bypass self-update/A6/A7, or use broad remote shell as a
   shortcut. Record the precise evidence gap and owner in the existing issue.
5. **Every operator command must say WHERE:** explicitly label the machine,
   shell (Windows PowerShell vs Linux), intended user, read-only versus
   mutation, prerequisites and expected safe stop result. Avoid copied steps
   that target an ambiguous host alias; never print credentials or private
   environment values.
6. **Reconcile after a successful change:** verify the same physical service's
   serving revision/health and existing rollback, then update the authorized
   topology metadata, issue and handover with fresh non-secret evidence.
   A real SQL command/result/ACK needs its own end-to-end evidence; liveness
   and HTTP authentication-only probes are not an ACK.

This is an **operational precondition**, not an additional relay, controller,
auth/login mechanism, installer, approval/review queue, or authority to bypass
existing bounded-tool and service constraints. Related existing fleet coordination:
Runner-Fabric #924, Runner-MCP #341/#669 and AIfordable #585.

## Owner-confirmed MCP scope in integrated cockpit (2026-10-20)

AIfordable is the company-wide **business cockpit**, holding customer/product registrations and canonical desired-state/infrastructure identity metadata. Runner-Fabric owns the **technical F10/F17 Cockpit and all technical task/AI orchestration**. Runner-MCP is the **bounded authenticated MCP execution/access boundary** plus the optional narrow Fabric bridge, not another scheduler, provider/gateway authority, relay, updater or generic filesystem manager. Existing AIfordable-owned relay code/service stays a transport with Fabric coordinating work/results/ACK; Agent Bus traffic need not physically pass through Runner-MCP. Reuse approved workspace preflight/prepare on bounded worker/work-unit IDs only; Fabric decides scheduling. No host mutation or release/relay/runtime qualification follows from this documentation. Canonical contract: [https://github.com/Blacksp1d3r/AIfordable/blob/main/docs/CROSS_PRODUCT_ROLE_BOUNDARIES.md](https://github.com/Blacksp1d3r/AIfordable/blob/main/docs/CROSS_PRODUCT_ROLE_BOUNDARIES.md).

## Operator control route — 2026-10-17

All normal cross-server operational data (topology, health, installed/loaded version, heartbeat), rollout and installation operations are REQUIRED to pass through first-party bounded Runner-MCP tools and its authenticated Runner Fabric bridge, rather than Desktop Commander, direct unmanaged remote shell or GitHub Actions-as-host-control. Desktop Commander is emergency break-glass ONLY after the ordinary path is verified unavailable, never an automatic substitute for a missing feature. A connected Runner-MCP process verifies its OWN hosting runtime, not another host listed in a topology file. Per-host fleet health and managed update require a separately authenticated, identity-bound agent/Agent Bus route and fresh original-client evidence; unknown/stale remains UNKNOWN and mutation unavailable if not admitted. Preserve the canonical topology: do not create duplicate primary tunnels or conflate lab and runner hosts. The lab's historical native Python SIGSEGV activation gate is #198 and primary-tunnel route confusion is Runner-Fabric #1202. Missing private tunnel-health URL on the connected central instance is not by itself evidence of lab failure.

# AGENTS.md

## Owner decision — test-first development; review later (2026-10-14)

This is the current operator-approved pre-customer workflow. It supersedes older project
instructions imposing review waits (12h/24h), mandatory external review, GitHub
APPROVED events or reviewer-App availability as prerequisites for source-code merges.
For work on the functional product: implement -> automated lint/build/tests/CI on
the exact change -> fix actual defects -> use the normal GitHub merge path under
its real enforced rules -> qualify and test isolated staging -> validate behaviour.
Do not wait for Blacky, RTX5080, Claude or any external reviewer. These agents
MAY examine code and report bugs concurrently or asynchronously; their checks
are advisory, and actionable defects should be fixed. Formal review programs
are deferred until the application is operational and customer phase begins.

This is **not** permission to bypass GitHub-enforced branch rules, green CI,
source/revision validation, host isolation, real security defects, production
approval/backup/rollback, safe credential and billing custody, tenant privacy or
runtime lease/fencing. A source merge does not authorize a production release,
remote command, paid model/API call, protected-data operation or live AI dispatch.
The employer-managed workstation must never be used for private Runner-Fabric
downloads, scripts, tunnels, SSH or development execution. Restrict any host
tests/deploys to authorized privately owned environments. Full context and
status: Blacksp1d3r/Runner-Fabric issue #972 (2026-10-14 owner override).


## Mission

Build Runner MCP as a small, auditable, deny-by-default operations interface. Prefer narrow capabilities over generic remote execution.

## Canonical cross-project standards

For every session follow Library `/Standards/MASTER_AI_ENGINEERING_SESSION_HANDOFF_PROTOCOL.md` v1.2; for repository/bootstrap design follow Library `/Standards/AI_REPOSITORY_BLUEPRINT_STANDARD.md` v1.0. These standards complement, rather than replace, the stricter Runner-MCP security and ownership rules below. The Library master never grants host, filesystem, Git or production privileges.

Runner-MCP predates the blueprint. Apply its `COMPATIBLE/PARTIAL/NEEDS_REVIEW/BLOCKED` migration mapping in `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md`: preserve current `roadmap/children`, handover, diagnostic topology and live agent ownership. **Do not** mass-rename existing children or infer qualified local Git/storage authority. New bounded child tasks should use `TASK.md` + `STATE.md`, with a reference to legacy issue documents when relevant. Any Fabric automatic scaffold plan/apply is a separately authorized future capability, not an available Runner-MCP execution surface.

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

## Zero incremental software-cost rule

Until AIfordable has revenue, new project software/service dependencies must have **zero incremental licence or subscription cost**. Prefer existing first-party code, permissively licensed/open-source software, and capabilities already available at no additional software cost. Hardware, electricity and connectivity are owner infrastructure costs and are a separate optimisation concern.

Paid SaaS, Enterprise-only tooling, paid deployment/update tiers, commercial gateways and similar services may be studied as references but must not become runtime/build/control-plane dependencies without a later explicit owner decision after revenue exists. Time spent building/maintaining free software is an accepted current cost; do not trade this rule away merely for convenience.

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

## Epic decomposition and bounded-child rule

Large roadmap items, epics and cross-cutting features must be decomposed into bounded executable child work before substantial implementation.

Use one umbrella for end-to-end intent and dependencies, then split implementation into small child issues with one coherent responsibility and explicit acceptance criteria. Each child should be small enough to inspect, implement, test, review and hand off within a bounded tool/model context. Large Markdown plans are architectural references, not the executable unit of work. When context/tool output becomes truncated or hard to reconcile, split further rather than compressing away constraints. Parent completion is derived from child evidence.

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

## Diagnostic topology — mandatory troubleshooting rule

For non-trivial troubleshooting, regression analysis, new bounded components or changes to source/state/evidence flow, read `docs/diagnostics/README.md` and resolve the owning component in `docs/diagnostics/component_registry.yml` before changing behavior.

Then inspect that component's `ROADMAP.md`, `SOURCES.md`, `DATA_LINEAGE.md` and `FAILURES.md`, plus `FIELD_LINEAGE.md` for public tool/result fields. Diagnose from the visible symptom upstream to the earliest proven expected/observed divergence. Do not patch a downstream status/result merely because it is where the error became visible.

The diagnostic structure must remain public-safe: no real hostnames, ports, paths, usernames, service names, endpoints, credential values or customer payloads. Infrastructure/credential facts reference the canonical AIfordable/Runner-Fabric authorities instead of being copied here. Existing `.github/ISSUE_TEMPLATE/failure-record.md` and `docs/SAFE_DIAGNOSTICS.md` remain canonical detailed failure/runtime-diagnostic contracts.

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
