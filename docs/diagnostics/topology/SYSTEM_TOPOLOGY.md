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
