## 2026-11-06 — F30 #937 generic signed Release byte-batch (source-only 0.1.142)

`fetch_exact_signed_fabric_bundle_bytes(token, signed_document, signature, public_key, independently_trusted_key_sha256, expected_commit, expected_release_id, observed_metadata, asset_reader=existing)` → `verify_signed_fabric_roster` (roosterbytes Ed25519 onder door caller aangeleverde *extern* verwachte key/bron/release-ID) → `compare_signed_fabric_roster` (reeds apart gevalideerde exacte Release/tag API metadata) → uitsluitend bij match: 5..160 maal `fetch_pinned_asset_bytes` op vaste eerste-partij GitHub asset-ID + exacte size/SHA → hercontrole bytes/digest en totaal 256MiB cap → `verify_signed_fabric_wheelhouse` bestaande BUNDLE/SHA256SUMS/COMMIT/ZIP/METADATA/RECORD → in-memory dict; geen filewrite, service of stage. `operator_signer_authority_attested` blijft niet bewezen, want key+source beleid ontbreekt bij Fabric #924. Live update en originele ACK blijven NIET GETEST.

## 2026-11-06 — #937 generic signed wheelhouse ZIP/RECORD

`verify_signed_fabric_wheelhouse(signed_pins, observed_release, all_asset_bodies)` → 0.1.138 `compare_signed_fabric_roster` → 0.1.139 gedeelde `check_complete_signed_fabric_bundle` (BUNDLE/COMMIT/SHA256SUMS en complete SHA256-byte set) → dezelfde bestaande `_wheel_record_check` als Q7 29-wheel ZIP-pins (METADATA Name/Version, WHEEL, RECORD, directory/path/symlink, limits, expanded total). Genereert alleen `wheel_metadata_record_only`, `wheel_metadata_verified=true` over aangeleverde bytes en alle signer-authority/download/custody/mutation/rollback/original-client ACK=false. Geen netwerk/hosttoegang. Regressies: bestaande `tests/test_fabric_release_wheelhouse.py`, aangevuld met generic 5/33/160 en corrupte ZIP-fouten.

## 2026-11-06 — #937 shared in-memory complete bundle validation

`verify_signed_fabric_roster(externally pinned commit/release/key)` + `inspect_exact_release(GitHub metadata)` → `compare_signed_fabric_roster` → `check_complete_signed_fabric_bundle(signed_pins, observed_metadata, asset_bodies)` → dezelfde `_verify_complete_contents` als historische `check_complete_q7_bundle` (Q7-pins eerst apart via vaste historische comparator). Check alle namen/asset-ID/omvang/digest, complete Manifest/COMMIT_SHA/SHA256SUMS, bootstrap en wheelcount; hoogstens `bundle_consistency_only`, geen download, ZIP/RECORD, fysieke custody, bron-/signerautoriteit, install/rollback of originele ACK. Positieve/negatieve regressies `tests/test_fabric_release_full_bundle_generic.py` en bestaande `tests/test_fabric_release_full_bundle.py`; #937.

## 2026-11-06 — #937 signed Fabric release roster, offline-only

`verify_signed_fabric_roster(signed_document, signature, public_key, independently_trusted_key_sha256, expected_commit, expected_release_id)` -> geauthenticeerde *buiten deze functie* aangeleverde exacte bron/release/signer pin -> Ed25519 over originele payloadbytes -> strikte JSON-schema-/duplicatecontrole -> bestaande `inspect_exact_release` assetbegrenzingen -> `ReleaseAdmission` met onveranderlijke naam/ID/size/SHA-pins. `compare_signed_fabric_roster(signed_pins, observed_metadata)` -> gesigneerde inventaris versus aparte vaste GitHub Release-admission -> hoogstens `comparison=match_only`. `operator_signer_authority_attested=false`, `download_performed=false`, `install_authorized=false`, `rollback_verified=false`, `original_client_ack_proven=false`. Geen netwerk-/filesystem-/subprocess-aanroepen, geen bron-/wielinstallatie, geen servergeneratie of privé-sleutel. Bestaande Q7 signed import blijft onafhankelijk. Nieuwe publisher/productie-signer voor `runner-fabric/signed-release-roster/v1` bestaat nog niet als geverifieerde autoriteit: het schema is slechts een kandidaat voor Fabric #924. Tests `tests/test_fabric_release_signed_roster.py`; #937.

