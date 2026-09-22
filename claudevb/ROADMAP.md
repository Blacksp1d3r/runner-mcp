# Voorstellen: `roadmap/ROADMAP.md`

## Wat er nu is

`roadmap/ROADMAP.md` is 573 regels lang en bevat 28 `## Phase`-koppen
(Phase 0 t/m Phase 10, plus tussenliggende sub-fases zoals 3.5, 3.6, 3.7,
3.8, 3.8.1 t/m 3.8.10, 3.9). Elke fase beschrijft in doorlopende tekst wat
"Implemented" is en wat "Next"/"Still deferred"/"Still planned" is. Dat is
inhoudelijk heel precies en eerlijk (het onderscheidt consequent "gebouwd"
van "beweerd"), maar de vorm is een lineair proza-document zonder enige
navigatiehulp.

## Concrete pijnpunten

1. **Geen inhoudsopgave / status-overzicht.** Om te weten "wat is er nu wél
   en niet geïmplementeerd" moet je alle 573 regels lezen. Er is geen
   samenvattende tabel met per fase: status (✅ done / 🚧 partial /
   ⏳ planned), en geen anker-links.
2. **Sub-fase-explosie is moeilijk te scannen.** Phase 3.8 heeft tien
   sub-fases (3.8.1 t/m 3.8.10) die elk een eigen "Implemented foundation" +
   "Next"-structuur hebben. Vanaf de titel alleen is niet te zien dat dit
   allemaal onderdeel is van "de GitHub-mailbox-bridge hardening". Een
   subkop-niveau (bv. "### Bridge hardening" met daaronder 3.8.1–3.8.10)
   zou de group-structuur zichtbaar maken.
3. **"Next" en "Still deferred/planned" worden inconsistent gebruikt.**
   Sommige fases gebruiken "Next", andere "Still deferred", "Still
   planned", "Remaining before a broader launch". Functioneel is dat
   hetzelfde concept (openstaand werk), maar de wisselende koppen maken het
   lastiger om geautomatiseerd of visueel te scannen op "wat is nog open".
4. **Losstaand van `handover/CURRENT_STATE.md`.** Er zijn nu twee
   documenten die allebei "wat is af" bijhouden: de roadmap (per fase, met
   architecturale features) en `handover/CURRENT_STATE.md` (per datum, met
   validatiecijfers). Die twee overlappen sterk in inhoud maar niet in
   structuur, en zoals in DOCS.md beschreven lopen concrete testaantallen
   tussen deze bestanden uiteen. Het is niet gedocumenteerd wélke van de
   twee leidend is wanneer ze elkaar tegenspreken.
5. **Geen tijdsindicatie/versie-tags.** Fases hebben geen datum en geen
   koppeling naar een git-tag/commit. Voor een lezer die na een paar maanden
   terugkomt is niet meteen duidelines "sinds wanneer" een fase af is.
6. **Fase-nummering wordt semantisch overladen.** "Phase 3.8.9a" (shared
   Playwright test runtime) breekt de x.y.z-conventie met een letter-suffix.
   Op zichzelf onschuldig, maar het is een signaal dat het fasenummerings-
   schema krap begint te zitten na organische groei.

## Voorstellen

- **Voeg bovenaan een compacte statustabel toe** (fase, één-zin-titel,
  status, link naar detail-sectie). Dat kost een paar regels Markdown en
  maakt het document in 10 seconden scanbaar in plaats van in 10 minuten.
  Voorbeeld:

  ```markdown
  | Fase | Onderwerp | Status |
  | --- | --- | --- |
  | 0 | Repository & design | ✅ Done |
  | 1 | Minimale MCP-server | ✅ Done |
  | … | … | … |
  | 3.9 | Public launch readiness | 🚧 Alpha-tag nog niet getagd |
  | 10 | Restricted command templates | ⏳ Optioneel, alleen bij bewezen behoefte |
  ```

- **Groepeer de 3.7–3.8.x-cluster onder één `##`-sectie** met sub-`###`
  koppen per sub-fase, zodat de GitHub-mailbox-bridge-hardening als één
  samenhangend verhaal leesbaar is in plaats van als tien losse
  top-level-fases.
- **Standaardiseer op precies twee koppen per fase**: `Implemented` en
  `Next` (laat "Still deferred", "Still planned", "Remaining" vervallen ten
  gunste van consequent "Next"). Kleine tekstuele wijziging, grote
  consistentiewinst.
- **Maak expliciet welk document leidend is** voor "huidige status":
  bijvoorbeeld een regel bovenaan de roadmap: "Voor exacte
  validatiecijfers (testaantallen, CI-status) is `handover/CURRENT_STATE.md`
  leidend; deze roadmap beschrijft alleen architecturale fases." Dat
  voorkomt toekomstige drift-verwarring.
- **Overweeg de roadmap te splitsen in "Done" en "Planned"** als aparte
  bestanden (`roadmap/DONE.md` / `roadmap/PLANNED.md`) zodra het document
  verder groeit — op dit moment (573 regels) is dat nog niet strikt nodig,
  maar bij de volgende paar fases wel het overwegen waard.
- **Voeg per fase een korte "waarom"-zin toe** waar die ontbreekt. De meeste
  fases beginnen al mooi met een motiverende zin ("Make asynchronous work
  observable to the operator…"), maar een paar (bv. Phase 8, Phase 10) zijn
  extreem kort en missen die context — voor een nieuwe lezer die niet de
  hele geschiedenis kent is niet meteen duidelijk waaróm "multi-project
  adapters" een aparte fase verdient.
