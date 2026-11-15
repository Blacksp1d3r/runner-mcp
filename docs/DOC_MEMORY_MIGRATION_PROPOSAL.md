# Doc-memory migratievoorstel — Runner-MCP

Status: **goedgekeurd door de eigenaar op 2026-11-15**, gefaseerd in uitvoering.

## 0. Eigenaarsbesluiten 2026-11-15

1. Archiefgrenzen goedgekeurd: `SESSION_HANDOFF` vóór 2026-11-13; `CURRENT_STATE`, `ROADMAP`, `DEPENDENCIES` (en Runner-MCP `NEXT_ACTION`) vóór 2026-11-08. Voorwaarde: actieve taken, blokkades, afhankelijkheden en claims blijven zichtbaar, en alle historie blijft terugvindbaar. Daarom zet `split --open-items` elk nog open issue/PR dat alleen in gearchiveerde secties voorkomt in een vast blok bovenaan het actieve bestand. `AGENT_EXCHANGE` en `CURRENT_ASSIGNMENT` worden niet op datum gearchiveerd.
2. Compacte `AGENTS.md` goedgekeurd en in deze PR geactiveerd. Het origineel is byte-identiek bewaard (`docs/agents/AGENTS_FULL_2026-11-15.md`, SHA-256 bewaakt in CI). De dekkingscontrole staat in `docs/agents/AGENTS_COVERAGE_2026-11-15.md`.
3. Library-protocol v1.7 (31 oktober 2026) is actueel. Verouderde vermeldingen als "actueel" zijn bijgewerkt; historische vermeldingen zijn behouden.
4. Geen herschrijving van de Git-geschiedenis. Vertrouwelijke infrastructuurwaarden zijn in de actuele documentatie vervangen door veilige verwijzingen naar register-ID's (bv. `<AF-HOST-0003-lan-ip>`). `split` weigert secties met zulke gegevens te archiveren, en CI faalt als een archiefbestand ze bevat. Er zijn geen echte wachtwoorden, tokens of privésleutels gevonden: alle treffers waren testfixtures of detectiecode.

Uitvoering stap 1 (mechanisch archiveren) volgt in een aparte PR per repository, zodra de betrokken bestanden niet meer door open A7-/systemd-/agent-PR's worden gewijzigd.

Doel: het bestaande GitHub-geheugen kleiner, actueler en efficiënter maken, zonder informatieverlies, zonder tweede beheersysteem en zonder nieuwe infrastructuur.

## 1. Nulmeting (main, 2026-11-15)

| Bestand | Tekens nu | Streefwaarde | Gedateerde secties | Oudste | Na stap 1 (simulatie) |
|---|---:|---:|---:|---|---:|
| `AGENTS.md` | 27,545 | 10,000 | 7 | 2026-10-14 | 27,545 |
| `handover/CURRENT_STATE.md` | 594,317 | 20,000 | 324 | 2026-09-21 | 75,828 |
| `handover/SESSION_HANDOFF.md` | 489,100 | 10,000 | 259 | 2026-09-24 | 36,258 |
| `roadmap/ROADMAP.md` | 427,824 | 25,000 | 210 | 2026-10-06 | 99,351 |
| `handover/AGENT_EXCHANGE.md` | 192,537 | 15,000 | 132 | 2026-09-22 | 287 |
| `decisions/DECISIONS.md` | 3,966 | 60,000 | 3 | 2026-10-16 | 3,966 |
| `handover/NEXT_ACTION.md` | 53,104 | 10,000 | 33 | 2026-10-10 | 2,317 |
| `roadmap/DEPENDENCIES.md` | 182,782 | 15,000 | 109 | 2026-09-30 | 37,080 |
| `claude_feedback/CURRENT_ASSIGNMENT.md` | 103,276 | 10,000 | 2 | 2026-09-22 | 103,276 |

**Context die een agent bij de verplichte opstart moet lezen** (leesvolgorde uit `AGENTS.md`):

| Toestand | Tekens | ≈ tokens |
|---|---:|---:|
| Nu | 2,021,347 | 505,336 |
| Na stap 1 (mechanisch archiveren, gesimuleerd) | 383,591 | 95,897 |
| Na stap 1 + compacte `AGENTS.md` (9,103 tekens) | 365,149 | 91,287 |
| Doel na stap 2 (alle streefwaarden gehaald) | ≤ 165,000 | ≤ 41,250 |

Tokens zijn geschat als tekens/4. De simulatie draaide op een kopie, met `split` + `verify-split`: alle gesplitste bestanden waren aantoonbaar verliesvrij (SHA-256 van de reconstructie = origineel).

