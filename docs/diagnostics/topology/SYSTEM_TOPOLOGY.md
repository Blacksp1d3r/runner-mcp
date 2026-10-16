# Runner-MCP system topology

This topology is intentionally deployment-neutral.

```text
MCP client
  -> HTTP/MCP server + tool catalogue
     -> bounded tool schema
        -> authorization / operational safety
        -> owning component manager
           -> private local state/config
           -> project source/test/deploy/database adapter
           -> fixed Runner-Fabric peer
           -> GitHub mailbox/source edge
           -> fixed tunnel/control transport
        -> audit / safe diagnostics / result projection
  <- client catalogue/session may have its own refresh state
```

## Component edges

- MCP server/interface projects bounded capabilities into the client-visible tool catalogue.
- runtime/update consumes project-source + test execution + service lifecycle.
- project-source/custody feeds testing, deployment, migration, self-update and Fabric-update staging.
- mailbox/watchers feed bounded request processing and completion delivery.
- Fabric bridge is a fixed peer boundary; Runner-Fabric remains orchestration authority.
- worker qualification/bootstrap consumes fixed private policy + Fabric revision/evidence.
- deploy/migration/backup consume known-project config + safety/approval.
- CI runner consumes bounded enrollment/lifecycle/secret-handoff contracts.
- tunnel/connectivity supplies a transport/readiness boundary, not domain authority.
- diagnostics/audit/build identity observe or stamp operations but do not widen authority.
- artifact/mirror custody supplies immutable content/source evidence to approved consumers.

## Failure-domain rule

A healthy local component does not imply the end-to-end path is healthy. A healthy server capability also does not imply an already-open client has refreshed its catalogue. Every crossed boundary remains separately observable as local, client-interface, peer, source-control, transport or external-provider state.

## 2026-10-14 — Original-client and Fabric-peer live generation

Logical operational shape, excluding private coordinates:

```text
ChatGPT connector -> one independent tunnel -> Runner-MCP MCP server 0.1.8
 -> bounded FabricBridgeClient -> Fabric Agent MCP 51c37f1e...
 -> cron-managed Agent Bus worker and qualification agent, both 51c37f1e...
 -> private exact-artifact custody + managed slot update transaction
 -> audit/observability (not an execution-authority substitute)
```

- **Proven by original-client and operator receipts:** serving Runner-MCP 0.1.8; six cron role owners from the isolated 0.1.8 installation; one separate systemd tunnel remains while duplicate cron tunnel was removed; both Fabric child processes from the new managed slot; Fabric peer reports `ready` and full revision `51c37f1eac65951e15a5122b89f368aa6e18c1f5`. Local health checks passed; two test workers and idle queue in sampled status. The timed Runner-MCP rollback was disarmed after verification.
- **Open cross-boundary failure:** local Fabric `inspect_host()` and `build_operational_snapshot_provider()` execute successfully, but original-connector `fabric_host_inspect` reports `fabric_inspection_unavailable` and `fabric_operational_snapshot` returns an error. The local snapshot was `degraded=true` because relay evidence is `unknown` rather than a local crash. Distinguish package function, MCP registration, tool call, response schema, bridge session and connected-client delivery before applying a fix.
- **Provenance gate:** installed package version 0.1.8 is not a verified active Git source/digest (#669); doctor reports `active_revision_unavailable`, never substitute historical self-update revision. Fabric A6/A7 independent release authority remains outside the green checks.
- **Next safe diagnostic:** read-only compare peer tool names and first failure reason from the fixed client; add a regression; avoid restarting or granting extra permissions until cause is localized.

### 2026-10-14 — Source-confirmed reconnect contract mismatches (#681 / PR #683)

Read-only source inspection found two **independent** violations at `FabricBridgeClient._client()` before 0.1.9:

1. It supplied the full allow-list of optional Fabric capabilities without a reduced `required_tools` set. Generic `LocalMCPClient` then required every optional A6/probe/guest tool after stale-session generation verification, even when the legitimate Fabric peer intentionally omitted them.
2. It omitted `expected_component_id`, defaulting to `runner-mcp` while the Fabric agent correctly advertises `runner-fabric-agent-mcp`. A build-identity check on reconnect therefore rejects the genuine peer.

The 0.1.9 **source candidate** specifies the unconditional host-inspection/snapshot set as required and the exact Fabric component identity. The allowed capability names, protocol, interface-digest validation and stale unknown-effect non-replay remain unchanged. Synthetic negative tests are tracked in #683. This is not yet physical original-client acceptance, and the active operator host remains on Runner-MCP 0.1.8 until a separately qualified rollout.

### 2026-10-15 — Version-specific stage versus verified active route

- **Installed/serving now:** original-client `runner-mcp=0.1.8`; fixed peer `runner-fabric-agent-mcp` source revision `51c37f1e...`, handshake `ready`. Host-inspect and operational-snapshot original-route return paths are NOT qualified. Agent Bus relay remains unknown/degraded; normal test queue has two available workers in one snapshot.
- **Source available but not serving:** `0.1.9` fix for both Fabric reconnect contract mismatches merged as PR #683 / source `e7cb9162d686b5992b3862a4b61f85980cbdfbd4`. Green source CI/installer/attribution does not validate post-update connected-client return path. Do not write `0.1.9` as live topology before root activation, physical six-role evidence and client acceptance.
- **Release boundary:** standard self-update currently unready (`self_update_ready=false`), active artifact provenance #669 absent. A proposed operator-only fixed-commit stage plus separately armed independent systemd rollback is NOT physically executed. Public topology records this boundary only, no private machine coordinates or privileged scripts.

### 2026-10-16 — #669 offline artifact preflight, source-only PR #689

Candidate 0.1.11 compares an untrusted receipt, pinned wheel SHA-256, and complete Python-module inventory/digests. It returns offline_bytes_match or unverified; it MUST NEVER set active_build_provenance_verified=true.

- A receipt is not signed or a trusted serving-process witness. Matching self-declared bytes is an offline preflight only.
- Unlisted native extensions (.so/.pyd/.dll/.dylib), linked directories, incomplete manifests, malformed receipts and unsafe permissions fail closed.
- self-update-state.json is historical transaction data, never proof of the currently loaded wheel.
- A trusted builder manifest, immutable versioned environment, atomic private installer receipt, loaded-module generation binding, A6/A7 rollback and original-client ACK remain separate requirements.
- This draft source change neither mutates the serving 0.1.9 installation nor authorizes 0.1.11 release.
