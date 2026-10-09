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

## 2026-10-09 — independent safety and CI admission state

- #584 is **BLOCKED** on actual disposable self-hosted CI runner admission evidence. Draft #589 already owns docs/checklist; #387 owns isolated dispatch qualification and #388 owns preconfigured enrollment. Do not duplicate or reroute untrusted PR validation to privileged/shared hosts.
- #591 is a bounded read-only-to-host side effect fix in `ci_runner_secret_handoff.reap_expired`: scan at most 4097 directory entries, refuse above 4096 before deleting anything, preserve 0700 root/0600 record ownership/TTL rules. Synthetic tests check exact boundary and over-limit refusal. This **does not** qualify #584 isolation or enroll a runner; exact-head CI required before merge.
- Runner-MCP connector read tools `runtime_status`, `runtime_doctor`, `list_projects`, `worker_status` currently all yield generic internal tool failures. Dedicated #590 tracks the transport/runtime boundary; no health/capacity/isolation conclusions can be drawn. Avoid repetitive probes or unrestricted shell fallback.
- Performance optimization is a separate stream: Faster baseline #514, hosted shadow labs #458 and broader shadow benchmarks; OCR qualifying work was historical and must not be repeated. Prior test heads for #514/#537/#458 show green CI, but their PRs remain owned/open and should not be merged casually across agents.
