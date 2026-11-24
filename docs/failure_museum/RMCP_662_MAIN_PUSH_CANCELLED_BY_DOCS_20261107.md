## 2026-11-24 — IIT 0.1.199 source-main CI CANCELLED; causal attribution still unknown

Independent follow-up for *this existing Failure Museum topic*, not a second museum or CI controller. Source PR #1072 `1b5bc89a...` passed all three exact-head PR CI groups and source merged `243794d1533d49ac6c798e38ba0361622929dd06`. But **post-main validation** Actions run [45338160758](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/45338160758) ended **CANCELLED**; job `Disposable real systemd user lifecycle` ID 138255615314 ended CANCELLED while Ruff/pytest + clean demo passed, release artifact was SKIPPED. Exact docs-main merge SHA `72c41f8...` independently passed attribution and validation; those successes are NOT substitute evidence for cancelled source-main SHA.

The systemd job began near 06:09 UTC and the source run concluded near 06:14 UTC; existing systemd CI has `timeout-minutes: 5`, which is consistent with but does **not prove** a timeout. A bounded in-progress Actions job-log request returned HTTP 404 BlobNotFound from log backing storage, so the exact cancellation cause is **UNVERIFIED**. Do not assert docs-push cancellation, code defect, or timeout without additional actual source evidence. No rerun/bypass, CI workflow change, or new runner was performed; this is an evidence correction. [Canonical IIT #952 reconciliation](https://github.com/Blacksp1d3r/runner-mcp/issues/952#issuecomment-7136087099).

Later IIT v0.1.200 source PR #1074 exact-head three workflows passed; its independent source-main acceptance is separate and must be checked before saying success. Its operator deliberately postponed next docs-main merge until previous source-main CI terminal, to avoid concurrent main commits obscuring evidence.

## 2026-11-07 — aanvullend gevonden: de artifactjob liep vóór de einddemo (0.1.154 bronkandidaat)

- V0.1.152 main `42351052147` had exact kandidaatartifact al geüpload ondanks overall CANCELLED tijdens demo. Dat onthult naast het in-progress-cancelprobleem een afzonderlijke volgordeafhankelijkheid: de bestaande `release-artifact` vroeg alleen `validate`, niet de reeds bestaande `demo-smoke` en `disposable-systemd-user`.
- Bestaande workflowjob nu `needs: [validate, demo-smoke, disposable-systemd-user]`: dezelfde validators/artifactbron, géén nieuwe publicatiemethode of CI-systemen. Statische regressietest houdt deze drie dependencies vast. CI/merge voor deze bronkandidaat 0.1.154 nog OPEN; externe attribution/Ubuntu, pending-run-queue en fysieke host/A6/A7/ACK-bewijzen blijven los.

## 2026-11-07 — #662 eindbewijs bronpatch 0.1.153 (MERGED / PR CI PASS)

- De ontbrekende actieve-main-push-retentie is in [PR #962](https://github.com/Blacksp1d3r/runner-mcp/pull/962) gecorrigeerd met `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` in beide bestaande workflows. Exact-head `aa39aa72e65abc9e8be27d9672d5ce8c9e15e530`: 7/7 CI SUCCESS inclusief **4708 pytest** en volledige demo; merge `f79f07e27b5af1d97c7019f298e42c5275af85f9`. Nieuwe opvolgende docs main-push wordt gebruikt om echte ononderbroken main-run te controleren.
- Let op: dit voorkomt annulering van **lopende** main-runs, niet automatisch GitHubs mogelijke vervanging van nog **wachtende** runs in dezelfde concurrencygroep. Owner/host/rollback/A6/A7/ACK blijven afzonderlijk OPEN; zelfs volledige bron-CI levert nooit install-authority.

# RMCP #662 — docs-push annuleert automatische source-release CI (2026-11-07)

## Aangetroffen en via GitHub geverifieerde fout

De bestaande `.github/workflows/validation.yml` gebruikt op `main` de concurrencygroep `runner-mcp-ci-<workflow>-<ref>` met `cancel-in-progress: true`. De shipping/source-merge v0.1.152 `4155e7f7219139603a167dbaa72abb84694c749b` startte main workflow `42351052147`: Ruff/pytest en het built-artifact job waren SUCCESS, maar de vijfminutendemo werd **CANCELLED** toen een volgende docs-commit `5220b3e7097b1ebb480a6d0c7e31461944df874d` zijn main-push workflow startte. De eerdere source-run eindigde daarom met conclusie **CANCELLED**, niet SUCCESS.

Via de officiële Actions artifactlijst is voor die eerste shipping-run het bestand `runner-mcp-candidate-0.1.152-4155e7f7219139603a167dbaa72abb84694c749b`, artifact ID `13565557686`, status `expired=false` aangetoond. Een opgeslagen wheel/sdist is **geen** einddemo-/alle-checks-groenbewijs en geen fysieke updateautoriteit. De nieuwe docs-only main workflow `42351240774` was zelf SUCCESS maar kon niet achteraf de geannuleerde exacte bron-run bewijzen.

## Oorzaak en begrensde oplossing (0.1.153 kandidaat)

De bestaande `cancel-in-progress: true` was terecht voor *verouderde PR-runs*, maar fout voor shipping commits op `main`, waar elk SHA zijn eigen releasevalidatie en eventueel artifact-custody nodig heeft. In de twee bestaande workflows `validation.yml` en `commit-attribution-policy.yml` wordt die instelling `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. De concurrencygroepen, runners, source-artifactjob, uploadretentie en alle bestaande controles blijven gelijk. Geen tweede CI-updater, extra controller, betaalde service of signer. Een statische test in bestaande workflowtests bewaakt deze keuze.

**Acceptatie nog niet bewezen:** exacte PR-head CI 7/7, merge en een echte vervolgdocs-push tijdens de main-release-run moeten uitsluiten dat die source-run weer wordt geannuleerd. Tot die tijd BRONKANDIDAAT. Echte A6/A7/original-host en originele-client ACK zijn aparte **WAIT**-voorwaarden; bronartifact ≠ productieupdate.
