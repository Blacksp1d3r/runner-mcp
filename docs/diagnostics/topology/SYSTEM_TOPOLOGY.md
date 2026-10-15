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

## 2026-10-15 — Staged-only Runner-MCP 0.1.9; independent rollback not yet armed

- Operator's exact-source staged receipt: Runner-MCP 0.1.9 source `e7cb9162d686b5992b3862a4b61f85980cbdfbd4` with locally built wheel SHA-256 `92c9ab6cc2731cbf40a361f1133cc79908750ebd44553497b9afbc41977b0fbd` and 100/100 Python modules source/wheel/installed identical. This is **offline staging**, not process activation.
- The original ChatGPT connector still reports active 0.1.8, self-update not ready, and fixed Fabric peer `ready` on `51c37f1eac65951e15a5122b89f368aa6e18c1f5`. Six cron roles and single independent tunnel remain the accepted live route.
- Independent root-owned rollback script and persistent one-shot systemd deadline are the **next operator-controlled preparation task**, not yet installed or observed. Never perform cutover without timer-active, pre-activation rollback dry-run, exact old/candidate cron, independent old executable and symlink restore, and safe activation window. Never treat CI source merge #683 as live acceptance of `fabric_host_inspect`/`fabric_operational_snapshot`.
- Once promoted, topology must be revised from staging to verified serving generation only after exact original-client, process-lock, tunnel, peer tool and rollback-confirmation evidence. See #681 and #669. No private host locations or credentials belong here.

### 2026-10-15 — Rollback ARMED but cutover NOT ACTIVATED (operator receipt)

Operator independently observed successful pre-activation no-op recovery probe and a root-controlled systemd calendar rollback timer enabled and active. The staged 0.1.9 wheel and source are unchanged; serving Runner-MCP remains 0.1.8 and the separate tunnel remains active. The future cutover script's expected rollback-source digest matched the preparer's source, with activation guarded on timer liveness, minimum window, exact six lockholding generations and staged wheel checksum. **Do not promote this to an active release node before six-role runtime + original connector evidence**, and do not mark #681 resolved before the host inspection and operational snapshot pass end to end. No private addresses/tunnel values are recorded here.
