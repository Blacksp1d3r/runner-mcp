# Runner-MCP failure index

This index complements the existing failure-record issue template.

| Failure ID | Component | Status | Symptom/risk | Root cause / state | Prevention / next guard | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0001 | tunnel/connectivity + end-to-end status | KNOWN | local test queue can be idle while the first-party path is still busy | local queue state was insufficient as end-to-end authority | operational snapshot must represent upstream relay/Agent-Bus/Fabric layers and unknown states | #269 |
| RMCP-F-0002 | Fabric bridge / qualification | KNOWN | a healthy local restart can coexist with absent expected peer tools | peer tool/interface/config lifecycle may be incomplete or stale independently of process health | explicit peer preflight + interface/build/protocol evidence; do not equate PID health with capability availability | Fleet A6 track / historical #509 |
| RMCP-F-0003 | source/credential boundary | KNOWN | source preflight can fail although runtime itself is healthy | repository authorization/source reachability is independent of runtime health | source preflight and credential-role/topology resolution remain separate from runtime status | historical #417 |
| RMCP-F-0004 | client/tool catalogue | KNOWN | server capability may be live while an already-open client session cannot call it | client tool schema/catalogue loaded before server capability existed | treat catalogue refresh as client compatibility state; do not duplicate server tools as workaround | multiple qualification/update handoffs |

Closed/known failures remain here after fixes. Do not include private host/path/token values.
