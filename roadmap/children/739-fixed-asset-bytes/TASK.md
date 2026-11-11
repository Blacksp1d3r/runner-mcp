# #739 — fixed GitHub Release asset ID byte integrity helper

Status: SOURCE_ONLY / INERT HELPER. Parent #739 stays open.

Scope: from an authenticated fixed Runner-Fabric GitHub API `/releases/assets/<numeric-id>`, accept exactly direct 200 or ONE HTTPS 302 to `release-assets.githubusercontent.com`; never follow another redirect, send credentials off API, proxy, accept URL/path parameters or write files. Bounded up to 64 MiB with exact externally pinned length/SHA256. Any error returns only one fixed category. No installation or download invocation is wired to MCP/public tools.

Acceptance: synthetic HTTP direct200+302 with exact pin and no bearer leakage; wrong host/scheme/port/userinfo/query misrouting, 401/403/404/429, malformed redirection, wrong digest, shorter/longer stream, declared length mismatch, bad asset IDs, proxy+redirect denied; no real network or private bearer. CI exact-head required.

Hard gate: independently trusted release identity, asset roster and digest values (not merely the same GitHub metadata), signed BUNDLE.json/COMMIT_SHA/SHA256SUMS, total 33/33, rootless atomic fsync-protected local custody and replay-denial, operator/supervisor approval, host attestation and original-client ACK are separate and NOT proved by this helper.
