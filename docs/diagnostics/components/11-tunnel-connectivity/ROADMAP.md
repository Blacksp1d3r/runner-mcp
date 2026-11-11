# 11-tunnel-connectivity — Tunnel, relay en connectivity readiness — roadmap

## Subcomponents
1. config readiness
2. managed runtime/process
3. local health evidence
4. topology evidence
5. heartbeat/freshness
6. end-to-end readiness
7. relay/control path

## Dependencies
Upstream: 10-service-lifecycle, fixed private tunnel configuration, canonical infrastructure authority.
Downstream: 04-mailbox-watchers, 05-fabric-bridge, 12-diagnostics-audit.

## Current implementation
tunnel_config_readiness.py; tunnel_health_evidence.py; tunnel_readiness.py; tunnel_runtime.py; tunnel_topology.py; tunnel_topology_heartbeat.py; tunnel_topology_refresh.py; aifordable_relay.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| topology/freshness hardening | ONGOING where relevant | component tests + upstream authority |
| authority expansion | BLOCKED unless separately designed/reviewed | security rules |

## Definition of done
The component can explain current state, source freshness/revision, authority, effect/evidence and recovery without exposing private deployment details.