## 2026-11-06 — F30 exacte Release-foutcategorieën (source-only)

`fabric_release_assets_readiness(commit)` en de #934 diagnostische Actions-fallback hergebruiken dezelfde read-only `FabricUpdateManager.release_assets_readiness`. Beide vaste GitHub-GET's (Release plus exact tag-ref) moeten HTTP 404 opleveren voor `release_not_published`; één 404 en één aanwezig endpoint wordt `fabric_release_assets_unqualified`. Een transportstatus anders dan 404/netwerkfout wordt `release_provider_unavailable`; ongeldige asset-SHA metadata `release_digest_invalid`; alle overige ongeldige identiteit/assetlijst blijft `fabric_release_assets_unqualified`. Alle codes zijn zonder private providertekst, bron- of download-URL; `artifact_ready=false`, de Actions-bronstatus blijft blocked en geen resultaat autoriseert downloaden/installeren/rollback. HTTP 404 kan ook op verborgen toegang wijzen: uitsluitend diagnoselabel, **niet** publicatie- of updatebevoegdheid. Regressie: `tests/test_fabric_release_status_categories.py`. Original-target serving wheel, A6/A7 en same-client ACK blijven niet aangetoond.

## 2026-10-24 — Fabric GitHub Release metadata-only readiness

`fabric_release_assets_readiness(exact40hex)` → existing `FabricUpdateManager.release_assets_readiness` → original manager runtime/managed-launcher safety gate → fixed Runner-Fabric GitHub Release tag and Git tag ref metadata → `inspect_exact_release` validates exact source pin, asset names/counts, size and SHA-256 metadata → sanitized `source=github-release`, `state=ready`, `mutation_authorized=false`, `download_performed=false`, bounded audit event. On bad source/unsafe runtime/unqualified ref/digest metadata → `bounded_fabric_readiness_failure(source=github-release)`, `artifact_ready=false`. Neither result verifies bytes, independent signer, staging, actual serving module, previous-good rollback or permission to install. The distinct `fabric_update_readiness` retains GitHub Actions-only semantics; NO silent fallback to GitHub Releases. Regression: `tests/test_fabric_release_metadata_readiness.py` and `tests/test_fabric_update_readiness_unavailable.py`.

# Runner-MCP field/action lineage

For Runner-MCP, field-level lineage means tracing every public tool field or result field to the exact bounded authority that produced it.

## Required dimensions

| Dimension | Meaning |
|---|---|
| tool | MCP/public capability |
| semantic_input | caller-supplied bounded semantic field |
| validation | schema/allow-list/revision validator |
| trusted_source | private config, project registry, fixed catalogue, peer evidence, local state |
| policy | safety/approval/compatibility policy |
| executor | exact manager/component |
| state_write | private metadata/job/audit state, if any |
| external_edge | GitHub/Fabric/database/project/runtime edge, if any |
| result_field | sanitized public evidence |
| tests | narrowest proving tests |
| failures | linked stable failure IDs |

## Critical chains

`self_update(commit) -> commit validation -> known self-project -> source synchronizer -> bounded tests -> installer -> restart markers -> runtime_status`

`run_tests(project, suite) -> project registry -> test profile -> safety guard -> bounded subprocess -> job metadata -> redacted bounded result`

`Fabric proxy -> fixed allow-listed Fabric tool -> protocol/build/interface preflight -> peer call -> schema validation -> sanitized result`

`mailbox request -> strict protocol parser -> replay/fencing -> bounded capability dispatch -> durable result sink -> acknowledgement`

`deploy/migration/backup -> known project config -> approval/safety state -> fixed manager -> durable job/metadata -> bounded result`

A result field must never be treated as proof of an upstream fact that is not represented in its lineage.
