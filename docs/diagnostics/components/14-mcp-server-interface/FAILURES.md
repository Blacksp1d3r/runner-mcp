# 14-mcp-server-interface — MCP server, tool catalogue en public interface — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0004 | KNOWN | client catalogue/interface | Server capability is live but an already-open client cannot call it | client tool catalogue/schema was loaded before the server capability became available | distinguish runtime/tool-registration state from client-catalogue state; refresh client/session; never add duplicate proxy as workaround | historical qualification/update handoffs |

| RMCP-MCP-0005 | OPEN/LIVE UNLOCATED | client/catalog/transport vs installed runtime | Doctor now returns old 12-check WARN (0 failed, 3 warnings), while runtime_status and build_identity failed generically through connected client | Current main has at least three additional doctor checks; source-only #627/#629 correct two potential opaque error paths, **not** proof of active installed version or correct tunnel return route | Exact-source/catalog/session plus private read-only ingress and response-delivery correlation; no speculative restarts or broad-shell bypass | #590 / PR #627 / PR #629 |

| RMCP-MCP-0005 / 2026-10-10 reconfirmed | OPEN/LIVE UNLOCATED | partial read-only tool dispatch | `list_projects`, `queue_status`, `safety_status`, `project_capabilities` return structured; `project_status`, `build_identity`, `worker_status` and mirror admission fail; doctor has only 12 checks | See [bounded matrix](../../CONNECTOR_PROBE_MATRIX_2026-10-10.md); mixed success constrains diagnosis but still does not prove same target runtime/client route | Approved opaque-ID ingress → dispatch → response-delivery correlation; separately prove build/catalogue generation, no blind restart | #590 / #634 |

Use the repository failure-record template for a new recurrence with concrete bounded evidence.

## RMCP-MCP-0005 — 2026-10-10 operator-verified catalogue split and route evidence

Status: **OPEN / FIRST FAILED EDGE UNKNOWN**. This is a recurrence of the existing connector failure, not a confirmed duplicate response or a newly discovered second server. See #590 and the 2026-10-10 bounded probe matrix.

- Two **intentionally distinct** Runner-MCP installations, registered in the canonical private infrastructure authority, were compared using installed `server.py` AST tool declarations under their respective service identities. The primary-control installation had 63 declarations; the worker/lab installation had 68. All 63 common names matched; the five additional lab declarations were the fixed Bewind OCR qualification tools. Source SHA-256 digests differed. **This is source-declaration evidence only**, not an independently authenticated live MCP `tools/list` catalogue or exact input-schema digest.
- The primary-control tunnel was healthy at loopback readiness; dispatcher had 71 completions, response delivery had 71 accepted HTTP-200 results, zero retries/terminal failures, and local queue 71 enqueued/dequeued. Immediately after one connected `runtime_status` call returned an opaque internal client error, those counters remained **71/71**. The earliest failing edge remains **UNKNOWN**: client/catalogue/admission, alternate route or failure before counted dispatch are all possible. Historical accepted responses do not prove acceptance of that failed request.
- MCP health reported `unknown/not_observed` with `same_child_evidence_unavailable`. That can be a transport evidence limitation for HTTP; it is **not** proof of a misrouted or duplicate server.
- Root cause is **not established**. Avoid repeating the already-known two-host discovery, speculative tunnel changes, forced restarts or promoting different physical hosts into one unrestricted runtime.
- Operator's required end state: **one versioned Runner-MCP source distribution and tool interface contract across hosts**, with independently authenticated per-host/per-capability admission. An installed/advertised tool that is not authorized on the current host should return a fixed, sanitized **permission denial** (for example `HOST_TOOL_NOT_PERMITTED`) rather than accidentally executing or leaking a private configuration error. Tool discovery, tool availability and mutation authority remain distinct. Fail closed when host binding/topology is missing or stale; never accept client-supplied role/hostname as authority. Higher-risk Fabric lease/fencing and operator-stop checks must still run even when host allows the capability.
- Acceptance requires both hosts' independently verified runtime build identities, exact `tools/list` names **and schemas**, host-scoped negative tests for all five OCR-only capabilities, one authorized known-good and one failing request correlated through the first-party inbound→dispatch→response-delivery→client path, and a durable local database record with verified write/read-back. **No local authoritative database write has been verified**; GitHub issue/docs are not a substitute.

Next action: qualify a first-party bounded incident evidence `record/read` connector to the operator's own database, not arbitrary SQL or shell. Prefer local durable storage and nightly verified backup; GitHub only for source-level regression/failure knowledge.

### RMCP-MCP-0005 — 2026-10-10 mitigations, NOT resolved

Operator-mandated exact security release parity and host-local denial:
Runner-MCP PR #641 (`4e32a260`) merged the source-only
`host_tool_admission.py` decision contract and adversarial tests. A tool
that is in the shared catalog but not granted on a host should yield
`HOST_TOOL_NOT_PERMITTED`, including stale or unknown policy/build/schema.
This is **not yet wired into MCP dispatch**, and no installed host has been
upgraded or authoritatively requalified from these tests. Runtime admission
integration/audit and all-host positive/negative tool-path proof are tracked
under Runner-MCP #642; previous docs PR #640 remains OPEN.

Fabric A7 #943 was restored to OPEN after erroneous completion from source
work. Merged Fabric #1443/#1444/#1445 cover offline watchdog intent, protected
prior-wheel escrow and an isolated synthetic disconnected recovery path, not
actual self-hosted supervisor/restore, reboot or real return ACK. A6 #942
off-target physical evidence remains OPEN. No source-only success resolves
opaque connected `runtime_status` failure #590 or stale catalog issue #540.

### RMCP-MCP-0005 / Q7-20261010 — generic coding qualification error hides safe blocker

Observed on currently connected Runner-MCP source revision
`a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`: fixed
`fabric_coding_availability_qualify` returned an opaque MCP/tool error, so
no valid Q7 state (WAIT/OPERATOR_REQUIRED/BLOCKED) or session/worker
authorization can be claimed. Separate successful `runtime_doctor` exposed
`fabric_continuity_status_configuration_unavailable` and worker qualification
readiness unavailable; intermittently successful Fabric snapshot showed
agent-bus.relay `evidence-unavailable`, execution/mutation disabled.
The continuity configuration warning belongs to source/CI continuity;
it is **not proven to cause** the missing Agent Bus relay evidence.
Neither check demonstrates a failed Claude OAuth subscription.

Corrective source-only Runner-MCP #643 merged as `edbe8a78`: sanitized
`fabric_coding_availability_preflight()` distinguishes operator stop,
unqualified Fabric launcher and missing private Q7 binding without invoking
Claude or revealing sensitive values. Successful preflight means ONLY
attemptability, never READY or dispatch. Fabric #1446 merged `6b308156`:
reject HTTP redirects and environment proxies before bearer-bound coding
loopback MCP requests. Both commits passed exact-head CI; they are NOT
installed on the old control host.

Operational status: **OPEN/NO_DISPATCH**. To close: correct-host rootless
Claude #370/#381 qualification, authenticated Q7 loopback #972, durable Fabric
issuer+lease/fencing #1398/#1400, independent A6/A7 #942/#943 safe fleet
updates, exact active process/runtime/catalogue and real correlatable ACK.
Do not infer there is no Claude worker, install a second provider adapter,
enable paid API fallback, claim credentials are expired or restart the tunnel
from a sanitized generic error.
