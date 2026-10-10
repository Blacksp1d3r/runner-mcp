# 2026-10-10 — Connected MCP read-only probe matrix

Tracking: [Runner-MCP #590](https://github.com/Blacksp1d3r/runner-mcp/issues/590). Adjacent authority gate: [#634](https://github.com/Blacksp1d3r/runner-mcp/issues/634). Owner: MCP interface/component 14 and tunnel/component 11. Source of evidence: one authenticated ChatGPT-connected session, **not** a qualified independent operator/local runtime inspection. Capture window: 2026-10-10 afternoon Europe/Brussels. Main GitHub tree checked at `167cc30c402d1d23dd1fb57ce33c7f422bae104b`.

## What this session actually returned

| Read-only tool | Observed response | Strict conclusion |
|---|---|---|
| `list_projects` | Structured success: six registered staging projects, including `runner-mcp` | Only the exposed registration list exists; not primary local Git or a qualified mirror |
| `project_capabilities(runner-mcp)` | Structured success: generic adapter, `project_root_available=true` | Adapter can report a project root; no provenance, ownership, filesystem authority, or source revision proven |
| `queue_status` | Structured success: zero queued/claimed/running, two available workers, project lock inactive | Queue snapshot only, not health of all worker services or Fabric lease authority |
| `safety_status` | Structured success: operator-stop inactive, retention configured | Only safety status projection; no acceptance for restore/release mutation |
| `runtime_doctor` | WARN, **12 named checks**, zero failures, three warnings: continuity configuration unavailable, worker qualification unavailable, migration job storage not configured | Only these 12 checks proven on the answering route; source generation still UNKNOWN |
| `build_identity`, `project_status(runner-mcp)`, `worker_status` | Generic client/tool failure, no structured application payload | First failing edge and responding generation UNKNOWN |
| `file_metadata(runner-mcp, AGENTS.md)`, `known_project_preflight(runner-mcp)` | Generic client/tool failure | Neither file reachability nor project source admission proved |
| `fabric_repository_mirrors_activation_readiness`, `fabric_bridge_preflight`, `fabric_host_inspect` | Generic client/tool failure | Cannot admit mirror/storage/bridge/host readiness |
| `fabric_continuity_status`, `fabric_repository_mirrors_preflight`, `known_project_source_preflight(runner-mcp)` | Connector exception mapped as `INVALID_ARGUMENT` with generic nested execution error | **Not** a proven invalid user argument, Fabric policy rejection, host absence, or a ready mirror; actual error lineage unknown |

Do not infer that all successful and failing tool calls share an identical installed generation or response route. Do not infer physical disk independence, protected release custody, queued Claude work, or live status from GitHub source CI.

## Source cross-check

On current GitHub source `src/runner_mcp/server.py`:

- `list_projects` projects each `cfg.public_summary(code)`; `project_status` retrieves the same allow-listed `cfg`, projects `cfg.public_summary(project)`, adds `status=registered`, and records a bounded audit event. A successful list with a failed status therefore does **not** independently prove a project config absence; it calls for tool-call admission/dispatch/serialization and private audit/route correlation.
- `runtime_status` source now has fixed degraded reply guards for unreadable managers (merged source #627). `build_identity` source now has fixed unavailable reply for missing/invalid provider (merged source #629). This does **not** prove either source implementation is installed on the connected runtime.
- The current source doctor contains at least the additional checks `self_update_source_baseline`, `self_update_runtime_activation`, and `fabric_a6_binding_state`, while the observed projection is 12 checks without them. Installed version versus client catalogue/session versus tunnel target generation remains an unresolved three-way distinction.

## Minimal approved operator-owned correlation (no host mutation)

1. Record a *private and sanitized* first-party installed build/schema identity plus the client-advertised tool schema/catalogue revision and an independently authorized target/route generation. If any element is unavailable, set `UNQUALIFIED`, not `current-main`.
2. With existing approved, bounded read-only dispatcher, response-delivery and MCP audit/counter projections, correlate **one** known-good `list_projects` call and **one** failing `project_status(runner-mcp)` call, each with its own opaque request ID, target generation and result classification. Compare admission, dispatcher receipt, server dispatch, server completion, response-delivery 200 acceptance and client outcome. No raw payloads, token headers, private addresses, host paths or full request logs.
3. Correlate `build_identity` and `runtime_status` once on an authorized fresh session **after** confirming that version and route evidence belong to the same target. Require structured valid/unavailable or degraded envelopes, not generic connector failure. A missing `build_identity` identity is a BLOCK, not a successful runtime identity.
4. Identify the **first divergent edge** and owner (client/catalogue, tunnel response delivery, server tool dispatch, status manager or source identity provider). If no correlation exists, leave #590 OPEN as `UNKNOWN` and request a specific bounded diagnostic capability; do not enable generic command execution to compensate.
5. For #634, treat `list_projects` and `project_root_available=true` as *registry-only* facts. Local primary Git ownership, independent storage, isolated restore and Fabric fencing remain `BLOCKED_EXTERNAL_AUTHORITY`; no root `project.yml`, automatic mirror action or artifact deletion.

## Safety and acceptance

No restarts, self-updates, tunnel changes, mount/copy/delete, credential changes, logging of private topology, synthetic claim of a Fabric lease, access to another worker's branch or cloud executor fallback. A source-only documentation merge does not establish installed runtime, archive receipts or authorized physical Git custody.

Issue #590 may close only after one authenticated fresh route proves consistent installed identity, complete expected doctor schema, canonical structured status, and request-to-response matching across the relevant tools. This snapshot itself is **diagnostic evidence**, not operational acceptance.
