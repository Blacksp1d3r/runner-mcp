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
