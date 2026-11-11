## F30 2026-11-07 — extra stage-status regressie nu afgerond (0.1.152)

- Na #960 had `stage_local_bundle` drie oude hash-only checks die na aanpassing van wheel én SHA256SUMS `bundleReady=True` konden melden, terwijl de inmiddels strengere `local_readiness` de ZIP weigerde. **Geen productie-incident aangetoond**.
- [PR #961](https://github.com/Blacksp1d3r/runner-mcp/pull/961) deelt nu dezelfde bestaande `verify_wheel_records=True` op de drie stage-checkpoints; twee nieuwe synthetische regressies (bestaande en vers gebouwde bundel) PASS. Exact head `ef54623fb6062f18b000345eb0ea68750cb4f10e` 7/7 CI PASS inclusief **4707 pytest**; merge `4155e7f7219139603a167dbaa72abb84694c749b`. Oude kandidaatclaims hieronder zijn historische momentopnames, niet huidige CI-status.
- **Geen originele fysieke host-/wheel-, A6-/A7- of ACK-admissie.** Hergebruik de validator, bouw nooit een tweede updatepad.

## Aanvulling 2026-11-07 — volledige lokale stage-status volgde nog niet dezelfde validator (v0.1.152 kandidaat)

- Na het v0.1.151-herstel van `local_readiness` bleek bij broninspectie dat `stage_local_bundle` drie status- en opslagpaden nog met default `_validated_bootstrap` (alleen hashes) controleerde. Daardoor kon een eerder geaccepteerde maar later herpinde corrupte wheel alsnog `alreadyStaged=True, bundleReady=True` opleveren; ook de nieuwe clone/build bevestigde die READY-status zonder interne RECORD-inspectie. Dit is een inconsistentie tussen twee bestaande consumenten van dezelfde private custody, geen bewezen productie-incident.
- Correctie: op die drie plekken expliciet `verify_wheel_records=True`, en negatieve source-fixtures voor bestaande opslag en een nieuwe ongeldige builderoutput met herberekende SHA256SUMS. Geen tweede ZIP-parser, geen service of fysieke activatie. **Nog geen groene CI voor deze aanvullende bronkandidaat of merge claim.** 0.1.151-resultaten hierboven blijven afzonderlijk bewezen.

# F30 — lokale Fabric-wheel wijzigt samen met SHA256SUMS; oude ongeldige fixtures (2026-11-07)

## Risico en oorzaak

Runner-MCP [#341](https://github.com/Blacksp1d3r/runner-mcp/issues/341) gebruikt al één bestaande private lokale `local-bundles/<commit>` en bestaande `FabricUpdateManager.local_readiness`. De lokale herlezing valideerde de onbetrouwbare op dezelfde schijf bewaarde SHA256SUMS opnieuw, maar niet de interne ZIP/METADATA/WHEEL/RECORD van elk wheel. Wie na de aanvankelijk correct gecontroleerde byte-import **zowel een wheel als zijn SHA256SUMS** wijzigt, kan de oude hashcheck laten slagen, zelfs wanneer de ZIP ongeldig is. Dit is een synthetisch getoetst bronrisico, **geen bewezen incident op een productiehost**.

## Herstel binnen bestaande architectuur

[PR #960](https://github.com/Blacksp1d3r/runner-mcp/pull/960) hergebruikt **de reeds bestaande** `fabric_release_wheelhouse._wheel_record_check` met dezelfde globale expansielimiet als de GitHub-byte-import. `FabricUpdateManager._validated_bootstrap` neemt een `verify_wheel_records`-opt-in die **alleen** wordt gevraagd op de bestaande lokale custody-route: tijdens read-only `local_readiness`, vóór en na een lokale werkbundelkopie en direct vóór de lokale BOOTSTRAP-preflight. De gewone Actions-source en rollback worden niet gewijzigd. Een fout retourneert de vaste categorie `fabric_bundle_integrity_failed`, zonder ongecontroleerde ZIP-inhoud/paden te lekken. Dit bewijst geen onafhankelijke signer-, eigenaar-, fysieke host- of rollbackbevoegdheid.

## Mislukte eerste CI-heads zijn geen geslaagde tests

1. PR-head `e86b7ec359b2f236cc4e6c8d3867439ee157a5e6`: Validation `42310389215` **FAIL**, versie 0.1.151 nog niet in het **vierde** vereiste metadata-/discoverybestand `glama.json`. Daarna alle vier (pyproject, server.json, package __version__, glama.json) gelijk gezet.
2. PR-head `a852a02ce5073f38dcb198311b91feec5c8717b1`: Validation `42310508247` **FAIL**, Ruff I001 importvolgorde in bestaande validatorhergebruik. Sorteervolgorde hersteld.
3. PR-head `66cc47ad342a66dddd1e73438c2df6f2ecfceb3c`: Validation `42310613857` **FAIL**: 5 falende bestaande positieve local-custody tests / 4700 PASS. Die fixtures leverden `b"synthetic-wheel"` of ZIP met alleen METADATA/WHEEL **zonder RECORD**, dus waren nooit geldig volgens het reeds bestaande wheelcontract. **Geen versoepeling** van productie-validator: beide bestaande testhelpers maken voortaan kleine geldige echte ZIP-wheels met `runner_fabric/__init__.py`, METADATA, WHEEL en volledig gehashte en op lengte gecontroleerde RECORD.

Finale head `920dcf884b0d00c8149464371f867ca5d19a122e`: Validation `42310895233` **SUCCESS** (Ruff, **4705 pytest PASS**, release-reservering, gebouwde distributie, disposable systemd, vijfminutendemo); Clean Ubuntu `42310895135` **SUCCESS**; Attribution `42310895172` **SUCCESS**. Exact 7/7 gates. PR #960 squash **MERGED** op `main` als `22624dbf42c63f6b57d2161eaf88f6050128a6bd`. Test verifieert geldige 5-asset custody, dan wheel beschadigen en SHA256SUMS herberekenen: oude hash-only checker ziet overeenstemming, nieuwe ZIP/RECORD checker weigert vóór stage/apply.

## Niet opnieuw doen en blijvende stop

Behoud de structurele wheelvalidator en valideer fixtures tegen het echte formaat vóór claims over defecte productcode. Controleer bij versie-uitgifte altijd alle **vier** discovery-/runtimeversies; check Ruff, de volledige repo-tests en exacte commit vóór merge. Laat rode CI-historie bestaan en kwalificeer alleen de finale head.

**BRON/CI VOLTOOID, LIVE ONBEWEZEN:** lokale `artifact_ready` is geen fysieke updatebevoegdheid, en pakketchecks zijn geen onafhankelijke integriteitssignatuur wanneer alle lokale bytes gemanipuleerd kunnen zijn. Op de oorspronkelijke `github-runner` is actief wheel/source/procesverificatie #669 nog niet bewezen; eigenaar/CI-policy, behouden startbare baseline #341, echte off-target A6 #942, onafhankelijk boot-persistent offline A7 #943 en oorspronkelijke-client result+ACK zijn onvoltooid. Geen serverwijziging, rollback, Qwen/Claude/SQL-mutatie of ED-productsleutel in dit bronwerk.
