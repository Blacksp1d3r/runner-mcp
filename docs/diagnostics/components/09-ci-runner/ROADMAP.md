# 09-ci-runner — CI-runner lifecycle en guest isolation — roadmap

## Subcomponents
1. runner enrollment
2. GitHub registration
3. guest enrollment
4. Fabric transport
5. secret handoff
6. runner lifecycle
7. cron/supervisor
8. status/start/stop

## Dependencies
Upstream: 05-fabric-bridge, 08-safety-approval-retention, fixed GitHub runner authority.
Downstream: 12-diagnostics-audit.

## Current implementation
ci_runner_enrollment.py; ci_runner_github.py; ci_runner_guest_enrollment.py; ci_runner_guest_fabric_transport.py; ci_runner_guest_github.py; ci_runner_lifecycle.py; ci_runner_secret_handoff.py; ci_runner_supervisor.py; ci_runner_cron.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| topology/freshness hardening | ONGOING where relevant | component tests + upstream authority |
| authority expansion | BLOCKED unless separately designed/reviewed | security rules |

## Definition of done
The component can explain current state, source freshness/revision, authority, effect/evidence and recovery without exposing private deployment details.
