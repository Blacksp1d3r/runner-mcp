## Full Q7 manifest consistency (source-only)

`independently trusted source/asset roster still external -> compare exact Q7 33 metadata -> map[str, bytes] (caller's in-memory synthetics) -> all 33 length/hash -> bounded JSON and canonical COMMIT_SHA -> 29 wheel + bootstrap SUMS consistency -> result bundle_consistency_only`. No signature verification, wheel ZIP inspection, network fetch, filesystem persistence, host authority or original-client delivery ACK. A parsed bundle is NOT independently issued or executable.

## Independent Q7 roster structural comparison (source-only)

`externally trusted issuer/pin custody REQUIRED BUT NOT PROVIDED -> PinnedReleaseRoster as caller data -> strict 40hex source/ref and positive release ID -> exactly 33 safe unique id/name/length/sha256 tuples -> compare with ReleaseAdmission observed fields -> category-only MATCH_ONLY or constant denial`. No network, HTTP token, download, file, signature or original-client receipt. A caller MUST NOT populate trusted pins from same observed source and treat it as independent authority.

## #739 source byte helper (not active/private)

`separate independently trusted digest/size + exact numeric asset ID -> fixed GitHub REST API GET with bearer/no proxy/no redirect -> 200 OR one 302 to allowlisted HTTPS blob host -> NEW GET without Authorization/Cookie -> streamed <=64MiB and exact length/SHA256 -> IN-MEMORY bytes`. No local store, signature/key authority, release identity acceptance, asset materialization, bootstrap or ACK is part of this pure source function. A caller must never derive an allegedly independent pin from the same untrusted metadata.

## Pinned operator Release metadata read (#739)

`local interactive tty -> hidden short-lived owner-supplied token -> fixed api.github.com repository/tag GET (proxy off, redirect off, 8s, <=256 KiB) -> bounded 200/HTTP denial -> strict JSON tag/source/prerelease/33-count metadata check -> category-only PASS/WAIT`. This does not cross the actual downloadable asset or local storage boundary; trust in publisher/signature, host/install and ACK remain UNKNOWN.

# 13-artifact-mirror-custody — Artifact custody, repository mirrors en Fabric update artifacts — data lineage

## Core chain
`semantic action/status request -> fixed identity/config resolution -> freshness/precondition -> bounded operation/read -> private state or external edge -> sanitized result -> audit/diagnostic projection`

## Independent release-archive readiness
`zero-argument readiness -> private binding completeness -> private-directory checks -> real-mount check -> containment/symlink checks -> filesystem-device separation -> bounded readiness/reason -> audit`

This read-only chain performs no directory creation, permission change, mount, copy, restore, delete, network or subprocess action.

## Required lineage
Track stable component/action identity, source/current revision, freshness, authority decision, state transition, external edge result category, public projection and regression evidence.

## Physical state
Use DATA_STORE_MAP. Real deployment identifiers remain private.
