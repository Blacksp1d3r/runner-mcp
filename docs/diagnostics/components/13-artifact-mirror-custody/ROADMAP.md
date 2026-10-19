## 2026-10-19 — source-only asset byte integrity child #739

Inert fixed release asset REST numeric-ID verifier, direct HTTP 200 or narrowly admitted official HTTPS 302, no bearer onward, bounded 64 MiB/asset and independently supplied SHA256; 33 isolated synthetic tests PASS, production unavailable/CI pending. This is separate from #743 metadata visibility. Physical protected custody and 33/33 pinned signatures/rollback remain external gates.

## 2026-10-19 — first-host pinned Release access (#739)

Distinct source-only standalone read-only metadata access prerequisite (candidate 0.1.41, 33 local synthetic regressions) precedes any protected bytes importer. It cannot authorize or perform downloads, changes to custody or host. Exact-head CI and host-private original-client read remain pending; #739 parent OPEN. Do not confuse API visibility with integrity, provider identity or release activation.

# 13-artifact-mirror-custody — Artifact custody, repository mirrors en Fabric update artifacts — roadmap

## Subcomponents
1. content-addressed custody
2. digest/size verification
3. repository inventory
4. mirror activation
5. mirror reconcile/readiness
6. Fabric update bundle custody
7. artifact freshness/retention
8. independent release-archive volume readiness

## Dependencies
Upstream: 02-project-source, private fixed custody/mirror config.
Downstream: 01-runtime-self-update, 06-qualification-bootstrap, 07-deploy-migrate-backup.

## Current implementation
artifact_custody.py; fabric_repository_mirrors.py; fabric_repository_mirror_activation.py; fabric_update.py; fabric_release_archive_mirror_readiness.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| topology/freshness hardening | ONGOING where relevant | component tests + upstream authority |
| independent release-archive volume readiness | ACTIVE | #585 / #586 |
| authority expansion | BLOCKED unless separately designed/reviewed | security rules |

## Definition of done
The component can explain current state, source freshness/revision, authority, effect/evidence and recovery without exposing private deployment details.
