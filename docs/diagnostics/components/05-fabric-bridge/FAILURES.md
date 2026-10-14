# 05-fabric-bridge — Runner-Fabric bridge en peer compatibility — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0002 | KNOWN | peer capability/interface | Local Fabric-agent process restart is healthy/PID-changing but required peer tools remain absent | process health, peer initialize compatibility, tool registration and private binding state are independent layers | explicit bridge preflight with protocol/interface/build/tool availability; never equate process health with capability readiness | Fleet A6 historical #509 |
| RMCP-F-0004 | RELATED | client interface | Server/peer capability is available but an already-open client cannot invoke it | client tool catalogue may predate the live capability | diagnose server registration vs client catalogue separately; refresh client/session rather than add duplicate proxy | repeated qualification/update handoffs |

Keep peer, local process and client-interface evidence as separate layers.

| RMCP-F-0028 / #681 | SOURCE HAZARD PROVEN / LIVE CAUSE OPEN | Fabric peer reconnect required-tool catalogue | On first same-session post-upgrade calls original bridge returns `fabric_inspection_unavailable` / snapshot tool error despite healthy peer and successful exact-slot local functions. Source `LocalMCPClient` requires entire `_FABRIC_TOOLS` on reconnect while preflight explicitly observes optional A6/synthetic tools absent; source mismatch is certain if reconnect reached, live root cause under qualification | separate mandatory and optional peer tools, preserve exact build/interface and no stale-call replay, synthetic restart/catalog/schema negatives and original-client proof | #681 / #590 / Fabric #942/#943 |
