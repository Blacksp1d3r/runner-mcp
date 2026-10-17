# Fabric GitHub Release assets — metadata-only first-party admission

Tracking: Fabric #972, AIfordable #370, Runner-MCP #381 and existing Runner-MCP `FabricUpdateManager`.

## Why

The Q7 Fabric wheelhouse successfully built and passed clean offline Q7 tests and simulated rollback, but the old `Control-plane update bundle` Actions artifact upload hit the **account-wide storage quota**. Fabric's new GitHub Release assets producer published the original tested source SHA in 33 digest-verified files; the existing Runner-MCP consumer still retrieves only GitHub Actions artifacts. GitHub Release publication does **not** by itself grant host update authority or give a protected offline backup.

## First bounded source child (0.1.35 candidate, not deployed)

`runner_mcp.fabric_release_assets.inspect_exact_release` validates **data** only: 40hex source commit, exact fixed allowed tags `fabric-q7-bundle-<commit>` and `fabric-update-bundle-<commit>`, tag ref object type `commit` and same exact SHA, prerelease metadata, exact repository-bound source, at least 5 and no more than 160 unique safe asset names/IDs, 4 fixed manifests, one project wheel, 1+ wheels total, per-asset SHA256 digest/byte count, size limits, no symlinks/paths/URL/host arguments. This function does not read network, filesystem or credentials.

`FabricUpdateManager.release_assets_readiness(commit)` calls the existing credentialed **read-only** fixed `api.github.com/repos/Blacksp1d3r/Runner-Fabric` transport to fetch only the exact release tag and tag ref. The already published Q7 SHA has one fixed legacy prefix; future SHA values use `fabric-update-bundle-<commit>`. No user-supplied download URL, arbitrary repository, ref, binary path, SSH/shell, asset upload or install is supported. A positive response includes `source=github-release`, asset count and project-wheel digest, with `mutation_authorized=false`, `download_performed=false`.

Tests deny absent/forged/mismatched tags and target/source commits, duplicate/invalid names/IDs, traversal, unsupported file types, incorrect digest, draft/not-prerelease, unsafe or missing manifest files, and a process in active self-update. The existing `github-actions` and `local-custody` update flows are unmodified. No public MCP exposure or server enablement is added in this source child.

## NEXT — admission not activation

1. Verify source version candidate and test CI on exact PR head. Actual installed Runner-MCP on each private machine may differ from repository source; **do not claim** deployed 0.1.35 from code merge.
2. Add separately reviewed and tested owner-scoped downloader/importer using **only fixed release `asset.id` API paths** and bounded bytes. Avoid following attacker-supplied `browser_download_url`; authorize and verify any GitHub official redirected domain before removing Authorization. Never send the token to a redirected blob host.
3. Recompute SHA256 of **all downloaded** asset bodies and validate `BUNDLE.json`, `COMMIT_SHA`, `SHA256SUMS`, project wheel + Q7 inspector against existing `_validated_bootstrap` checks. Stage atomically to existing owner-only `local-bundles` without overwriting, and prove independent verified restore copy before activation.
4. Only after protected local custody and a fresh exact host identity/lease, use the **existing** authorized `start_local(commit)` rollback-gated Fabric updater. Central Runner-MCP's localhost is **not** the dedicated Claude worker host. Test original-client ACK, lease/fence and three provider-free Q7 availability cases before enabling any subscription coding work.

Do not replace the legacy Actions-artifact consumer until the new importer passes wrong repo/sha, partial asset, corrupt body, replay, missing mount, incorrect signed release identity and rollback tests. No private host paths, tokens or customer data may be committed to GitHub.
