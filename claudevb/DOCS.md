# Voorstellen: documentatie en consistentie

Runner MCP heeft ongewoon uitgebreide documentatie (README, QUICKSTART,
AGENTS.md, CONTRIBUTING, CHANGELOG, SECURITY.md, 12 bestanden onder
`docs/`, 11 onder `security/`, plus de roadmap en handover-notities). De
kwaliteit is hoog en consistent in toon. Onderstaande punten zijn vooral
over **drift tussen bestanden** en **vindbaarheid**, niet over inhoudelijke
fouten.

## 1. Concreet geconstateerde cijfer-drift

- `handover/CURRENT_STATE.md:352` zegt: *"pytest: 628 tests green"*.
- `docs/RELEASE_NOTES_0.1.0.md:78` zegt: *"the current pre-tag
  release-candidate baseline is 651 passed tests"*.
- De werkelijke testsuite op dit moment (verse Python 3.12-venv, `pytest -q`)
  geeft **685 passed, 1 warning**.

Alle drie de bronnen zijn "waar" op het moment van schrijven — dit is geen
fout, maar een teken dat testaantallen in proza-documenten snel verouderen
zodra er nieuwe tests bijkomen. Twee bestanden bevatten al een verouderd
cijfer terwijl ze beide recent gedateerd zijn (2026-09-21).

**Voorstel:** noem in dit soort documenten geen exact testaantal in lopende
tekst, of voeg een expliciete "laatst geverifieerd op commit `<sha>`"-notitie
toe. Nog beter: laat de CI het actuele aantal automatisch in de
release-notes-draft plakken vlak vóór het taggen (dit staat feitelijk al
als instructie in `docs/RELEASE_CHECKLIST.md`: *"Record the exact passing
test count and commit SHA in the GitHub release notes when the tag is
created"* — dat proces is dus goed doordacht, het is alleen de
tussentijdse drift in niet-release-documenten die opvalt).

## 2. Twee "huidige status"-documenten zonder duidelijke hiërarchie

`roadmap/ROADMAP.md` (architecturale fases) en
`handover/CURRENT_STATE.md` (chronologisch, met validatiecijfers) beschrijven
allebei "wat is af". Ze overlappen inhoudelijk sterk maar zijn structureel
verschillend geordend (per-fase vs. per-datum). Nergens staat expliciet
welke van de twee leidend is als ze elkaar tegenspreken. Zie ook
[ROADMAP.md](ROADMAP.md) in deze map voor een concreet voorstel (één
verwijzende zin bovenaan de roadmap).

## 3. Geen CI-badge / build-status zichtbaar in README

Het project heeft een werkende publieke GitHub Actions-workflow
(`.github/workflows/validation.yml`, drie jobs: validate, demo-smoke,
release-artifact) die op elke push/PR draait. Nergens in README.md,
CHANGELOG.md of de `docs/`-map staat een build-status-badge
(`![CI](...)`). Voor een project dat expliciet "public launch readiness"
als fase heeft (Phase 3.9) en waarvan de vijf-minuten-demo juist bewust in
CI wordt gevalideerd, is een zichtbare groene badge een goedkope
vertrouwenssignaal voor nieuwe bezoekers.

**Voorstel:** voeg een GitHub Actions-statusbadge toe bovenaan README.md,
vlak onder de titel.

## 4. `docs/RELEASE_NOTES_0.1.0.md` heeft geen paginakop-hint dat het een draft is buiten de titel

De titel zegt "release-candidate draft" en de eerste regel herhaalt dat,
wat prima is. Maar het bestandspad (`docs/RELEASE_NOTES_0.1.0.md`) suggereert
een definitief document, en het staat niet gelinkt vanuit README.md of
CHANGELOG.md (wat op zich bewust lijkt, om te voorkomen dat het als
gepubliceerde release wordt gelezen voordat het getagd is) — maar dat
betekent ook dat een lezer die via de repo-bestandenlijst binnenkomt het
kan aanzien voor een echte, gepubliceerde release. Een duidelijkere
bestandsnaam zoals `RELEASE_NOTES_0.1.0.DRAFT.md` zou dat risico verder
verkleinen, al is dit een kleine kanttekening.

## 5. Roadmap-cross-references ontbreken soms

`docs/CONCURRENCY.md`, `docs/WATCHER_RESILIENCE.md`,
`docs/COMPLETION_FEEDBACK.md` en `docs/GITHUB_MAILBOX_BRIDGE.md` linken
onderling goed naar elkaar, maar geen van deze vier linkt terug naar het
specifieke roadmap-fase-nummer dat ze implementeren (bv.
`docs/CONCURRENCY.md` implementeert Phase 3.8.8, maar noemt dat
fasenummer nergens). Voor iemand die van de roadmap naar de detaildocs
navigeert werkt dat goed (de roadmap linkt al naar `CONCURRENCY.md`), maar
andersom — van een detaildoc terug naar "welke fase is dit ook alweer" —
niet.

**Voorstel:** een korte regel bovenaan elk `docs/*.md`-bestand: "Implements
roadmap Phase X.Y." Kost een regel per bestand, maakt de twee documentlagen
in beide richtingen navigeerbaar.

## 6. AGENTS.md is kort en direct — dat is een sterk punt, geen probleem

Ter vergelijking met de rest: `AGENTS.md` is compact (31 regels) en legt
precies de tien niet-onderhandelbare regels vast. Dit werkt goed als
"contract" voor AI-assistenten/bijdragers. Geen wijziging nodig; genoemd
hier puur omdat het een positief contrast is met de soms zeer uitgebreide
overige documentatie — een mogelijk model voor het inkorten van andere
documenten (zie punt 7).

## 7. Overlap tussen README, QUICKSTART en docs/USING_AND_EXTENDING.md

Alle drie bevatten (in wisselende mate van detail) dezelfde
installatiestappen (`git clone` → `./install.sh` → `runner-mcp setup` →
`doctor` → `guide`/`serve`). Dat is op zich prima voor onboarding
(herhaling is didactisch nuttig), maar het risico is dat een toekomstige
commando-wijziging (bv. een nieuwe verplichte stap) in één document wordt
bijgewerkt en in een ander vergeten. Op dit moment zijn ze onderling
consistent — geen fout gevonden — maar het is een structureel risico dat
de moeite waard is om te benoemen.

**Voorstel:** overweeg de exacte installatiecommando's op één plek te
"ownen" (bv. README als canonieke bron) en de andere documenten daarnaar te
laten verwijzen met alleen context-specifieke aanvullingen, in plaats van
de volledige commandoreeks driemaal te herhalen.

## 8. Taal en toon

Alle documentatie is in consistent, zakelijk Engels geschreven, zonder
overdrijving ("production-ready", "unhackable" worden zelfs expliciet
verboden in `docs/LAUNCH_COPY.md`). Dit is een van de sterkste punten van
het hele project en verdient geen wijziging — alleen expliciete erkenning
hier, omdat het makkelijk is om bij "verbetervoorstellen" alleen naar
gebreken te kijken.
