# Older customer tool contract compatibility — TASK

Status: DESIGN PROPOSED. API contracts owner: Runner-MCP; routing/admission: Runner Fabric.
Canonical design: docs/architecture/ADR-2026-10-12-LEGACY-TOOL-CONTRACTS.md.

## Build children
1. Extract verified published tool contract snapshots for each supported legacy release: names, required/optional input fields, defaults, outputs, statuses and authorization semantics. Version snapshots immutably; source-tool count is NOT contract proof.
2. Implement CI contract comparator. Prevent incompatible changes under a current v1 tool name; create a separate v2 name and keep v1 while safe and supported.
3. Add authenticated read-only capability/version handshake and reviewed legacy compatibility mapping. Cache is bound to serving host, build, policy version and session generation.
4. Fabric-owned routing selects only the mutually supported and authorized tool contract. New function requested on an old binary -> UNSUPPORTED_TOOL_VERSION, not fake successful fallback.
5. Create a test matrix for old/new clients and servers, v1/v2 migration, schema drift, policy-disabled actions, wrong tenant/host, replay and disconnected/expired clients. Prove no unauthorized side effects.
6. Agree customer/LTS support window and security exceptions before marketing compatibility. Track controlled rollout and upgrade warnings without automatically upgrading unapproved customer hosts.

## Gates
Runner-MCP #662 version conveyor, #590 communication, #341 recovery; Fabric #942 A6, #943 A7 and AIfordable #428 runtime authority. No live update, no new generic execution permissions.
Task acceptance: cross-version old tool behavior proven with immutable fixtures; unknown/unsupported tools blocked safely; mixed-version scenario attested through the original client.
