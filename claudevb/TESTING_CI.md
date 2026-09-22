# Voorstellen: tests, CI en releaseproces

## Geverifieerde huidige status (2026-09-22)

Om claims in de documentatie te toetsen is lokaal een schone Python
3.12-venv aangemaakt en is het project geïnstalleerd zoals een nieuwe
gebruiker dat zou doen (`pip install -e '.[dev]'`). Resultaat:

- `pytest -q` → **685 passed, 1 warning** (9.98s) — de ene waarschuwing is
  een bekende, reeds gedocumenteerde third-party
  Starlette/AnyIO-`DeprecationWarning`, geen projectcode.
- `ruff check .` → **All checks passed!**

Deze venv is buiten de repository aangemaakt (`/tmp/...`); er is niets aan
de repository zelf aangepast, dit was puur verificatie.

Beide bevestigen dat de "Validation is green"-claim in
`handover/CURRENT_STATE.md` klopt — alleen het exacte testaantal loopt
achter (zie [DOCS.md](DOCS.md) punt 1).

## 1. CI-workflow is goed opgezet, met één verbeterpunt

`.github/workflows/validation.yml` heeft drie duidelijk gescheiden jobs
(`validate`, `demo-smoke`, `release-artifact`), gebruikt gepinde
action-SHA's (goede supply-chain-praktijk), `permissions: contents: read`,
en een `concurrency`-groep om overbodige parallelle runs te annuleren. Dit
is al sterk.

Kleine observatie: de drie jobs draaien **parallel**, niet sequentieel. Dat
is prima voor snelheid, maar betekent dat `demo-smoke` en
`release-artifact` ook draaien als `validate` (compile/ruff/pytest) al
faalt — wat CI-minuten verspilt op een commit die toch al rood is.

**Voorstel:** `needs: validate` toevoegen aan de `demo-smoke`- en
`release-artifact`-jobs, zodat ze alleen draaien nadat de snelste/
goedkoopste job (validate) geslaagd is. Dat bespaart CI-tijd zonder de
dekking te verminderen.

## 2. Geen CI-badge zichtbaar (zie ook DOCS.md)

Al genoemd in DOCS.md, maar relevant genoeg om hier te herhalen vanuit
CI-perspectief: er bestaat geen zichtbare link tussen "we hebben groene CI"
en de plek waar een bezoeker dat zou verwachten (README).

## 3. Testorganisatie: `unit/`, `integration/`, `security/`

De driedeling is logisch en consistent toegepast. Een observatie: sommige
bestanden in `tests/security/` (bv. `test_public_examples.py`,
`test_private_config.py`) testen configuratie-/documentatiehygiëne
(bv. "geen echte infrastructuurwaarden in publieke voorbeelden") eerder dan
klassieke beveiligingslogica zoals padvalidatie. Dat is functioneel
correct geplaatst (het zijn wel degelijk beveiligings-/privacy-regressies),
maar een lezer die op zoek is naar "waar wordt padvalidatie getest" moet
weten dat die ook onder `security/` valt in plaats van `unit/`. Geen
wijziging nodig, alleen het waard om te vermelden voor iemand die voor het
eerst door de testmap navigeert.

## 4. Ontbrekende dedicated unit-tests

Zie [CODE.md](CODE.md) punt 11 voor het volledige overzicht
(`audit.py`, `server.py`-validatielogica, dunne `test_adapters.py`). Kort
samengevat: de dekking is functioneel goed (alles wordt uiteindelijk via
integratietests geraakt), maar een paar kleine, fundamentele modules zouden
baat hebben bij een eigen, snel te lezen unittestbestand.

## 5. Releaseproces is ongewoon volwassen voor pre-alpha

`docs/RELEASE_CHECKLIST.md` is compleet: code/validatie, publieke-
repository-hygiëne, documentatie, package-metadata, release-notes-inhoud,
tag/release-stappen, en een expliciete "cost rule" (geen verborgen betaalde
afhankelijkheid). Dit is een van de sterkste onderdelen van het hele
project en behoeft inhoudelijk geen wijziging.

Enige kanttekening: de checklist is een Markdown-document, geen
geautomatiseerd script. Voor een project dat verder alles fail-closed en
geautomatiseerd test, zou een `scripts/release-check.sh` die een deel van
de checklist automatisch afvinkt (compile/ruff/pytest/whitespace/
artifact-smoke — wat feitelijk al los in CI gebeurt) de menselijke
foutmarge bij het daadwerkelijk taggen verder verkleinen. Dit hoeft geen
100%-dekking te hebben; zelfs alleen de geautomatiseerde helft (wat toch al
in CI zit) samenvoegen tot één lokaal te draaien commando zou nuttig zijn
vóór het zetten van een tag.

## 6. `scripts/release-artifact-smoke.sh` en `scripts/demo-smoke.sh`

Beide scripts zijn kort gelezen tijdens deze review en zijn goed
geschreven: `set -euo pipefail`, expliciete cleanup via `trap`, geïsoleerde
`$HOME`/venv per run. Geen wijzigingsvoorstel; genoemd hier ter bevestiging
dat de CI-scripts zelf niet de zwakke schakel zijn.
