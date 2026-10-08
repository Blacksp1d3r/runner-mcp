# 10-service-lifecycle — Managed service lifecycle en autostart — data lineage

## Core chain
`semantic action/status request -> fixed identity/config resolution -> freshness/precondition -> bounded operation/read -> private state or external edge -> sanitized result -> audit/diagnostic projection`

## Required lineage
Track stable component/action identity, source/current revision, freshness, authority decision, state transition, external edge result category, public projection and regression evidence.

## Physical state
Use DATA_STORE_MAP. Real deployment identifiers remain private.
