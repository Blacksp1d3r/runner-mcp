# 05-fabric-bridge — Runner-Fabric bridge en peer compatibility — data lineage

## Core chain
`bounded request -> exact source/current-state lookup -> policy/approval/preflight -> executor -> durable/private effect or peer call -> validation -> sanitized result/audit`

## Diagnostic keys
Track exact project/capability/operation identity, source or peer revision, request fingerprint where defined, current state revision, policy/approval decision, job/evidence identity, result category and recovery relationship.

## Physical state
See global DATA_STORE_MAP. Private path/endpoint/service identity is intentionally not represented here.

## 2026-10-23 — fixed original issuer/ACK diagnostic lineage

The original issuer publisher is a distinct authenticated **machine controller**, not a worker, a human login or the Fabric bridge handshake. Trace separately: original serving process/source and parent -> managed v2 slot receipt -> actual installed wheel/RECORD/import -> independently recoverable launcher -> private issuer mode+credential custody -> exact relay requester -> fixed request ID and target -> positive worker claim/generation -> terminal result payload/digest -> same-original authenticated durable ACK + readback. Never promote a partial edge to end-to-end green. Registered `runner:control` in the relay without process-private binding remains **BLOCKED**; connected `0.1.38` reports provenance NULL and cannot load the merged v0.1.84 optional-file source by assumption. Receipt schema uses `projectWheelSha256` and `bundleSumsSha256`; querying `wheelSha256` causes a false diagnostic negative. The owner's subsequent read-only receipt *field presence/syntax* PASS is not a binary rehash or rollback qualification. See existing #341 TASK/STATE and the canonical upstream Infrastructure/Credential Authority; do not place physical identifiers or secrets here.
