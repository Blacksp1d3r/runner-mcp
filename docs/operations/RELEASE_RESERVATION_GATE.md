# Runner-MCP #662 — concurrent source release admission

Status: DRAFT source-only candidate 0.1.45; not a deployed release.

The new CI job uses existing read-only GitHub API permissions and an exact PR synthetic merge. It checks current main SHA/version, expected PR base and head, open merge-eligible PR version metadata, duplicate reservations, strictly the next patch release, and postchecks main freshness. Documentation-only PRs skip reservation. Unknown API/metadata/page overflow or stale source evidence cause WAIT/FAIL. It never updates another PR branch, generates credentials, publishes artifacts or activates a host.

A passing CI result is still **not** an atomic version lock. Enforce branch protection making Release reservation admission required, require the PR be current with main OR a merge queue that recomputes the check per final merge, and serialize main merges under one release steward. Without independently verified GitHub policy configuration, treat this as an advisory preflight rather than guaranteed conflict prevention. This source PR should remain draft and correctly WAIT until the owner merges 0.1.42, 0.1.43 and 0.1.44 ahead of candidate 0.1.45; no one may jump other feature owners by changing their reserved versions.

Dependencies: release conveyor #662, canonical cross-project coordination Runner-Fabric #924, AIfordable #609, provenance #669 and PRs #743/#745/#750. GitHub source merge never certifies the installed Runner-MCP or Agent Bus. Preserve historical self-update state and actual current 0.1.38 diagnostic failures.

## Same-version coordination and freshness

Two READY PRs that propose the same next patch do not have to deadlock each other. The lower numbered PR has deterministic first priority; the other stays WAIT/rebases. An explicit release steward can change priority by moving the earlier PR back to draft, closing it or changing its candidate source and rerunning checks. Before and after inventory the checker independently re-reads the current candidate PR open/draft/base/head from GitHub, so an event from an obsolete head does not grant even provisional admission. Incomplete inventory and duplicate PR IDs fail closed. This priority rule is not an atomic queue and does not replace required checks + merge serialization.
