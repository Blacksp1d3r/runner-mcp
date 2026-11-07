# RMCP #662 — docs-push annuleert automatische source-release CI (2026-11-07)

## Aangetroffen en via GitHub geverifieerde fout

De bestaande `.github/workflows/validation.yml` gebruikt op `main` de concurrencygroep `runner-mcp-ci-<workflow>-<ref>` met `cancel-in-progress: true`. De shipping/source-merge v0.1.152 `4155e7f7219139603a167dbaa72abb84694c749b` startte main workflow `42351052147`: Ruff/pytest en het built-artifact job waren SUCCESS, maar de vijfminutendemo werd **CANCELLED** toen een volgende docs-commit `5220b3e7097b1ebb480a6d0c7e31461944df874d` zijn main-push workflow startte. De eerdere source-run eindigde daarom met conclusie **CANCELLED**, niet SUCCESS.

Via de officiële Actions artifactlijst is voor die eerste shipping-run het bestand `runner-mcp-candidate-0.1.152-4155e7f7219139603a167dbaa72abb84694c749b`, artifact ID `13565557686`, status `expired=false` aangetoond. Een opgeslagen wheel/sdist is **geen** einddemo-/alle-checks-groenbewijs en geen fysieke updateautoriteit. De nieuwe docs-only main workflow `42351240774` was zelf SUCCESS maar kon niet achteraf de geannuleerde exacte bron-run bewijzen.

## Oorzaak en begrensde oplossing (0.1.153 kandidaat)

De bestaande `cancel-in-progress: true` was terecht voor *verouderde PR-runs*, maar fout voor shipping commits op `main`, waar elk SHA zijn eigen releasevalidatie en eventueel artifact-custody nodig heeft. In de twee bestaande workflows `validation.yml` en `commit-attribution-policy.yml` wordt die instelling `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. De concurrencygroepen, runners, source-artifactjob, uploadretentie en alle bestaande controles blijven gelijk. Geen tweede CI-updater, extra controller, betaalde service of signer. Een statische test in bestaande workflowtests bewaakt deze keuze.

**Acceptatie nog niet bewezen:** exacte PR-head CI 7/7, merge en een echte vervolgdocs-push tijdens de main-release-run moeten uitsluiten dat die source-run weer wordt geannuleerd. Tot die tijd BRONKANDIDAAT. Echte A6/A7/original-host en originele-client ACK zijn aparte **WAIT**-voorwaarden; bronartifact ≠ productieupdate.