## 2. Belangrijkste bevindingen

1. **Drievoudige duplicatie.** 160 secties staan letterlijk in meer dan één van `CURRENT_STATE`, `SESSION_HANDOFF` en `ROADMAP`: 594,193 dubbele tekens. Dezelfde dagboeksectie wordt dus twee- tot driemaal gelezen.
2. **Dagboek in plaats van toestand.** De laatste 7 dagen kwam er per dag ongeveer 7,036 tekens bij in `CURRENT_STATE`, 6,934 in `SESSION_HANDOFF` en 6,376 in `ROADMAP`. Mechanisch archiveren alleen haalt de streefwaarden daarom niet. De schrijfwijze moet veranderen: bijwerken in plaats van toevoegen.
3. **De echte roadmap is klein.** De ongedateerde, duurzame roadmaptekst in `ROADMAP.md` is ongeveer 54,439 tekens. De rest zijn gedateerde statuskopieën.
4. **`AGENTS.md` wordt automatisch ingeladen** (27,545 tekens). Er staan regels dubbel in (NL en EN versie van dezelfde bewijs-hergebruikregel; overlappende topologie- en bedieningsrouteregels). Het compacte voorstel is 9,103 tekens en neemt de veiligheidsregels letterlijk over.
5. **Vertrouwelijke gegevens.** `CURRENT_STATE` en `SESSION_HANDOFF` bevatten een home-pad van een testgebruiker (1 unieke waarde). Waarschijnlijk een wegwerp-testaccount, maar in een publieke repository verdient het controle. Geen privé-IP's gevonden.
6. **Inconsistente verwijzing naar de Library-standaard.** De toolblokkaderegel noemt v1.7, elders staan v1.6 en v1.2 als actueel. Dit voorstel lost dat niet stilzwijgend op; de eigenaar beslist.

## 3. Wat deze PR toevoegt (geen actieve bestanden gewijzigd)

- `tools/doc_memory/doc_memory.py`: alleen standaardbibliotheek, subcommando's `measure`, `check`, `split` en `verify-split`.
- `tools/doc_memory/budget.json`: streefwaarden; alle bestanden in modus `advisory`.
- `tests/test_doc_memory.py`: test verliesvrijheid, detectie van gewijzigde archieven en gebroken links, en dat `advisory` nooit blokkeert.
- CI: Alleen `tests/test_doc_memory.py` in de bestaande job *Ruff and pytest*. Er is bewust **geen** wijziging aan `.github/workflows/` of `scripts/`: die paden vereisen in deze repository een release-versiebump en zouden concurreren met de versiereserveringen van #1003/#1004. Het script staat daarom in `tools/doc_memory/`.
- `docs/agents/AGENTS_COMPACT_PROPOSAL.md`: voorstel voor een compacte `AGENTS.md`.

**Waarom dit andere PR's niet blokkeert:** groottegrenzen geven alleen een waarschuwing. Een fout volgt alleen als een gearchiveerde sectie (via een manifest) gewijzigd of verwijderd is. Op dit moment bestaan er nog geen manifesten.

## 4. Verliesvrije archiveringsmethode

1. `split BESTAND --keep-since JJJJ-MM-DD` deelt op `## `-koppen (buiten codeblokken). Alleen **gedateerde** secties ouder dan de datum gaan ongewijzigd naar `BESTAND.archive-JJJJ-MM.md` in dezelfde map, zodat relatieve links blijven werken. Ongedateerde secties (vaste roadmapfasen, `Current assignment`, ...) blijven altijd in het actieve bestand.
2. Een manifest `BESTAND.split-DATUM.doc-memory.json` legt per sectie vast: SHA-256, lengte, kop, datum en bestemming. Daarnaast de SHA-256 van het origineel en van elk uitvoerbestand.
3. `verify-split --original git:REV:pad` reconstrueert het origineel byte voor byte en vergelijkt de hashes. Het controleert ook dat alle issue-/PR-nummers, URL's, 40-tekens-SHA's en relatieve links behouden blijven, dat links vanaf de nieuwe plek werken, en meldt inkomende `bestand#anker`-links naar verplaatste koppen.
4. `check` (in CI) controleert bij elke PR dat elke gearchiveerde sectie nog byte-identiek bestaat. Archieven zijn dus alleen-aanvullen; historisch bewijs kan niet ongemerkt verdwijnen.
5. Bovenaan het actieve bestand komt één vaste verwijzing naar de archieven. Er worden geen nieuwe taak- of beslissings-ID's ingevoerd; zoeken gebeurt op de bestaande issue-/PR-nummers, SHA's en datums.

