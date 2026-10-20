# Host-local tool admission and shared MCP catalogue — source contract

Operator binding 2026-10-10: **every managed Runner-MCP instance runs the
same exact promoted secure code/tool-schema release**, even if a worker does
not need all tools. A tool may be *advertised* everywhere but must answer
`HOST_TOOL_NOT_PERMITTED` when its local host/capability is unauthorized.
Never silently remove a tool to represent denied execution. Avoid sending
the call to a second, more privileged server.

`host_tool_admission.py` provides the bounded deterministic fail-closed
**policy decision** for that behavior. It compares the expected exact
registered tool set, source SHA, interface schema digest, and expiring
host-local granted-tool set. Missing/stale/mismatched facts or a tool absent
from the qualified catalogue return a fixed denial. A grant alone never
overrides existing OperatorSafetyGuard, Fabric admission/lease/fencing,
operator stop or high-risk approvals.

## What is still required to use this at runtime

- First-party Fabric must independently resolve service identity from the
  canonical infrastructure registry (not a client hostname/claim).
- It must verify the permitted tool set and release artifact provenance
  with a protected service-local binding, expiry and anti-replay controls.
- The *actual executing* MCP process must report its own loaded source/
  schema generation. Installed source files and an old `0.1.3` package
  version are insufficient.
- The MCP dispatch middleware/handlers must call this local decision
  before *any side effect* and emit a sanitized audited structured denial,
  preserving tool names/input-output schemas.
- Positive host admission alone is not authorization to perform a high-risk
  operation. Existing safety, approval and Fabric lease checks still apply.
- Add live negative-path tests for the five OCR-only capabilities on the
  primary host and positive authorized lab tests, then qualify that each
  response returns through the matching connected tunnel with a fixed
  request correlation/ACK.
- Only after separately qualified A6 off-target journal and A7 independent
  networkless rollback is the full-fleet upgrade safe for live control hosts.

This PR is SOURCE-ONLY: it does not instantiate trusted host policy, change
live MCP registration, grant any host new permissions, restart servers or
resolve stale connector tool catalogues (#540). The two intentionally
separate local Runner-MCP servers remain unmodified, and Runner-Fabric is
still the *single* fleet control plane.

Tracking: Runner-MCP #341/#540/#590, Fabric #924/#942/#943, Fabric merged
#1438/#1439. Runner-MCP PR #640 instruction-policy parity remains OPEN.
