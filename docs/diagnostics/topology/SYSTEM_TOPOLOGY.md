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