## 5. Gefaseerd migratieplan

**Stap 0 — deze PR.** Tools, tests, advisory-CI en voorstellen. Geen inhoudelijke wijziging.

**Stap 1 — mechanisch archiveren** (per repo één kleine PR, alleen verplaatsen). Pas uitvoeren als de afhankelijkheden vrij zijn (§6). Voorgestelde grens: `SESSION_HANDOFF` alles vóór 2026-11-13; `CURRENT_STATE`, `ROADMAP` en `DEPENDENCIES` (Runner-MCP ook `NEXT_ACTION`) vóór 2026-11-08. `AGENT_EXCHANGE` **niet** op datum archiveren: open claims eerst handmatig markeren. Na merge: `verify-split` met `git:<merge-basis>:pad` als origineel, resultaat vastleggen in de handover.

**Stap 2 — toestand in plaats van dagboek** (inhoudelijk, met review). `CURRENT_STATE` krijgt één bijgewerkte sectie *Actuele toestand* per lane (status, blocker, volgende actie, bewijs-ID's). `SESSION_HANDOFF` bevat alleen de laatste overdracht. Grote grotendeels ongedateerde bestanden (Runner-MCP `claude_feedback/CURRENT_ASSIGNMENT.md`) worden hier inhoudelijk ingekort. Dubbele tekst wordt vervangen door een verwijzing. Dit is samenvatten, dus eerst als voorstel-PR met een onafhankelijke reviewer (Claude/Qwen), en pas daarna archiveren. Het origineel blijft via stap 1 integraal bewaard.

**Stap 3 — compacte `AGENTS.md` activeren** na goedkeuring door de eigenaar. Het huidige bestand wordt byte-identiek `docs/agents/AGENTS_FULL_2026-11-15.md` (SHA-256 gecontroleerd); de bootstrap-volgorde verwijst naar alleen-actief-lezen.

**Stap 4 — grenzen aanscherpen.** Per gemigreerd bestand de modus van `advisory` naar `no_growth`, en later `enforce`. Niet-gemigreerde bestanden blijven `advisory`.

**Meten na elke stap:** `python3 tools/doc_memory/doc_memory.py measure` voor en na, en het resultaat in de handover vastleggen.

## 6. Afhankelijkheden — waarom de echte migratie nu nog niet gebeurt

- Open PR's die dezelfde bestanden wijzigen: #1004 (0.1.175 wheel-custody) en #1003 (#866 cron/systemd-fases) wijzigen `CURRENT_STATE`, `SESSION_HANDOFF` en `ROADMAP`. Een split nu zou merge-conflicten veroorzaken in actief A7-/#866-werk.
- Veilig moment: geen open PR meer die deze bestanden raakt, of een afgesproken kort venster waarin agents geen handovers schrijven. Bij merge-conflicten later: het actieve bestand opnieuw splitsen vanaf de nieuwe main, nooit archiefsecties handmatig samenvoegen.
- Geen invloed op A7, automatische updates of de systemd-migratie: deze PR wijzigt geen bron in `src/`, geen release-/updatecode en geen hostgedrag.

## 7. Geldigheidsregels per type informatie

Zie §6 van het compacte `AGENTS.md`-voorstel. Kort: stabiel = hergebruiken; semi-stabiel (geïnstalleerde revisie/wheel, cron/systemd) = gericht herverifiëren na deploy/herstart; dynamisch (PID, poort-eigenaar, online-status, lease) = altijd actueel op de exacte doelserver vóór een risicovolle wijziging; bewijs (CI-run, ACK) = gebonden aan de exacte SHA. Vertrouwelijke infrastructuurgegevens blijven in de private AIfordable-autoriteit en worden alleen met hun register-ID vermeld.

## 8. Open beslissingen voor de eigenaar (beslist op 2026-11-15, zie §0)

1. Akkoord met de archiefgrenzen uit stap 1?
2. Akkoord met het compacte `AGENTS.md`-voorstel (rangorde, letterlijk overgenomen veiligheidsregels)?
3. Welke versie van de Library-standaard is actueel (v1.2 / v1.6 / v1.7)?
4. Hoe de gevonden vertrouwelijke waarden opruimen: alleen uit de actieve bestanden halen, of ook uit de Git-geschiedenis? Het laatste is een destructieve actie en dus een aparte beslissing.
