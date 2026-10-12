# ADR-2026-10-12 — Legacy customer tool compatibility

Status: PROPOSED FOR OPERATOR REVIEW. Architecture only; not an active feature or deployment.
Parent: ADR-2026-10-12-UNIVERSAL-TOOLSET. Runner Fabric remains the authoritative control plane.

## Decision
All Runner-MCP releases share one canonical codebase and complete package-specific toolset. Customer installations may temporarily run older supported releases. New centrally deployed functionality must keep old published tool contracts compatible where safe. A new capability cannot run on an old binary that does not implement it. No host-specific package forks, magic fallback or perpetual support promise.

## Four separate versions
- Package: SemVer plus immutable source and wheel hash.
- Wire protocol: a supported authenticated protocol epoch, independently negotiated.
- Tool contract: name, schema, defaults, outputs, error/status semantics and permission scope.
- Activation policy: host/tenant/role enablement plus separately versioned policy digest.
Installed, registered, advertised, enabled, authorized and successfully callable are separate facts.

## Tool compatibility invariants
1. Existing supported tool names retain their established purpose, units, required inputs, default behavior, relied-upon outputs, error semantics and authorization boundaries. Compatible internal corrections and security hardening are allowed in a NEW package version.
2. Add optional inputs only when omission preserves old behavior; add output fields only when legacy consumers tolerate unknown keys. Breaking input/output/default/semantic changes require a new named contract such as archive_document_v2. Preserve archive_document as v1 for supported clients.
3. Unsafe legacy tools may be disabled immediately with SECURITY_BLOCKED and an upgrade path. Safety overrides indefinite compatibility.
4. Each newer universal wheel includes both supported old contracts and new capabilities, even on hosts where an old contract is disabled by policy. Disabled functions cannot cause side effects through aliases or indirect adapters.
5. No arbitrary shell, privilege escalation or unqualified alternate worker when a capability is missing.

## Negotiation and legacy routing
- Authenticate the actual serving instance; bind package/source/wheel identity, protocol epoch, published tool-contract schema hashes, policy generation, session generation, caller, nonce, expiry and request correlation.
- Fabric selects the intersection of the caller's requested contract and the instance's trusted advertised/supported contract plus host/tenant policy. Host rechecks permissions, leases, fencing and idempotency. Verify the original client result and ACK.
- Invalidate capability caches on process restart, policy change, update or reconnect.
- For old instances without a modern handshake, use a reviewed immutable legacy compatibility snapshot and a separately verified read-only identity bootstrap. Unknown identity or missing safe baseline yields UPGRADE_REQUIRED / UNTRUSTED_RUNTIME, never guessed rights.
- New client / old server: invoke an existing v1 contract if trusted. New v2 on v1-only server: UNSUPPORTED_TOOL_VERSION. Old client / new server: retain v1 behavior. Disabled: DISABLED_BY_POLICY.

## Support lifecycle
Older versions can remain interoperable only within a published supported-version window. Exact number of supported release trains and customer LTS duration requires operator/business approval. A security exception can require an earlier upgrade. Do not advertise an unlimited backward-compatibility SLA.

## Required proof
- Immutable snapshots for published tool schemas, defaults, outputs and permission semantics, not merely tool counts.
- CI rejects incompatible in-place tool contract changes; demands new tool ID for breaking changes.
- Tests: old client/new server, new client/old server, v1/v2 coexistence, unavailable tool, policy denial, replay, stale cache, wrong host, and no privileged fallback.
- A6/A7 independent rollback plus same-client catalogue and result ACK before fleet upgrades. No mass forced upgrade from unapproved CI.

Implementation status: DESIGN ONLY. No server protocol, tool compatibility gate, policy, host or deployment changed by this ADR.
