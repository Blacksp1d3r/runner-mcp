# #739 — pinned Release access probe state

Status: IMPLEMENTED_SOURCE_CANDIDATE / NOT DEPLOYED / CI_PENDING.

Branch: `feat/739-release-metadata-access-probe-20261019`, stacked on open #742 (runtime Doctor, unrelated files). Independent issue #739 has no competing PR observed when claimed on 2026-10-19.

Files: `scripts/fabric_release_access_probe.py`, `tests/test_fabric_release_access_probe.py`, `docs/operations/FABRIC_RELEASE_ACCESS_PROBE.md`.

Synthetic local test: 39/39 green on isolated Python 3.13 environment; `compileall` green. Ruff/full repository validation and GitHub exact-head CI are separate required gates, **not yet proven**.

True original-client release read: UNKNOWN / NOT ATTEMPTED. Host token and private first-host physical admission: WAIT. No real bearer generated, no asset bytes downloaded, no installation, relay or service mutation.

Next: validate exact branch head; if green merge via normal rules after stacked dependency #742, update this state. Independently scope a future 33/33 verified release-bytes importer with atomic owner-only custody and fail-closed host rollback check. Do not confuse access PASS with bundle authority.

Preventive RMCP-F-0047: HTTP Content-Length missing may be acceptable, but when present a valid positive bounded declaration MUST equal received bytes; tested malformed/missing and truncated length with synthetic fake HTTP. Actual live incident NOT observed.
