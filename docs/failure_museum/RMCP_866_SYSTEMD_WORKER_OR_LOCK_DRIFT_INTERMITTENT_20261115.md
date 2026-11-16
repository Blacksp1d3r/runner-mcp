# Runner-MCP #866 — wisselvallige systemd-test: `worker_or_lock_drift`

- **Registratiedatum:** 2026-11-15
- **Scope:** bestaande cron→systemd-user-migratie [#866](https://github.com/Blacksp1d3r/runner-mcp/issues/866); geïsoleerde systemd-test, **geen geconstateerde originele-hoststoring**
- **Status:** `REPORTED_INTERMITTENT / CAUSE_UNVERIFIED`
- **Eigenaar vervolgdiagnose:** bestaande #866-werkstroom / [draft-PR #1003](https://github.com/Blacksp1d3r/runner-mcp/pull/1003); niet overnemen van de actieve bronbranch
- **Wijzigingsscope van dit record:** uitsluitend documentatie; geen testharnas, cron, systemd-unit, CI-configuratie, Runner-MCP, A6 of A7 aangepast

## Gemelde waarneming

Tijdens de voorbereiding en validatie van de afzonderlijke doc-memory-PR [#1006](https://github.com/Blacksp1d3r/runner-mcp/pull/1006) meldde de uitvoerende agent op 15 november:

> In MCP faalde de systemd-test één keer met `worker_or_lock_drift` en slaagde bij een herhaling.

Deze uitspraak is de **oorspronkelijke beschikbare melding**, niet een door deze registratie herhaalde test. De bijbehorende mislukte log, exacte testnaam, commit-SHA, CI-run-/job-ID, kloktijd, hostgeneratie en herstartconditie waren **niet meegeleverd**. Daardoor zijn herhaalbaarheid, oorzaak en exacte testfase **NIET BEWEZEN**.

## Afgebakende onafhankelijke GitHub-readback (2026-11-15)

- Op doc-memory-branch `docs/doc-memory-budget-20261115` zijn officiële [validation #43702400920](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43702400920), [#43702770708](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43702770708), [#43703068170](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43703068170) en [#43705218076](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43705218076) `SUCCESS`; de afzonderlijke disposable systemd-user-lifecycle-jobs waren daarin eveneens `SUCCESS`. De ingeziene joblogs tonen de normale M2 PASS-markers, **niet** het gemelde mislukte `worker_or_lock_drift`-moment.
- Op de actieve systemd-bronbranch is [validation #43696306023](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43696306023) `FAILURE`, maar met **vijf andere, concrete unit-asserties**: verwacht `original_cron_role_unqualified`, ontvangen `original_managed_block_unqualified`. Dat is **geen bewijs** voor deze intermittent-waarneming. De latere [validation #43696617856](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43696617856) is `SUCCESS`, op **andere HEAD**, dus ook geen identieke herhaling van de gemelde fout.
- Zowel het mislukte moment als de oorzaak van `worker_or_lock_drift` blijven voor deze audit **onafhankelijk onbevestigd**. Een groene herhaling alleen bewijst niet dat een mogelijk race-/timingprobleem opgelost is.

## Foutsignatuur en risico

**Foutsignatuur (gemeld):** `worker_or_lock_drift`, in de bestaande systemd-user-/gedeelde-cronlock-kwalificatie. De precieze emitter en voorwaarden moeten nog uit het falende log of een gerichte code-/testroute worden aangetoond.

**Mogelijke hypotheses — niet als oorzaak vastgesteld:** overgang tussen procesgeneraties of systemd-state, asynchrone worker-PID/lock-observatie, timing rond stop/restart, of een werkelijk gewijzigd lock-/workercontract. Zonder originele bewijsregel mag dit niet als “alleen flakiness” worden weggezet.

**Impact:** mogelijk onbetrouwbare CI-acceptatie of een werkelijke regressie die door nieuwe starts onzichtbaar wordt. **Niet aangetoond:** dubbele uitvoering, verloren cronregels, mislukte rollback of productiefout. De oorspronkelijke `AF-HOST-0001`-cutover blijft onafhankelijk van dit onderzoek geblokkeerd op zijn bestaande #866/A7-poorten.

## Volgende gerichte controle bij een nieuwe waarneming

1. Bewaar de **eerste** falende testuitvoer vóór een rerun: exacte opdracht/testnaam, HEAD-SHA, CI-run/job-ID of lokaal test-ID, timestamp/tijdzone, exitstatus en de originele **geredigeerde** `worker_or_lock_drift`-regels. Geen gevoelige host-/gebruikerspaden of credentials kopiëren.
2. Vergelijk uitsluitend rond die mislukte fase de reeds bestaande testobservaties: verwachte versus feitelijke systemd `ActiveState`/`MainPID`/procesgeneratie, werkelijke gedeelde `flock`-toestand, cronrol en functionele test-ACK, met tijdstippen en dezelfde fixture-input.
3. Stel de **vroegste afwijking** vast. Splits een echte worker-/lockcontractregressie van een test-harness-race; voer alleen een kleine causale correctie in de bestaande #866-branch uit met een gerichte negatieve/positieve regressietest.
4. Aanvaard pas `RESOLVED` wanneer hetzelfde exacte scenario reproduceerbaar/verklaard is, de correctie faalt op de slechte variant en slaagt op de goede, plus verplichte exacte-HEAD-CI. **Niet** de foutcontrole uitschakelen, vaste `sleep` toevoegen zonder bewijs, CI blind blijven herhalen of productieactivering uitvoeren.

## Geen herhaling van bestaand onderzoek

Zie het andere, **onafhankelijke** incident [RMCP_866_CANDIDATE_DELTA_NOT_VERIFIED_20261114.md](RMCP_866_CANDIDATE_DELTA_NOT_VERIFIED_20261114.md): dat gaat over onjuiste éénrols-cron-kandidaatvalidatie en bevat al een causale bronfix. Dat is niet dezelfde fout. Hergebruik bovendien de geslaagde M2/M3-disposable-proeven van #866 zonder ze onnodig opnieuw te draaien.

**Acceptatiestatus van deze registratie:** incident **VASTGELEGD**, oorzaak **ONBEKEND**, aparte oplossing **NIET GETEST**. Aanvullen in ditzelfde museumrecord bij het eerstvolgende concrete bewijs; geen tweede Failure Museum of beheerregister oprichten.

## 2026-11-16 — werkelijke cron-minuutstart en kernel-lockeigenaar bevestigd

**Nieuw VERIFIED mechanisme; de twee eerdere incidentele fouten zijn NIET met een PID-witness herleid.** De bestaande #866-eigenaar heeft zonder original-hostacties één gericht test-only experiment toegevoegd in de geïsoleerde, niet-root GitHub-hosted Linux-proef. De officiële code-HEAD was `d01ec05d9e95b301850e23b5973408142a434abf`, [validatie](https://github.com/Blacksp1d3r/runner-mcp/commit/d01ec05d9e95b301850e23b5973408142a434abf/checks). De eigen systemd-lifecycle-job (GitHub job `133429576086`) was **SUCCESS**. De proef gebruikte de bestaande `render_cron_block`, `run_cron_component`, echte door de crondaemon geactiveerde test-crontab, dezelfde `flock` en exact één wegwerp-`github-watcher` zonder netwerk- of echte taken.

**Geobserveerd bewijs in de officiële joblog:** `M3_REAL_CRON_MINUTE_OWNER=PASS pid=2639 second=1` op **2026-11-16 16:11:01 UTC**. De PID had via de werkelijke procfs-parentketen de crondaemon als voorouder, laadde de exact toegestane test-executable en stond als **enige FLOCK ADVISORY WRITE-eigenaar** voor het vaste test-lock-inode in `/proc/locks`. Een gelijktijdige tweede `autostart cron-run github-watcher` leverde **geen tweede startrecord/worker** op: `M3_REAL_CRON_LOCK_WAIT_AND_SECOND_EXEC_DENIED=PASS`. De bestaande `before_exclusion`-checkpoint gaf bij die aantoonbaar rechtmatige cronworker **`consistent=False`, `worker_or_lock_drift`**, dus **fail-closed vóór een verboden parallelle omschakeling**. Dit is een juiste blokkering van een nog bezette gedeelde lock, niet automatisch een productiefout.

**Begrensde interpretatie:** de originele twee gemelde CI-fouten gebeurden rond de minuutgrens en passen technisch bij dit mechanisme, maar hun specifieke eerdere lockeigenaar/PID werd destijds niet vastgelegd. Hun exacte causaliteit blijft daarom `UNVERIFIED`; géén claim van bewezen root cause voor die twee jobs. Bewijs uit de gerichte test geldt uitsluitend voor de opgewekte fixture op deze wegwerp-host en is geen originele fysieke host-/A7-/herstelkwalificatie.

**No-repeat / CI-kosten:** de gerichte minuutproef gebruikt een kernel-gewachte gebeurtenis (`select`) en géén sleeps, retries of verzwakte exclusiviteit. Na SUCCESS staat zij **standaard UIT** op #866 draft-head `b83da6aeeb188b54d9c47feb52ded8cfd02655bf` en kan uitsluitend binnen dezelfde disposable gate expliciet als `RUNNER_MCP_866_MINUTE_PROBE=true` worden geactiveerd. Zo ontstaat géén permanente 60-secondenlast per validatie. Productielogica/algemene autostart, echte cron/systemd, A7-updater/worker en serverrechten bleven onveranderd. Een uitgeschakelde opt-in-test is niet automatisch bewijs voor de nieuwe HEAD; de eerdere concrete run is de positieve attestatie. Originele M3-activering blijft geblokkeerd op alle bestaande host-, A7-, rollback- en writer-exclusiviteitsgates.
