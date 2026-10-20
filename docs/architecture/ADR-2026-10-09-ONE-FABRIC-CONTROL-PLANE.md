# ADR-2026-10-09 — One Runner Fabric control plane

Status: ACCEPTED by operator on 2026-10-09. Applies across Runner Fabric, Runner-MCP, AIfordable and EnerCue. This is an architecture/policy decision, NOT runtime activation or proof of readiness.

## Binding decision
**Runner Fabric is the single authoritative control plane** for worker registration, discovery, capability/qualification evidence, eligibility, admission, leases and fencing, work-unit planning/routing/scheduling, capacity, lifecycle intent, recovery/failover and canonical audit. The Fabric Cockpit/ChatGPT are operator entry points, not parallel control planes.

**Runner-MCP / Agent Bus is the bounded communication and host-local execution layer**, not an independent scheduler or second authority for Claude/OCR/coding workers. It may expose fixed, allow-listed adapters and evidence, only under Fabric-authorized intents and host-local verification. Avoid duplicate control-plane state, policy, worker inventories or autonomous lifecycle decision-making.

**AIfordable workers (including Claude Code subscription-backed worker)** remain dedicated, least-privilege worker runtimes. Host-local service execution must remain bound to the dedicated OS identity and exact approved unit. Fabric does not get generic shell, cross-user sudo, arbitrary systemd unit, path, environment, credential, endpoint, unrestricted PowerShell or merge/deploy privileges. The host independently enforces authorization/fencing, target/action allowlists and preflight, and returns bounded status. Loopback-only service binding (currently expected at 127.0.0.1:8030) remains an independent check; service remains disabled by default absent separate production approval.

**EnerCue** consumes Fabric's qualified work-unit dispatch and provider-neutral capabilities. Claude may only claim explicitly scoped, isolated work after end-to-end readiness, authorization, relay/evidence and lifecycle qualification; preflight handshake alone is not execution readiness. Unqualified work such as EnerCue #89 stays blocked for dispatch. Claude must not bypass branch/path restrictions or receive merge/deployment authority.

## Boundaries and implementation sequence
1. Preserve provider- and OS-neutral worker contract; Linux/Incus and Windows backends are local implementations, not a separate control plane.
2. Define Fabric-owned exact-target lifecycle intents with versioned capability/evidence, actor/approval, lease/fencing generation, idempotency, expiry, audit and fail-closed returns.
3. Implement only the smallest fixed local service actuator for the dedicated AIfordable coder identity (Runner-MCP #381), not a second lifecycle policy manager. No generic sudo or arbitrary command execution.
4. Qualify local AIfordable rootless packaged service start/status/stop (#370), with actual user manager and listener/preflight evidence; keep disabled outside bounded test.
5. Prove complete Fabric → Agent Bus/Runner-MCP → authorized local adapter → worker → Fabric return path with fresh response correlation and no intermittent delivery failure (#590); then explicitly admit worker for bounded EnerCue work (#88/#89).
6. Measure actual OCR/coding throughput against real evidence; synthetic green tests alone do not prove production speedup or availability.

## Canonical cross-references
- Runner Fabric #1172 — platform-neutral worker capability contract and Windows qualification
- Runner Fabric #240 — Fabric F18 bounded work-unit orchestration owner
- Runner-MCP #381 — fixed bounded host-local service actuator only
- Runner-MCP #590 — external connector return-path issue
- AIfordable #370 — packaged Claude subscription coding-worker lifecycle qualification
- EnerCue #88 — Fabric-mediated Claude assistance
- EnerCue #89 — scoped Claude-ready ExperimentManifest; actual dispatch currently blocked

## Coordination
One architectural source of truth: this ADR is mirrored across the four repositories to make handovers discover it locally. Any later change must update all four copies and affected handovers/issues together. Do not interpret the policy decision as permission to start, deploy or merge a worker. Existing project roadmaps, branch ownership, unrelated deployments and tests remain unchanged.
