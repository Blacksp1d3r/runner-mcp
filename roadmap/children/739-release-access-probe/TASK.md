# #739 — first-host pinned read-only Release API access probe

Status: SOURCE / STANDALONE / NO HOST AUTHORITY.

Owner: Runner-MCP source lane (separate from active runtime Doctor #742).

## Bounded task

- A local operator can verify access to the single pinned private Fabric GitHub prerelease using an interactive short-lived, one-repository read token, without `gh`, installed new Runner-MCP, paths, network mutations or any asset downloads.
- Fixed API origin, repository and tag; no CLI parameters, proxy or HTTP redirect. Bound response and return only safe reason categories.
- Metadata `PASS_METADATA_READ` is **not** attestation, credential enrollment, binary integrity, release install authority or first-party target/original-client ACK.
- No private value, token, host identity, log or customer data may enter this repository.

## Acceptance

- Synthetic direct 200, HTTP 301/302/307/308 + 401/403/404/429, hostile redirect Location, proxy environment, missing/wrong prerelease, incorrect asset count, duplicate JSON keys, response size, interactive/non-interactive/argv denial, secret-safe outputs.
- Local isolated tests and exact PR-head CI: validation, attribution and clean Ubuntu. Source/branch merge only after green.
- Physical interactive check WAIT until owner supplies **locally** a bounded credential; no credential is requested here or stored.

## Out of scope / next child

- Bundle bytes download and digest validation, independent published digest trust, immutable local custody/replay denial, BOOTSTRAP.py preflight, operator install, relay CAS enrollment and original-client ACK remain #739/Fabric #1563 independent children.
