# #590 — Local MCP HTTP bearer egress child state

- owner: Runner-MCP communication lane, bounded deferred after #650
- status: UNCLAIMED
- risk_class: SOURCE_GAP_DISCOVERED_NOT_LIVE_INCIDENT_PROVEN
- current_defect: standard urllib.request.urlopen follows environment proxies/HTTP redirects despite initial loopback URL validation
- source_change: NOT_STARTED
- PR: NONE
- exact_head_ci: NONE
- source_landing_dependency: Runner-MCP #650 exact CI/merge first, because it modifies the same `bridge_mcp_executor.py`
- transport_precedent: Runner-Fabric #1446 MERGED source only
- live_host_or_tunnel_mutations: NONE
- blocker: Fabric A6 #942 / A7 #943 live fleet safety; #590 installed process/route proof unknown
- #381 Claude dispatch: NO_DISPATCH

## Next safe action
Reconcile exact current main and #650. If #650 source merged, implement the fixed per-client no-proxy/no-redirect opener as a separate bounded child branch; update old synthetic monkeypatches through the one transport seam. Run exact-head CI with hostile env/redirect cases. Preserve host allowlist, #650 unknown-effects classification and mandatory build/schema reconnect. Avoid broad network/tool side effects.

## Failure Museum
Pending evidence-based SOURCE finding. Never claim observed bearer exfiltration or physical tunnel redirect; only default urllib behavior is verified by source construction and Fabric #1446 precedent.
