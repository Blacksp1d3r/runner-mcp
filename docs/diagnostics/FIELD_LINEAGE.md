## 2026-10-24 — Fabric GitHub Release metadata-only readiness

`fabric_release_assets_readiness(exact40hex)` → existing `FabricUpdateManager.release_assets_readiness` → original manager runtime/managed-launcher safety gate → fixed Runner-Fabric GitHub Release tag and Git tag ref metadata → `inspect_exact_release` validates exact source pin, asset names/counts, size and SHA-256 metadata → sanitized `source=github-release`, `state=ready`, `mutation_authorized=false`, `download_performed=false`, bounded audit event. On bad source/unsafe runtime/unqualified ref/digest metadata → `bounded_fabric_readiness_failure(source=github-release)`, `artifact_ready=false`. Neither result verifies bytes, independent signer, staging, actual serving module, previous-good rollback or permission to install. The distinct `fabric_update_readiness` retains GitHub Actions-only semantics; NO silent fallback to GitHub Releases. Regression: `tests/test_fabric_release_metadata_readiness.py` and `tests/test_fabric_update_readiness_unavailable.py`.

# Runner-MCP field/action lineage

For Runner-MCP, field-level lineage means tracing every public tool field or result field to the exact bounded authority that produced it.

## Required dimensions

| Dimension | Meaning |
|---|---|
| tool | MCP/public capability |
| semantic_input | caller-supplied bounded semantic field |
| validation | schema/allow-list/revision validator |
| trusted_source | private config, project registry, fixed catalogue, peer evidence, local state |
| policy | safety/approval/compatibility policy |
| executor | exact manager/component |
| state_write | private metadata/job/audit state, if any |
| external_edge | GitHub/Fabric/database/project/runtime edge, if any |
| result_field | sanitized public evidence |
| tests | narrowest proving tests |
| failures | linked stable failure IDs |

## Critical chains

`self_update(commit) -> commit validation -> known self-project -> source synchronizer -> bounded tests -> installer -> restart markers -> runtime_status`

`run_tests(project, suite) -> project registry -> test profile -> safety guard -> bounded subprocess -> job metadata -> redacted bounded result`

`Fabric proxy -> fixed allow-listed Fabric tool -> protocol/build/interface preflight -> peer call -> schema validation -> sanitized result`

`mailbox request -> strict protocol parser -> replay/fencing -> bounded capability dispatch -> durable result sink -> acknowledgement`

`deploy/migration/backup -> known project config -> approval/safety state -> fixed manager -> durable job/metadata -> bounded result`

A result field must never be treated as proof of an upstream fact that is not represented in its lineage.
