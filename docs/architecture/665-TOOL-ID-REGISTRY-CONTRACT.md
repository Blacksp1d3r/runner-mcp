# #665 registry — immutable tool identity specification v1

Status: PROPOSED. Planning contract only, not a live protocol or approved assignment of IDs.

## Canonical keys
- `namespace`: fixed `com.aifordable.runner-mcp`, explicitly **not** an authentication token.
- `tool_id`: stable opaque ID assigned only by reviewed registry migration; ASCII `RMCP-[0-9]{6}` suggested format, numeric portion has no execution semantics. No generated ID may be inferred from alphabetical sort or Python hash().
- `tool_name`: exact registered MCP `tools/list` name; preserve original MCP compatibility.
- `contract_revision`: positive integer, increments for breaking schema/behavior/permission changes; previous revision remains bound to its original meaning.
- `input_schema_sha256` and `output_schema_sha256`: stable SHA256 over a defined canonical JSON schema serialization (deterministic sorted keys, compact separators, UTF-8, no NaN/Infinity). Schema equality does NOT imply equivalent permissions or implementation.
- `introduced_release`, optional `retired_release`; fixed unique version and immutable source/artefact fingerprints separately track packaging.
- `status`: active, deprecated, retired. A retired ID must NEVER be silently recycled.
- `permission_class`: reviewed permission intent, not a replacement for host/tenant authorization.

## Contract invariants
1. Registry key unique by (namespace, tool_id, contract_revision); name/ID mapping cannot silently change for an existing revision.
2. Every active actual MCP tool advertised by authenticated `tools/list` must correspond to exactly one approved active or deprecated registry entry and schema digest; no missing, extra, duplicate or dynamic alias admitted.
3. Unknown, missing, duplicated, reordered tool metadata must not cause automatic ID reassignment.
4. Signed/attested release artifact includes exact approved registry digest, build commit and wheel payload digest. Installed runtime evidence must independently confirm activated code and policy generation.
5. Never infer a tool's safety from its name or ID. `TOOL_DISABLED` is an explicit authorization decision; `UNKNOWN_TOOL` means absent, not automatically an older version.
6. Registry changes are reviewed migrations with immutable tombstones, version bump under #661/#663 and explicit compatibility tests #664.
7. Discovery or telemetry labels do not grant execution rights; dispatcher authorization remains #665-dispatcher and #642.

## Migration strategy
- Source baseline currently lists 95 tool names in pending PR #661. It does not capture every tool's full schema or verified active runtime; therefore do not mass-assign production IDs from it blindly.
- Stage a **candidate registry** generated from trusted reviewed source declarations; collect actual isolated `tools/list` schemas and determine stable IDs in a reviewed commit.
- Record manifest checksum and approved baseline; all future additions must allocate next never-used ID, not reuse gaps.
- Live old clients remain standard MCP consumers; optional identity metadata negotiated by #665-handshake. Do not deploy before A6/A7.

## Synthetic test vectors

| Test | Expected |
|---|---|
| Duplicate same ID with two names | Reject registry |
| One name mapped to two active IDs | Reject registry |
| ID recycled after retirement | Reject registry |
| Same ID/revision changed schema digest | Reject registry |
| New revision same name with supported prior revision | Permit only under explicit reviewed compatibility |
| Unknown ID or foreign namespace | Reject; no handler invocation |
| Same SemVer with different source SHA | Distinct build; fail exact-build matching |
| Registry includes 95 names, serving `tools/list` adds 96th unlisted alias | Reject attestation |
| Known tool disallowed by host policy | TOOL_DISABLED, zero side effect |
| Different tenant reports same failure | Separate alerts and history |

## Implementation gate and next handoff
The first source implementation should be a pure read-only registry validator with deterministic JSON and property tests. Do not modify `server.py` or active dispatcher yet. First ensure #661 version guard, #663 allocator and #664 contract semantics are merged/reconciled; assign unique shipping version and rerun exact-head CI. Claims and child STATE.md must be updated before code changes.
