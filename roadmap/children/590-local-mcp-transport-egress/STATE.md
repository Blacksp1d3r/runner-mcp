# #590 — Local MCP HTTP bearer egress child state

- owner: Runner-MCP communication lane, bounded deferred after #650
- status: COMPLETE_SOURCE_ONLY; LIVE_ACCEPTANCE_BLOCKED
- risk_class: SOURCE_GAP_DISCOVERED_NOT_LIVE_INCIDENT_PROVEN
- current_defect: standard urllib.request.urlopen follows environment proxies/HTTP redirects despite initial loopback URL validation; validated offline via standard-library redirect_request source showing original Authorization header retained except Content-Length/Content-Type and default opener having both ProxyHandler and HTTPRedirectHandler
- source_change: MERGED_SOURCE_ONLY
- PR: #651 MERGED
- exact_head_ci: reviewed HEAD d588c72619fc277d8423b680f473c8d62e3c992a; commit attribution 38086367280 SUCCESS; full validation 38086367281 SUCCESS (Ruff, 2813 pytest, built release artifact, clean demo)
- source_landing_dependency: Runner-MCP #650 MERGED 8608ddde46f228d045d64189f12e7464a1919fb9; branch based on post-#650 main
- transport_precedent: Runner-Fabric #1446 MERGED source only
- live_host_or_tunnel_mutations: NONE
- blocker: Fabric A6 #942 / A7 #943 live fleet safety; #590 installed process/route proof unknown
- #381 Claude dispatch: NO_DISPATCH

- squash_merge: 68093ab85bee293a8cc7616340d2893d5e4c24a0

## Next safe action
PR #651 source merge verified green with 2813 pytest. Next **operational** #590: independently approved A6 off-target update journal + A7 disconnected local rollback proof, then qualified live exact active build/client catalogue and ingress→response-delivery correlation; no tunnel guessing. Closed source risk does not imply active runtime uses new opener.

## Verified offline source detail (2026-10-10)

Python stdlib `urllib.request.HTTPRedirectHandler.redirect_request` on 301/302/303 POST builds a new GET `Request` with `newheaders = {k: v for k, v in req.headers.items() if k.lower() not in ("content-length", "content-type")}`; Authorization is **not** excluded. A default `urllib.request.build_opener()` includes both `ProxyHandler` and `HTTPRedirectHandler`. This confirms a source transport egress risk when an intermediary sends redirect or proxy environment settings are malicious. This is an offline standard-library inspection, **not** proof an actual remote server redirected, that a token left the host or any runtime session is compromised. Follow Fabric #1446 safe fixed opener/negative-tests precedent.

## Failure Museum
Pending evidence-based SOURCE finding. Never claim observed bearer exfiltration or physical tunnel redirect; only default urllib behavior is verified by source construction and Fabric #1446 precedent.
