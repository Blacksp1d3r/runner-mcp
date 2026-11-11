# 12-diagnostics-audit — Safe diagnostics, audit, build identity en host integrity — roadmap

## Subcomponents
1. safe diagnostic categories
2. text redaction
3. audit append
4. build identity
5. HTTP trace context
6. runtime doctor projections
7. host integrity
8. operational snapshot projections

## Dependencies
Upstream: all components.
Downstream: none.

## Current implementation
safe_diagnostics.py; text_redaction.py; audit.py; build_identity.py; host_integrity.py; host_integrity_linux.py; http_middleware.py; server.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| topology/freshness hardening | ONGOING where relevant | component tests + upstream authority |
| authority expansion | BLOCKED unless separately designed/reviewed | security rules |

## Definition of done
The component can explain current state, source freshness/revision, authority, effect/evidence and recovery without exposing private deployment details.
