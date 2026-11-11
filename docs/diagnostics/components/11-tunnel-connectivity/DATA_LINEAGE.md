# 11-tunnel-connectivity — Tunnel, relay en connectivity readiness — data lineage

## Core chain
`semantic action/status request -> fixed identity/config resolution -> freshness/precondition -> bounded operation/read -> private state or external edge -> sanitized result -> audit/diagnostic projection`

## Required lineage
Track stable component/action identity, source/current revision, freshness, authority decision, state transition, external edge result category, public projection and regression evidence.

## Physical state
Use DATA_STORE_MAP. Real deployment identifiers remain private.

## 2026-10-09 evidence precedence and connector separation

The existing pure readiness classifier orders trusted evidence as private restart configuration -> managed process observed -> local MCP health -> control-plane authentication -> external topology/uniqueness and Fabric A3 synthetic probe. Each step is independent; an observed healthy local server is **not** external ChatGPT connectivity. No local instance ID or stale timestamp confers external uniqueness.

- #597 validates exact boolean types for all five `TunnelReadinessEvidence` gates. A string `"false"` must not advance this chain. Current code PR requires exact-head CI before adoption.
- #598 ensures explicit current `degraded/error/failed/stopped` MCP health cannot be overridden by an earlier successful startup probe; the historical startup result does not supersede an explicit negative status.
- #599 flags `control-plane.details.last_success`: the current projector accepts any nonblank string as authentication evidence without age verification. Proposed future qualification must inspect actual poll cadence and add a deterministic timestamp freshness gate; do not invent one.
- #590 is the current ChatGPT connector internal-tool failure. #595 green merged only establishes local MCP dispatch/serialization. The exact first failing live edge remains unproved.
- Historical #333 documents an earlier stopped tunnel client and a later 2026-10-08 operational tunnel with a distinct `tunnel_topology_refresh` diagnostic failure. That latter bounded-reason gap was already closed by #523/#524; do not build a duplicate workaround.

No private tunnel coordinates, credentials, process names, raw health payloads or customer data are authorized for public GitHub documentation.
