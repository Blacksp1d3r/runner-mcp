# 07-deploy-migrate-backup — Deployment, migration en database backup/restore — data lineage

## Core chain
`bounded request -> exact source/current-state lookup -> policy/approval/preflight -> executor -> durable/private effect or peer call -> validation -> sanitized result/audit`

## Diagnostic keys
Track exact project/capability/operation identity, source or peer revision, request fingerprint where defined, current state revision, policy/approval decision, job/evidence identity, result category and recovery relationship.

## Physical state
See global DATA_STORE_MAP. Private path/endpoint/service identity is intentionally not represented here.
