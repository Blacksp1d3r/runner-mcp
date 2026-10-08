# 10-service-lifecycle — Managed service lifecycle en autostart — roadmap

## Subcomponents
1. allow-listed service resolution
2. status
3. start/stop/restart
4. service journal
5. autostart registration
6. cron autostart
7. activation
8. restart convergence

## Dependencies
Upstream: 08-safety-approval-retention, private service allow-list/config.
Downstream: 11-tunnel-connectivity, 12-diagnostics-audit.

## Current implementation
service_manager.py; service_journal.py; autostart.py; cron_autostart.py; autostart_activation.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| topology/freshness hardening | ONGOING where relevant | component tests + upstream authority |
| authority expansion | BLOCKED unless separately designed/reviewed | security rules |

## Definition of done
The component can explain current state, source freshness/revision, authority, effect/evidence and recovery without exposing private deployment details.
