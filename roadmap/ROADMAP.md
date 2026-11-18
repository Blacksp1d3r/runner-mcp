<!-- doc-memory:archive-pointer -->
> **Actief bestand.** Oudere gedateerde secties staan ongewijzigd in `roadmap/ROADMAP.archive-*.md` (manifest met SHA-256 per sectie ernaast). Lees die niet standaard; zoek gericht, bv. `grep -n "#1234"`.
>
> **Nog open werk waarvan de historie in het archief staat** (open issue/PR op het moment van archiveren; status volgt GitHub):
> - #757 Release admission: enforce required main check, freshness and prove merge denial — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
> - #739 F30 Black: private GitHub Release bytes importer with one-time read-only auth and immutable offline  — laatst 2026-11-06 in `roadmap/ROADMAP.archive-2026-11.md`
> - #735 First-host bootstrap: explicit local setup prerequisite and safe Agent Bus not-initialized status — laatst 2026-10-17 in `roadmap/ROADMAP.archive-2026-10.md`
> - #725 Security compatibility: redact new stateless GitHub App ghs_ installation JWTs — laatst 2026-10-20 in `roadmap/ROADMAP.archive-2026-10.md`
> - #665 Protocol tool identity, exact build negotiation and automatic mismatch alerts — laatst 2026-10-20 in `roadmap/ROADMAP.archive-2026-10.md`
> - #664 Compatibility: stable legacy tool contracts across customer Runner-MCP versions — laatst 2026-10-20 in `roadmap/ROADMAP.archive-2026-10.md`
> - #662 Release conveyor: unique version per tool change and gated automatic promotion — laatst 2026-11-07 in `roadmap/ROADMAP.archive-2026-11.md`
> - #653 docs(#341): exact A6 diagnosis and two-host security release gates — laatst 2026-10-23 in `roadmap/ROADMAP.archive-2026-10.md`
> - #642 F30: enforce qualified host-local tool denial at MCP dispatch without changing the shared catalogue — laatst 2026-10-10 in `roadmap/ROADMAP.archive-2026-10.md`
> - #634 BPA-02B: qualify local Git/storage authority before root project manifest — laatst 2026-10-10 in `roadmap/ROADMAP.archive-2026-10.md`
> - #630 Repository blueprint: incremental legacy compatibility adoption — laatst 2026-10-10 in `roadmap/ROADMAP.archive-2026-10.md`
> - #617 Recovery #531-D: operator-authorized bounded poison replay and audit — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
> - #616 Recovery #531-C: quarantine-aware watcher cursor without lost requests — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
> - #615 Recovery #531-B: crash-atomic quarantine custody and invariant tests — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
> - #590 Connector: runtime_status and runtime_doctor fail internally before runtime evidence — laatst 2026-10-27 in `roadmap/ROADMAP.archive-2026-10.md`
> - #587 I5/F34: mirror only the protected Runner Fabric release set to independent custody — laatst 2026-10-24 in `roadmap/ROADMAP.archive-2026-10.md`
> - #585 Ops: fixed independent-volume custody for protected Runner Fabric release archives — laatst 2026-10-22 in `roadmap/ROADMAP.archive-2026-10.md`
> - #584 Isolated runner admission gate (optional public-repo CI migration) — laatst 2026-10-17 in `roadmap/ROADMAP.archive-2026-10.md`
> - #537 Bewind: harden OCR qualification measurement before live run — laatst 2026-10-09 in `roadmap/ROADMAP.archive-2026-10.md`
> - #531 Prevent recurrence: quarantine poison recovery items without blocking watcher convergence — laatst 2026-10-20 in `roadmap/ROADMAP.archive-2026-10.md`
> - #489 Platform-neutral Runner MCP runtime with first-class Windows host support — laatst 2026-10-09 in `roadmap/ROADMAP.archive-2026-10.md`
> - #458 Lab: run Faster-13 shadow benchmarks on hosted CI — laatst 2026-10-09 in `roadmap/ROADMAP.archive-2026-10.md`
> - #383 FASTER-13: benchmark local MCP fast path and remove avoidable polling — laatst 2026-10-16 in `roadmap/ROADMAP.archive-2026-10.md`
> - #381 Bounded service alias for AIfordable subscription coding worker lifecycle — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
> - #333 Ops: make tunnel readiness and restart fail visibly — laatst 2026-10-16 in `roadmap/ROADMAP.archive-2026-10.md`
> - #297 Ops: detect stale connector tool catalog after self-update — laatst 2026-10-28 in `roadmap/ROADMAP.archive-2026-10.md`
<!-- /doc-memory:archive-pointer -->

## 2026-11-14 — #866 v0.1.174: bronauthentieke zesrollen-cron ↔ systemd-fases ↔ exact rollback op echte disposable Linux PASS

**VOLTOOID bron/M2 + voorbereidende M3; NIET originele M3-activering:** [PR #1000](https://github.com/Blacksp1d3r/runner-mcp/pull/1000), exact geverifieerde head `664e014cda839aeb00358b9a99c59745fb7ace8b`, is na drie officiële terminal-SUCCESS workflows **MERGED** als `main 2686f2ebc6f0d8e999b410cf35a04a1da6b46df6`; versie **0.1.174 uitsluitend GitHub-bron**, niet de fysiek geïnstalleerde versie. Officiële [validation 43586169404](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169404), [Clean Ubuntu 43586169460](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169460) en [attribution 43586169471](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169471) alle SUCCESS, inclusief **4.812 pytest**, Ruff, echte disposable nonroot `systemd --user`, schone installatie, vijfminutendemo en release-artifact.

**Gevonden en herstelde fout in v0.1.173:** een ‘consistent’ in-memory migratievoorstel kon ten onrechte een andere cronrol verwijderen of een externe cronregel veranderen, als de aanroeper dezelfde foutieve kandidaat als waarneming opgaf. De nieuwe pure `_exact_single_role_cron_delta` herleidt opnieuw dat exact één juiste managed `cron-run`-regel binnen het ene beheerde blok verdwijnt, **alle andere bytes identiek** blijven en executable plus config-dir van de geselecteerde cronrol exact overeenkomen met de gegenereerde systemd-`ExecStart`. Negatieve tests met aangepaste vreemde regel, andere verwijderde rol en extra regel geven fail-closed. Dit was een bron-/testbevinding, geen geconstateerde fysieke productie-uitval. Zie bestaande Failure Museum onder `docs/failure_museum/RMCP_866_CANDIDATE_DELTA_NOT_VERIFIED_20261114.md`.

**Nieuwe echte geïntegreerde CI-proef:** `render_cron_block` genereert exact zes brongebonden cronrollen plus een vreemde regel en schrijft die op een geïsoleerde GitHub-host in een echte gebruikerscrontab. `plan_single_peer_systemd_migration` en `assess_single_peer_migration_checkpoint` doorlopen alle zes fases tegen werkelijk `crontab -l`, de bron-gerenderde enabled unit, `systemctl --user`-status, werkelijke MainPID, geërfde `flock` en **synthetisch test-taakrecord**. Slechts één watcher wordt uitgesloten; na gecontroleerd stoppen en wissen van zijn testunit komt precies de volledige oorspronkelijke zes+vreemde crontab terug. Letterlijk `M2_DISPOSABLE_SOURCE_RENDERED_SIX_ROLE_PHASE_CHECKPOINT_ROUNDTRIP=PASS`, naast acht eerdere M2 PASS-markers. Dit is géén echt Fabric-ACK, productie-executor of fysiek rebootbewijs.

**M3–M6 fysiek GEBLOKKEERD / NIET GETEST:** geen enkele oorspronkelijke cronregel, managed unit, proces, A6/A7, Agent Bus, relay of automatische update gewijzigd. Eerst echte `AF-HOST-0001` owner/UID, draaiende wheel/imported source, PID/startticks/kinderen/poort, volledige originele cronbytes, actieve cronreconciler en externe cron-afhankelijke monitors, A7-/offline-/reboot-rollback en **duurzaam echt werkresultaat+ACK** onafhankelijk kwalificeren. De zes oorspronkelijke cronrollen blijven actieve eigenaar. Het aflopen van M2-validatie maakt een fysieke omschakeling niet automatisch toegestaan.

---
## 2026-11-14 — #866 v0.1.173: alleen-lezen M3-fasecontrole weigert volledige cron-/unit-/procesdrift (CI PASS)

**VOLTOOID bron en CI, NIET fysieke M3-migratie:** [PR #998](https://github.com/Blacksp1d3r/runner-mcp/pull/998), exact gevalideerde head `786e7c1f2fa412008927f8a67b0baaac8c7386c2`, is **MERGED** als `main ede99e271983168d1f411ca31348b22d79c2f686`. Versie **0.1.173** uitsluitend bron. Officiële [Runner MCP validation 43584760593](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43584760593), [Clean Ubuntu 43584760565](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43584760565) en [commit attribution 43584760587](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43584760587) **alle terminal SUCCESS**, inclusief Ruff, **4.812 pytest**, echte disposable nonroot Linux `systemd --user`, vijfminutendemo en release-artifact. Eerste Ruff-fout uitsluitend twee tests-importformatregels hersteld op dezelfde PR-branch; nieuwe exacte PR-head volledig groen.

**Nieuw broncontract op reeds bestaande `plan_single_peer_systemd_migration`:** het zuiver in-memory voorstel bindt nu óók de exacte herstartbestendige `boot_unit_contents` aan de statische cron-`flock`-kandidaat; er wordt nog steeds geen managed-unit geschreven. `assess_single_peer_migration_checkpoint` beoordeelt **zes** afzonderlijke alleen-lezen fasen (`before_exclusion`, `ready_to_stage`, `staged_inactive`, `new_worker_ack`, `rollback_ready`, `rollback_confirmed`) tegen volledige oorspronkelijke of kandidaat-cronbytes, exacte bootunitbron/afwezigheid, enabled/active, proces-PID, lock- en nieuw functioneel ACK-signaal. Volledige cron-drifts (ook niet-beheerde regels), gewijzigde unitbytes, typefouten, status- of PID-afwijking, ontbrekende lock/ACK, en onbetrouwbaar gemuteerde preview geven fail-closed. Iedere uitslag — zelfs `consistent=True` — houdt `next_action_authorized=False`. Het zijn **door de aanroeper geleverde observaties**, dus geen echte host-/bron-/ACK-attestatie of toestemming voor uitvoering; geen systemctl, crontab of procesaanroep in deze functie.

**M3–M6 GEBLOKKEERD / NIET GETEST op het fysieke origineel:** De juiste `AF-HOST-0001` owner, werkelijk geïmporteerde wheel/source en actuele proces-/poortgeneratie, originele crontabbytes, cronreconciler/externe monitorcontracten, gecoördineerde A7-/offline-/reboot-rollback en duurzaam functioneel ACK moeten fysiek en onafhankelijk worden bewezen vóór een echte rol-voor-rol switch. Geen productie-actuator/automatische rollback geïmplementeerd. De zes echte cronrollen, A6/A7, Agent Bus, relay, automatische updates, serverprocessen en managed unitmap zijn **niet gewijzigd**. De parallelle automatische-updateschat behoudt het eigenaarschap.

---

## 2026-11-14 — #866 v0.1.172: enabled peer crasht na user-manager-herstart; blijvend exact cronherstel PASS (disposable)

**VOLTOOID — bron + M2/voorbereidende M3-negatieve test, NIET originele productiemigratie.** [PR #996](https://github.com/Blacksp1d3r/runner-mcp/pull/996) exact geteste head `8ffee67d867233d55680f39f350d129dc5e36bbe` is MERGED naar `main bf4eb7be4ef4ab473ff055e31378c87303b7e08e` als source **0.1.172**. Officiële [validation 43583504538](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43583504538), [Clean Ubuntu 43583504553](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43583504553), [attribution 43583504611](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43583504611) **alle terminal SUCCESS**; Ruff, **4.795 pytest**, echte disposable Linux `systemd --user`, schone installatie, vijfminutendemo en release-artifact PASS.

**Nieuwe negatieve bewijsvariant:** de bestaande echte, `enable --now` geactiveerde en over de managerherstart heen succesvol herstartte bron-gerenderde lockende *test*-peer krijgt uitsluitend op een disposable GitHub-host een `chmod 000` van zijn nep-executable. Alleen zijn exact gemeten test-MainPID wordt beëindigd. De echte systemd `Restart=on-failure`-route levert `Result=exit-code`, `MainPID=0`, **geen vijfde werkrecord** en nog steeds exact de vijf onaangeroerde cronfixture-rollen plus vreemde regel. De test voert vervolgens `disable --now`, herstel testbinary, lock-vrijgave, verwijderen test-owned unit en `daemon-reload` uit; herstelt **exact de volledige oorspronkelijke zes+vreemde crontab**; herstart zijn user-manager een **tweede keer** en bewijst géén systemd-heractivering, géén extra uitvoer en ongewijzigde cronbytes. Exacte marker: `M2_DISPOSABLE_BOOT_PEER_CRASH_RESTART_FAIL_AND_PERSISTENT_CRON_ROLLBACK=PASS`; alle zeven bestaande markers blijven PASS.

**GEBLOKKEERD / NIET GETEST op fysiek origineel:** Het herstel wordt door de **test** aangestuurd; géén automatische productie-rollback, hostreboot, rolmigratie, duurzame werk-ACK of externe monitoracceptatie. Voor echte M3–M6 blijft gerichte verificatie nodig van originele `AF-HOST-0001` service-UID, werkelijk geladen module/wheel/revisie, PID/startticks/children/poort, exacte volledige cronbytes, concurrerende supervisors/monitors, A7/offline/herstart-herstel, per-rol functionele ACK. Geen wijziging aan zes echte cronrollen, A6/A7, Agent Bus, relay of automatische updates. Niet alvast een disabled managed user-unit op het origineel plaatsen zolang cron daar reconcilet.

---

## 2026-11-14 — #866 v0.1.171: echt gegenereerde lockbehoudende boot-peer, disposable user-manager-herstart en exact cronherstel PASS

**VOLTOOID bron en echte disposable M2/voorbereidende M3-test; NIET originele productiemigratie:** [PR #994](https://github.com/Blacksp1d3r/runner-mcp/pull/994), exact geteste head `b910d506a47c4fca4c8fda797a3e9280e8bf22f8`, **MERGED** als `06ee4cb148ccb1ab03878fa70588d798ed02d331` en bronversie **0.1.171**. Officiële [validation 43582064047](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43582064047), [Clean Ubuntu 43582064027](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43582064027) en [commit attribution 43582064022](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43582064022) zijn **alle drie terminal SUCCESS**. Ruff, **4.795 pytest**, disposable non-root echte `systemd --user`, clean installer, vijfminutendemo en release-artifact PASS.

**Nieuw:** `render_boot_candidate_cron_peer_unit` is een **puur berekenende Python-functie**: zij hergebruikt byte-identiek de bestaande gevalideerde statische lockende peer (zelfde `autostart cron-run <role>`, geërfde `flock`, hardening, géén `Requires=runner-mcp.service`) en voegt enkel `[Install] WantedBy=default.target` toe. Er is **geen** nieuwe aansturingsservice, cron-write, systemctl-call of activeringsvergunning. Op de GitHub-hosted disposable Linux-testhost werden zes onschuldige `/usr/bin/true`-cronrollen + vreemde regel geplaatst, exclusief één watcher uit cron gehaald, die daadwerkelijk gerenderde kandidaat enabled en gestart, PID+werkrecord en enable-link bewezen, daarna **alleen de wegwerp-host haar user-manager** herstart en een nieuw manager-PID, worker-PID en volgend record bevestigd. Daarna nieuwe unit `disable --now`, vrijgave gedeelde lock, verwijderen test-unit, `daemon-reload` en **exact alle zes+vreemde cronregels** teruggeplaatst. Letterlijke marker `M2_DISPOSABLE_BOOTABLE_LOCKED_PEER_USER_MANAGER_RESTART_AND_ROLLBACK=PASS`; de zes eerdere M2-markers zijn eveneens PASS.

**GEBLOKKEERD / NIET GETEST:** Dit is echte *user-manager*-restart, **geen fysieke hostreboot**, geen productie-rollbacktransactie en geen oorspronkelijke M3–M6-activering. Echte `AF-HOST-0001`-host/UID/actief imported wheel+procesgeneratie+poort, volledige crontabbytes, actieve cron-/systemd-/andere monitorconsumenten, A7/offline recovery, duurzame functie-/resultaat-ACK en exclusieve operatorcutover vereisen apart geldig live-bewijs. Geen systeemunit of zelfs disabled managed peer stagen op de originele unitlocatie zolang cron daar draait. **Geen wijziging aan de zes echte cronrollen, oorspronkelijke host, A6/A7, Agent Bus, relay, Fleet-updateketen of automatische updates.**

---

## 2026-11-14 — #866 v0.1.170: mislukte systemd ExecStart met exact zesrollen-cronherstel op disposable Linux PASS

**VOLTOOID bron/M2-negatieve test; géén originele M3-activatie:** [PR #992](https://github.com/Blacksp1d3r/runner-mcp/pull/992) is na exacte PR-head `8a3563950599967d461a4530628a2b411241c50c` en drie officiële terminal-SUCCESS workflows [validation 43580599925](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43580599925), [Clean Ubuntu 43580599941](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43580599941), [attribution 43580599936](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43580599936) **MERGED** als `main 5505343a4cf9ae9a33a6598e89d3e234075e9577`, source-versie **0.1.170**. CI had Ruff PASS, **4.794 pytest PASS**, een echte disposable nonroot `systemd --user`-unit, schone Ubuntu, vijfminutendemo en release-artifact PASS. Geen uitrol of productiehostmutatie.

**Nieuw onafhankelijk negatievepadbewijs op bestaande disposable-testhost:** de bestaande zes onschuldige `/usr/bin/true`-cronrollen inclusief één vreemde cronregel worden exact geplaatst, alleen de gesimuleerde `github-watcher` wordt uit crontab gehaald. De reeds daadwerkelijk door `render_inactive_cron_server_peer_unit` berekende static systemd-unit wordt uitsluitend met een `chmod 000` van de test-only nep-executable onuitvoerbaar gemaakt. Na `systemctl --user start` moet de werkelijke manager `Result=exit-code`, `MainPID=0` en geen extra taakrecord tonen. De test stopt de mislukte unit, verwijdert het test-owned unitbestand, herlaadt de user-manager, herstelt de nep-executable en exact **zes plus vreemde** oorspronkelijke cronregels; controle op behoud van vijf niet-geselecteerde rollen, byte-identiteit en cleanup is PASS. Letterlijke marker: `M2_DISPOSABLE_FAILED_EXEC_START_EXACT_CRON_ROLLBACK=PASS`. Alle vijf voorgaande M2-markerproeven blijven PASS. Deze restore wordt door de **test** georkestreerd; er bestaat nog geen productie-autotransactie.

**OPEN/GEBLOKKEERD:** M3–M6 echte fysieke `AF-HOST-0001`-migratie: actuele host/service-UID, echt draaiende wheel/imported modules, rol-PID/startticks/children, poort, exact originele cronbytes, cron-/user-unitconflict, externe monitorconsumenten, functioneel resultaat+duurzame ACK en originele A7-/offline reboot-rollback. Staging van een zelfs inactieve managed unit op het origineel kan cron-reconcile blokkeren; geen enkele oorspronkelijke cronregel, A6/A7, Agent Bus, relay of automatische update gewijzigd. De onafhankelijke automatische-updateschat blijft eigenaar van die keten.

---

## 2026-11-14 — #866 v0.1.169 geïntegreerde zesrollen-cron + echt gegenereerde systemd-peer: disposable PASS

**VOLTOOID op bestaande GitHub-hosted disposable Linux; geen productiecutover:** [PR #990](https://github.com/Blacksp1d3r/runner-mcp/pull/990) met exact gevalideerde head `8910d3716fc277badda05bc48ef513eb9c1c55d6` is **MERGED** op `main 120b28e0b068d8230bf5a31e662f1ec805e54949`. Officiële [Runner MCP validation 43579198174](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43579198174), [Clean Ubuntu installer proof 43579198173](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43579198173) en [commit attribution 43579198238](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43579198238) **terminal SUCCESS**; Ruff, **4.794 pytest**, echte `systemd --user`, vijfminutendemo, schone installatie en release-artifact PASS. Versie 0.1.169 is uitsluitend GitHub-bron en testartifact, **niet** originele hostruntime.

**Nieuwe gezamenlijke M2-acceptatieproef:** De bestaande `scripts/qualify_systemd_user_lifecycle_ci.sh` gebruikt één non-root GitHub-hosted Linux-testuser met vooraf lege crontab, uitsluitend zes onschuldige `/usr/bin/true`-fixture-rollen en één vreemde regel. Met alle zes regels in de werkelijk geïnstalleerde testcrontab bezit een nep-watcher de echte `cron_autostart.run_cron_component`-lock via overgeërfde `flock/execv`. `systemctl --user start` van de daadwerkelijk door `render_inactive_cron_server_peer_unit` gegenereerde static-unit maakt bij die lock **geen tweede PID/werkrecord** en blijft `inactive`; een succesvol startcommando geldt niet als ACK. Daarna verdwijnt alleen die ene testcronregel: vijf rollen en de vreemde regel blijven exact. De oude worker wordt gedraind, dezelfde static-unit start met één nieuwe `MainPID` en bewijsrecord. Bij mislukte functionele toelating stopt de test de nieuwe rol, verifieert vrije lock, verwijdert het test-owned unitbestand en herlaadt systemd **vóór** exact herstel van de originele zes cronregels plus vreemde regel. Geen extra unit, cronregel of werkproces op de oorspronkelijke server. Letterlijke CI-marker: `M2_DISPOSABLE_SIX_ROLE_RENDERED_PEER_EXCLUSIVE_SWITCH_AND_ROLLBACK=PASS`.

**Fysieke M3–M6 nog OPEN/WAIT:** Echt `AF-HOST-0001`-/`<AF-SVC-0001-service-user>`-UID/role-to-source/wheel/PID/child/poort/generatiebewijs, origineel volledige cronbytes, gedeelde lock/uitsluitingsclaim, managerconflicten, onafhankelijke originele A7/herstart-/offline rollback en echte functionele result+duurzame ACK blijven per rol te kwalificeren. De oorspronkelijke zes cronrollen en A6/A7/Agent Bus/relay/automatische updates zijn bij deze bron-/CI-test **niet aangeraakt**. Zet geen zelfs inactieve managed-unit op de originele user-unitmap en gebruik geen full-set `autostart install/remove/reconcile` voor één rol. De bestaande automatische-updateschat blijft zelfstandig eigenaar van die keten.

---

## 2026-11-14 — #866 ECHT gegenereerde systemd-peer vs overerfde cron-flock: real disposable PASS; source 0.1.168 MERGED

**VOLTOOID bron/M2 CI, niet originele productie:** [PR #988](https://github.com/Blacksp1d3r/runner-mcp/pull/988) sourcehead `e9567250576a3c6b75867ee90d8fdea305c35b4e`, officiële [validation 43577673346](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43577673346), [Clean Ubuntu 43577673291](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43577673291), [attribution 43577673286](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43577673286) **allemaal terminal SUCCESS**. De pytest-suite **4.794/4.794 PASS**, Ruff, echte disposable systemd-user, vijfminutendemo, release-artifact en schone Ubuntu PASS. **MERGED main `e51b2bfc51794dff61ddb9f4fcffdf79bbae1602`**, package/discovery/runtime 0.1.168 exact bronreadback PASS. Niet als actuele fysieke `AF-HOST-0001` installatie claimen.

**Nieuwe échte source-renderer integratie op alleen bestaande disposable Linux-host:** huidige `scripts/qualify_systemd_user_lifecycle_ci.sh` gebruikt enkel GitHub-hosted, nonroot systemd PID1 met eerder bewezen pre-existing cron-denial en eigen EXIT cleanup. Onder uniek `RUNNER_TEMP` een tijdelijk bronvenv, nep-`runner-mcp` zonder geheimen/netwerk en private config; neprol dispatcht **de echte `runner_mcp.cron_autostart.run_cron_component`** en het echte `fcntl.flock`/overgeërfde `execv`. De **daadwerkelijk uit `render_inactive_cron_server_peer_unit` geproduceerde** static `runner-mcp-github-watcher.service` draait via precies datzelfde argv; geen `Requires=runner-mcp.service`, geen `[Install]`, uitsluitend op test-user-unitmap. Teststart bij bezette lock resulteert in **geen tweede rol/PID/startrecord** en eindigt `inactive`. Na beëindigen/wachten op oude test-worker, lock read-only vrij, laat dezelfde systemd-unit exact één nieuwe `MainPID` en extra startrecord zien; daarna stop, MainPID=0, lock vrij, geen enabled unit of andere crontab. Exact job-output **`M2_DISPOSABLE_REAL_RENDERED_PEER_AND_SHARED_CRON_LOCK=PASS`** plus vorige drie PASS-markers incl. zesrol-schedulerrollback. Geen nieuw servicebeheer of testhost.

**Vervolg-gates M3–M6 blijven NIET GETEST op oorspronkelijke host:** de oude echte zes cronrollen blijven ongewijzigd. Een `systemctl start` met lockconflict kan SUCCESS melden terwijl unit `inactive` wordt; service-start is NOOIT functioneel ACK. Voor fysieke rol-voor-rol-cutover eerst actuele host/UID/imported wheel/port/procesgeneratie en huidige exacte cronbytes, onafhankelijke unitfile-conflict- en externe-managercontrole, enige old worker plus children drain, exacte rollback / A7 herstel en eerste echte same-campaign result+duurzame ACK kwalificeren; geen `autostart install/remove/reconcile` full-set voor een rol, geen inactieve managed unit naar originele `~/.config/systemd/user` zolang cron reconcilet. **GEEN** fysieke productie-activatie/update/cron-delete, geen wijzigingen Agent Bus/A6/A7 en deze #866 baan blokkeert de zelfstandige automatische updates niet.

---

## 2026-11-14 — #866 zes cronrollen → vijf cron + één systemd → exact herstel REAL DISPOSABLE PASS, v0.1.167

**SOURCE/CI VOLTOOID, NIET FYSIEK ORIGINEEL:** [PR #986](https://github.com/Blacksp1d3r/runner-mcp/pull/986), exact geteste head `64b85fef834d65e0f2bba9030e89d30a8349a415`, official [validation 43576189820](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43576189820), [Clean Ubuntu 43576188742](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43576188742), [commit attribution 43576188746](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43576188746) **ALLE TERMINAL SUCCESS**. De volledige Python-testsuite (4794/4794), Ruff, releasepoort, schone Ubuntu, echte geïsoleerde systemd-user, vijfminutendemo en release-artifact opnieuw PASS. **MERGED/main `aff9ce6863d780c04b8685a66540fb9bdae4f1a3`**, bron/discovery/runtime **0.1.167** teruggelezen. Geen originele hostdeploy of unit/cron-activatie.

**Eigen bestaande testinfrastructuur uitgebreid, niet verdubbeld:** `scripts/qualify_systemd_user_lifecycle_ci.sh` draait **uitsluitend** op wegwerp-GitHub-hosted Ubuntu, eis `GITHUB_ACTIONS=true`, `RUNNER_ENVIRONMENT=github-hosted`, nonroot systemd PID1 en vooraf lege crontab. De bestaande echte `systemd --user` test-unit en EXIT cleanup worden hergebruikt. De test maakt precies zes **onschuldige /usr/bin/true** cronregels in een managed-markerblok en één vreemde cronregel, vergelijkt echt `crontab -l`; sluit uitsluitend één gesimuleerde `github-watcher` uit, leest vijf overgebleven rollen plus exact vreemde regel terug; start één bestaande niet-enabled test-owned systemd-`sleep`-unit en leest echte `MainPID>0`; stopt die unit, leest `MainPID=0`, herstelt daarna de **volledige oorspronkelijke crontab exact**, verifieert zes rollen terug en ruimt alleen tijdelijke testtoestand op. Letterlijke CI-bevestiging: **`M2_DISPOSABLE_ONE_OF_SIX_CRON_TO_SYSTEMD_AND_FULL_ROLLBACK=PASS`**, plus eerdere `M2_DISPOSABLE_CRON_TO_SYSTEMD_TO_CRON_ROUNDTRIP=PASS` en `M2_DISPOSABLE_ACTUAL_SYSTEMD_RESTART_AND_UNIT_ROLLBACK=PASS`. Dit is een echte OS-scheduler/rollbackproef met synthetic role executables, **niet** een echte zesrollen functie/ACK- of rebootacceptatie.

**Afzonderlijke grenzen M3–M6 blijven OPEN:** bron 0.1.167 niet bewezen geïnstalleerd/ingeladen op fysieke originele `AF-HOST-0001`; actuele originele zes echte role process-PIDs/children en locks, exact werkelijke crontabbytes, eigenaar/private permissies, externe cron-consumenten, geen dubbelrol, A7 originele boot/revert, dezelfde updatecampagne-result+ACK, per-rol functionele activiteit en werkelijk fysieke herstartproef **NIET GETEST**. Oude fysieke :8000 en on-disk 0.1.88 baseline blijft historisch herbruikbaar, maar geen moderne imported-source-autoriteit. **Geen productiecron/systemd-cutover, geen unit op originele `~/.config/systemd/user` plaatsen (zelfs disabled managed marker blokkeert reconcile), geen volledige `autostart install/remove/reconcile` voor een enkele rol.** #866 vormt GEEN extra blokkade voor zelfstandig A7/automatische-updateswerk.

---

## 2026-11-14 — #866 v0.1.166 lockgedeelde inactieve systemd-nevenunit SOURCE MERGED; fysieke M3–M6 WAIT

**VOLTOOID SOURCE/CI; GEEN LIVE ACTIE:** [PR #984](https://github.com/Blacksp1d3r/runner-mcp/pull/984), exacte oorspronkelijke PR-head `7ce1ae8b6cb74b291d4be59172eaf8b6453269c8`, drie officiële workflows terminal **SUCCESS**: validation [43575111102](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43575111102) incl. **4794/4794 pytest**, echte Linux cross-`execv` `flock`-proeven voor 3 belangrijke rollen, Ruff, geïsoleerde bestaande echte systemd-user-cyclus, vijfminutendemo en artifact; schone Ubuntu [43575111055](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43575111055); attribution [43575111040](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43575111040). **MERGED `main eca7330b1c2a2bef77f1911a305623d5985dddba`**, pakket-/runtime-/discoveryversie **0.1.166**, daadwerkelijke bronreadback PASS. Niet werkelijk geïnstalleerd/geactiveerd op de oorspronkelijke server.

**Eén gerichte bronfix, geen tweede scheduler:** vorige `render_inactive_cron_server_peer_unit` gaf `ExecStart=<exe> --config-dir <config> <component> run`. Daardoor zou de systemd-kandidaat de oude `cron_autostart.run_cron_component`-flock omzeilen en met een nog actieve cronworker dezelfde rol uitvoeren. De bestaande **alleen-berekenende** migratiekandidaat gebruikt nu exact dezelfde `<exe> --config-dir <config> autostart cron-run <component>` als de oude cronwrapper; dezelfde owner-private `autostart-<component>.lock` wordt via `execv` aan de daadwerkelijke rol overgeërfd. De oorspronkelijke `run_cron_component`, normale systemd-user-multirole-installatie, alle zes cronregels, updateketen, Agent Bus en A7 blijven **ONVERANDERD**. Het pure `plan_single_peer_systemd_migration` verwerpt expliciet onbeschermd/direct-ExecStart, bewaart volledig rollback-crontab + SHA en retourneert `cutover_authorized=False`.

**Belangrijke limiet:** bij een bezette lock retourneert `cron-run` 0 zonder de rol te starten; deze statische unit kan dan `inactive` worden en start niet vanzelf opnieuw. Een geleverde kandidaat, afwezigheid van lock, status `active` of eerdere Linux proces-/bron-test is **GEEN** functioneel origineel rol-/proces-/client-ACK-bewijs. Exact huidige oorspronkelijke rol/child-PID, UID, actieve geïmporteerde bron/wheel, cronbytes, bewaarde echte herstelbron, exclusieve switch, poststartfunctie, A7 zesrollenrollback en dezelfde UPDATE ACK blijven onafhankelijk OPEN. De statische, managed-marker unit mag ook disabled **niet** in de live originele `~/.config/systemd/user` worden gestaged, omdat deze de bestaande cron-reconciler kan blokkeren. **Eerst disposable exclusieve één-rol omschakel- en rollbackproef; M3–M6 niet getest, geen productiebevoegdheid**. #866 is geen extra gate voor de afzonderlijke automatische updates.

---

## 2026-11-14 — #866 beperkte cron→systemd herstel-preview 0.1.165 SOURCE/CI GEMERGED, originele M3–M6 OPEN

**VOLTOOID bron / GEEN LIVE OMSCHAKELING:** [PR #982](https://github.com/Blacksp1d3r/runner-mcp/pull/982) exact geaccepteerde head `3ae16aea769fe696bb441881cc92caf1c65f16ec`; alle drie officiële workflows TERMINAL **SUCCESS**: [validation 43573158496](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43573158496) incl. 4790/4790 pytest, Ruff, echte geïsoleerde systemd-user lifecycle, schone vijfminutendemo en artifactbuild; [Clean Ubuntu 43573158445](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43573158445); [commit attribution 43573158447](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43573158447). **MERGED main `c347cec9f0e9284d362a9e74875d9a4649cf98ea`**, package/registry/runtime **0.1.165** en nieuwe bron op main exact teruggelezen. GitHub releasebron **NIET** als fysieke originele installatie claimen.

**Nieuw hergebruik in de BESTAANDE `autostart.py`:** `plan_single_peer_systemd_migration` combineert `plan_single_role_cron_exclusion` (#973, v0.1.159) en `render_inactive_cron_server_peer_unit` (#974, v0.1.160) zonder unitwrite, crontab-write, subprocess, activatie of parallelle manager. Exact read-only `AutostartMigrationPlan(PLAN_ONLY)` vereist, control/server/tunnel uitgesloten, oude volledige bytegetrouwe crontab als rollback plus SHA256 bewaard; kandidaat schrapt slechts één cronrol en bevat exact één statische nevenunit zonder `Requires=runner-mcp.service` en zonder `[Install]`. Vijf positieve nevenrolscenario's en elf fail-closed scenario's; geen nieuwe scheduler, relay, updater, registry of autoriteit. `cutover_authorized=False` ALTIJD. De kandidaat-unit is **uitsluitend geheugenbytes** en mag ook uitgeschakeld NIET in `~/.config/systemd/user` op originele host worden geplaatst: bestaande `has_managed_user_units()` en cron-reconcile zouden de andere vijf rollen kunnen hinderen.

**NIET GETEST/GEBLOKKEERD voor fysieke M0/M3–M6:** exacte actuele oorspronkelijke crontabbytes, alle zes echte rol-/proces- en PID-lockgeneraties, werkelijk geladen source/wheel/issuer, beheerde user-unit coexistentie, authentieke original-host boot-/rollbackproef en dezelfde echte updatecampagne-resultaat + duurzame ACK. Bestaande originele `AF-HOST-0001` owner/poort/PID/on-disk 0.1.88 historisch PASS blijft herbruikbaar maar vervangt geen live imported-source-readback. `0.1.165` niet live geattesteerd; A7-actor/ACK en productie-update blijven onder eigen zelfstandige updatechat. **Verbod op bulk `autostart install/remove/reconcile` voor een enkele rol blijft gelden.** De onafhankelijke automatische updates worden door #866 niet geblokkeerd en zijn niet gewijzigd. Volgende gerichte M3-ontwikkeling: exclusieve één-rol schedulerhand-off met echte old-process/lock/cadence/pid-state, host-readback en bytegetrouwe rollback, eerst disposable Linux; daarna afzonderlijke fysieke toelating.

---

## 2026-11-11 — #341 Runner-MCP 0.1.164 dubbele managed-supervisor preflight SOURCE MERGED; originele productie WAIT

**SOURCE VOLTOOID — NIET HERHALEN:** [Runner-MCP PR #980](https://github.com/Blacksp1d3r/runner-mcp/pull/980) exact geteste head `79fcb036d4aa58ff5afd06382a97046537941dab`, official [validation #43001648400](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43001648400), [Clean Ubuntu #43001648332](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43001648332) en [commit attribution #43001648186](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43001648186) **ALLE TERMINAL SUCCESS**. Source squash **MERGED `a63fc8ec423733153df7b3a06758bac71bfe2aeb`**, GitHub-main en packageversie **0.1.164** exact gecontroleerd. De volledige Python-/Ruff-regressies, echte disposable systemd-user, schone Ubuntu-installer, release-reservering, vijfminutendemonstratie en artifactbuild zijn geslaagd.

**GERICHTE VERBETERING:** al bestaande v0.1.163 managed cron/systemd-user SERVER-preflight werd uitsluitend bij `start()` gecontroleerd. Gedurende asynchrone bron-sync, lint/tests en wheel-staging kon de manager daarna verdwijnen. De bestaande `_restart_ready()` wordt nu **opnieuw** geraadpleegd ná de wheel/baseline-seal en onmiddellijk vóór `begin_transaction`. Verloren/inactieve/onleesbare manager → bounded `restart_supervisor_unavailable`, geen install-transactie/wheel-installatie/restartmarker, bestaand pre-install source-rollbackpad behoudt de baseline. Nieuwe negatieve test simuleert verlies ná geslaagde unit-test voor zowel cron als systemd-user. Dit verkleint alleen het tijdvenster, garandeert geen manager-levensduur ná die hercontrole en is **GEEN A7-bevestiging**. Geen tweede updater, daemon, relayer of service.

**FYSIEKE GRENS:** originele `AF-HOST-0001` owner `<AF-SVC-0001-service-user>` :8000 PID2202/startticks7503 fysiek geverifieerd 2026-11-11, originele `0.1.88` op disk/RECORD en bewaarde wheel/TAR-restore historisch PASS; NIET opnieuw testen zonder veranderde procesgeneratie. **0.1.164 NIET LIVE GEÏNSTALLEERD**; volledige werkelijk geladen wheel/source- en originele issuerbinding #669 OPEN; oorspronkelijke 4/4 A7-escrow, onafhankelijke boot-persistente zesrollen-restorer/rollback #943 OPEN; A6 echte exact dezelfde UPDATE-campagne-resultaat + duurzame originele ACK #942 OPEN (oudere disposable status-ACK is een andere scope). Verbonden Runtime/Fabric-continuïteit blijft `self_update_ready=false` / `fabric_continuity_status_configuration_unavailable`. **PRODUCTIE-UPDATE NIET GEKWALIFICEERD.** Geen ARM, SQL, cron-/systemd-cutover, source-activatie, backup, service of originele hostwijziging.

**SYSTEMD-MIGRATIE ONDER #866:** systemd-user blijft doel voor Linux; bestaande cron blijft actief totdat één rol per keer met originele UID, echt proces/poort, lock, functionele ACK en onafhankelijk rollbackpad aangetoond werkt. Het updatespoor blokkeert die aparte migratie niet en voert ze niet uit. Ontbrekende oude formele escrowbestanden worden zonder nieuwe concrete aanwijzing niet opnieuw gezocht.

---

## 2026-11-11 — #341 managed update supervisor-preflight 0.1.163 MERGED; #866 systemd-user is doel, cron faseert uit

**SOURCE/CI VOLTOOID — NIET HERHALEN:** [Runner-MCP PR #978](https://github.com/Blacksp1d3r/runner-mcp/pull/978) exact geteste head `2d1694c89f509e287c931cd749da7636e3e45104`, validation [42999039044](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42999039044), Clean Ubuntu [42999039016](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42999039016), attribution [42999038791](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42999038791) **alle drie SUCCESS**; squash **MERGED `58b0cafedd83bc22cb3a3a1cc65e5e2b65a0c229`**, originele GitHub-main exact gecontroleerd, package **0.1.163**. `SelfUpdateManager` hergebruikt de **al bestaande** 0.1.162 `managed_server_activation_status()` als read-only poort vóór `start()` een job mag maken, uitsluitend wanneer expliciet managed activation ingeschakeld is. Alleen één exacte beheerder van de MCP-SERVER, installed/enabled/active (cron of systemd-user) mag door; onbekend/inactief/ambigu/onleesbaar: **geen job/installer/restartmarker**. Statusvelden `managed_server_supervisor_ready/backend` zijn niet A7- of geladen-wheelbewijs. Bestaande niet-gemanagede reexec-route blijft ongewijzigd; nieuwe securitytests en werkelijke disposable systemd-test PASS. Er is geen tweede updater of service aangemaakt.

**EIGENAARSBESLUIT — SYSTEMD-FIRST:** [bestaand #866](https://github.com/Blacksp1d3r/runner-mcp/issues/866#issuecomment-6792825878) en aparte systemd-migratiechat zijn eigenaar van **gefaseerd cron → bestaande systemd --user** voor Linux-langlopers. Cron is uitsluitend tijdelijke compatibiliteit en wordt **per rol pas uitgeschakeld als de juiste systemd-processource, exclusieve rol-lock, poort, boot/rollback en herstel bewezen zijn**. Deze updatebron-PR migreert of installeert NIETS en mag geen cron uitbreiden. Black/Blacky/LAB/Windows zijn afzonderlijke doelen; Windows gebruikt Task Scheduler. De bestaande single-role cutover uit #866 nog niet live aanroepen; geen dubbele supervisorgeneraties.

**LIVE AFBAKENING:** originele `AF-HOST-0001` owner `<AF-SVC-0001-service-user>` :8000 PID2202/startticks7503 fysiek 2026-11-11 dezelfde 0.1.88-generatie, on-disk versie/RECORD en historische wiel/TAR-herstelproef PASS. **0.1.163 is NIET geïnstalleerd**, actieve wheel/source-identiteit #669 NIET ATTESTED, A7 originele onafhankelijke zesrollenrollback/formeel 4/4-escrow #943 OPEN, originele A6 dezelfde UPDATE-result/ACK #942 OPEN. Geen originele process-, cron-, systemd-, backup-, ARM- of credentialmutaties. `PRODUCTION_UPDATE_AUTHORIZED=FALSE`. Bronacceptatie is niet productieacceptatie.

---

## 2026-11-11 — #341 retained rollback-wheel SOURCE 0.1.161 MERGED/CI PASS; fysieke originele UPDATE WAIT

**SOURCE/CI VOLTOOID — NIET HERHALEN:** [Runner-MCP PR #975](https://github.com/Blacksp1d3r/runner-mcp/pull/975) exact geteste head `0a9aa301ea3f689eb8b8d7b8862a743ffbfd07e6`, volledige [validation CI #42982913614](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42982913614) **SUCCESS** (Ruff/volledige pytest, release-reservering, geïsoleerde echte systemd, vijfminutendemonstratie en candidate-build), [Clean Ubuntu #42982883670](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42982883670) **SUCCESS**, [attribution #42982911862](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42982911862) **SUCCESS**; squash **MERGED `fcebbd34ce4c1764d663e8be4aecda6ecbfe95e4`**, GitHub `main`, packageversie `0.1.161`, bestaande bron `self_update_install.py` blob `e8cca9437e8493c157299ce49b360178b59cac45` en regressietests blob `00a25b89236d882cc986efc956bc70e714273112` exact herlezen. #973 v0.1.159 en #974 v0.1.160 waren reeds gemerged en zijn NIET overschreven. De eerste bronhead met v0.1.160 werd door de **juiste** release-reservering tegen #974 geweigerd; oorzaak vastgelegd in bestaand [#341](https://github.com/Blacksp1d3r/runner-mcp/issues/341#issuecomment-6790343266). Er is nooit geprobeerd de reservering te omzeilen.

**BESTAANDE WERKING HARDER GEMAAKT, GEEN NIEUWE ACTOR:** `SelfUpdatePackageInstaller.staged_wheel_sha256()` bindt het originele behouden baseline-wheel aan één `O_NOFOLLOW`-FD en vergelijkt dev/ino/mode/uid/gid/nlink/size/mtime/ctime vóór/tijdens/na hashen en tegen de originele pathname. Metadatawijziging met byte-identiek wheel en ontbrekende symlinkbescherming leveren veilig `None` op. Dit is een **lokale rollback-wheelseal**, geen bewijs van geïmporteerde Python-code of authentieke wheel-source op het originele proces.

**LAATSTE FYSIEKE OORSPRONKELIJKE #669 — HERGEBRUIKEN:** echte `AF-HOST-0001` `<AF-SVC-0001-service-user>`, loopback :8000, Python3.12, PID `2202` + startticks `7503` op 2026-11-11 **SAME_GENERATION=TRUE** als 9-november op dezelfde fysieke machine; on-disk v0.1.88/RECORD en historische officiële wheel 131/131, originele escrow-/isolatierestore bestanden blijven PASS. De actieve in-memory wheel/source binding blijft **NOT ATTESTED**, geen herhaalde PID/wheel/backup-scan. De verbonden 0.1.88 MCP-tool geeft nog `active_artifact_digest=null` en `self_update_ready=false`. Bronversie 0.1.161 is **NIET fysiek geïnstalleerd**.

**VOLGENDE OPEN POORTEN:** oorspronkelijke #669 loaded source/wheel/issuer, #341 + Fabric A7 #943 originele onafhankelijk geïnstalleerde, boot-persistente zes-real-role-herstelactor en formele 4/4 escrow, Fabric A6 #942 authentieke exact dezelfde UPDATE-campagne voorbereidingsreceipt, uitval/herstel en originele requester terminal result + duurzame ACK. Afzonderlijk behaalde Black-noNIC runtime+hele-crontab rollback en originele A6-disposable runtime_status/ACK zijn NIET hetzelfde bewijs. `PRODUCTION_UPDATE_AUTHORIZED=FALSE`, geen oorspronkelijke server-/service-/cron-/back-up-/ARM-/credentialwijziging.

---

## 2026-11-11 — #866 één-rol cron→systemd BRON 0.1.159/0.1.160 MERGED; LIVE NIET GETEST

**SOURCE/CI VOLTOOID:** [PR #973](https://github.com/Blacksp1d3r/runner-mcp/pull/973), v0.1.159, exact-head `c25eaa34fe84a3c6ed2af8f224298a92603fb94a`, validation `42981553411`, clean Ubuntu `42981553376`, attribution `42981553386` SUCCESS; MERGED `cc736f79313b55bf24e80e70529e16fb394a7c41`. `cron_autostart.py` berekent uit de exact brongebonden originele managed crontab een kandidaat zonder één rol en bewaart de originele bytes, vijf andere rollen en vreemde cronregels. Positieve/negatieve regressies PASS; geen crontabmutatie.

**SOURCE/CI VOLTOOID:** [PR #974](https://github.com/Blacksp1d3r/runner-mcp/pull/974), v0.1.160, exact-head `01b0c38016e566dea80dcc2358e277d4d7d00878`, validation `42982220300`, clean Ubuntu `42982220320`, attribution `42982220314` SUCCESS; MERGED `3d53e11fe5decfb955cda7052ebd27689d6efb01`. `autostart.py` kan één statische kandidaat-nevenunit berekenen zonder `Requires=runner-mcp.service` (dat anders een tweede server naast de cronserver kan starten), zonder `[Install]`/`WantedBy`. De normale volledige installer en systemd-unitgraph blijven intact.

**CUTOVER WAIT:** reguliere `autostart install/remove/reconcile` handelt nog de volledige managed set af, niet één rol. Een zelfs disabled unitbestand onder de vaste user-systemd-directory voldoet aan `has_managed_user_units()` en kan cron-reconcile blokkeren. Nieuwe kandidaatbytes **niet op originele live unitlocatie plaatsen**. Nog open: exclusieve één-rol write/start/old PID-exit/rollback, werkelijke functionele ontvangst/ACK, originele boot/linger en cronafhankelijke externe monitors. De zes originele cronrollen en automatische updates blijven **ONAANGEROERD**.

**HISTORIE HERGEBRUIKT (NIET HERHALEN):** oorspronkelijke fysieke `AF-HOST-0001` operatorcontrole 11 november: TCP8000, PID2202/startticks7503, zelfde generatie als 9 november, eigenaar/Python executable PASS; historische on-disk wheel v0.1.88 RECORD 131/131 PASS. In-memory geladen wheel/source/issuer is **NIET ATTESTED**. A7 bootpersistente echte zesrollenrollback/4-escrow en een echte updatecampagne-eigen ACK nog OPEN; de andere originele A6 disposable result+duurzame ACK is wel apart PASS. GitHub-bron 0.1.160 is niet live geïnstalleerd. #866 M3–M6 WAIT; onafhankelijke automatische updates mogen normaal voortlopen.

---

## 2026-11-10 — #669 originele wielcapturereceipt per inode: v0.1.158 SOURCE MERGED/CI PASS, LIVE WAIT

**DEFINITIEVE SOURCE-ACCEPTATIE:** [PR #969](https://github.com/Blacksp1d3r/runner-mcp/pull/969) exact PR-head `ad47733469184c470c91a390601e95a364eb708a`; officiële Runner MCP validation `42906852580` SUCCESS (Ruff, volledige pytest incl. adversariële swaptest, reserved version, echte isolated systemd, complete demo en candidate), Clean Ubuntu `42906852624` SUCCESS, attribution `42906852753` SUCCESS; squash MERGED `4de0625642542b2a743fed6faf448fc564e47e56` en huidige `main`+bronblob+versie 0.1.158 fysiek GitHub-readback PASS. PR-kandidaatartifact `13806575029` **UNAPPROVED / NO_INSTALL**. Deze wijziging geeft GEEN serving wheel-provenance en activeert GEEN automatische productieupdate.

- **Geschiedenis eerst:** officiële v0.1.88-wheel SHA256 `4cfafb747aab16f1a6b8285873f86910ea4ff836ee3da68921dcb5ac74b23567` is op 30 oktober reeds fysiek bewaard in bestaande `AF-SB-0002` op `AF-HOST-0001`; op 31 oktober werd de originele complete v0.1.88-runtime/crontab SHA256 `b8c2003f169c52a60d9f7c43c3ed27324e95d173b612b17956cdbfa02a31aefe` volledig niet-dienend hersteld (3.614 bestanden, 510 directories, 3 links, originele Python-import PASS). Geen oude back-up of wheel opnieuw aanmaken of scannen. Zie [A7 #1650 fysieke restore](https://github.com/Blacksp1d3r/Runner-Fabric/issues/1650#issuecomment-6547553981).
- **Nauw afgebakende bronoorzaak:** bestaande `artifact_receipt_capture.capture_candidate_wheel_receipt()` leest ZIP met `ZipFile(wheel)` en opent hetzelfde pad pas daarna opnieuw voor `_sha256(wheel)`. Bij vervanging tussen beide lezingen kan de individuele modulemanifest uit oude ZIP komen en de SHA uit een nieuwe ZIP met identieke Python-modules; het oude `offline_artifact_receipt_preflight` kan dat niet onderscheiden. Dit is een bronrisico, **geen gemeld werkelijk serverincident**.
- **Beperkte correctie in BESTAANDE helper:** open één `O_NOFOLLOW`-descriptor; pin eigenaar/inode/link/mode/size/mtime/ctime vóór ZIP, lees ZIP én SHA256 via dezelfde descriptor, controleer na beide lezingen de oorspronkelijke inode én het actuele pad. Een vervanging of wijziging sluit de receipt fail-closed; de bestaande create-once/0600/fsync/publication-uncertain en negatieve vorige tests blijven ongewijzigd. Nieuwe regressie vervangt ZIP na ledenlezing door een wheel met dezelfde Python-bytes maar andere WHEEL-metadata, verwacht STOP/no receipt.
- **Beperkingen:** uitsluitend GitHub-versie `0.1.158` SOURCE MERGED/CI PASS; dit **is geen geverifieerde actieve wheel**, signing/issuer, alle zes rolidentiteiten, formele 4/4 A7-escrow, automatische echte zesrollenrollback, A6 voorbereide same-campaign-event of nieuwe update-ACK. Geen originele `AF-HOST-0001`/Black/LAB-server- of dienstactie; de bestaande onafhankelijke A7-actor en overige backups blijven behouden. Geen tweede updater/journal/controller, geen Ed-productiesleutel.

---

## 2026-11-09 — F30 / #341 v0.1.157 veilige multijob-transactie SOURCE voltooid; fysieke updateketen niet

- **VOLTOOID SOURCE:** [Runner-MCP PR #967](https://github.com/Blacksp1d3r/runner-mcp/pull/967) merge `b024cb565954f652ccd23c47a9f3a422210c2526`, 0.1.157; afzonderlijk 4.734 pytest, Ruff, release-reservering, disposable systemd, volledige 5-minutendemo, Ubuntu-bootstrap en attribution PASS. Een oude cleanup mag met gedeelde lock en jobgebonden CLEAR geen transactie van een nieuwe update meer wissen. Bestaande `begin_transaction` no-replace blijft ongewijzigd; er is geen tweede updater, scheduler, controlplane of releasecircuit.
- **VOLTOOID STAGING, GEEN PRODUCTIE:** AIfordable hoofdbranch release `a77e6c...` werd door bestaande CI automatisch als immutable staging geïnstalleerd en met lokale :18120 A6 issuer-smoke getoetst: [workflow 42658567746](https://github.com/Blacksp1d3r/AIfordable/actions/runs/42658567746) SUCCESS. Oorspronkelijke SQL :8020/Nginx blijven actief en ongewijzigd. Fabric exact e1854806… release met 33 assets is publiek gepubliceerd, niet als actieve hostinstallatie bewezen.
- **IN VOLGORDE NOG OPEN:** Runner-MCP oorspronkelijke host/ingeladen wheel #669; A6 echte onafhankelijke Black off-target journal + doelverlies #942; A7 oorspronkelijke bevoegde eenheidscampagne met zelfstandige no-NIC rollback #943; échte originele-client resultaat→duurzame ACK binnen dezelfde updatecampagne; veilige activering plus onafhankelijk nieuw PID/poort/executable/revisie-readback. A6 guest bestaande Agent Bus READY, beide diensten/9020 actief en authenticated idle claim PASS — niet herhalen. Veiligheidsgrenzen en rollback gelden onverkort; geen automatische productiepromotie op basis van alleen CI/artifact/staging.

---

## Customer/on-prem update readiness counterpart

Tracking: #414. Orchestration/policy owner: Blacksp1d3r/Runner-Fabric#1063. Customer/product semantics: Blacksp1d3r/AIfordable#401.

Runner-MCP may later expose only bounded local primitives required by Fabric: read-only semantic disk/RAM/memory-pressure/swap/OOM/CPU/thermal/storage/power/network/restart/build/schema/recovery readiness; returning-node trust-generation state; exact release staging/activation/rollback only after separate authorization; and bounded failover/failback hooks only for fixed target adapters.

Runner-MCP does not choose customers, cohorts, rollout order, canaries, soak windows or failure cause. Missing/unsupported health remains explicit unknown. Insufficient RAM/storage or unsafe resource pressure blocks before mutation. No arbitrary path, shell, package manager, endpoint, service selector, raw hardware log or customer data is exposed.

## Fleet Update Track A — control-path protection

Canonical umbrella: Blacksp1d3r/Runner-Fabric#924. Reviewed design: Runner-Fabric `roadmap/FLEET_UPDATE_PLANE_BUILD_VS_BORROW.md` v2. Runner-MCP execution issue: #341. Fabric Track A: #937–#943.

Runner-MCP owns the concrete bounded execution and local safety pieces, not fleet orchestration. Near-term order:
1. reproduce the historical stale/incompatible peer failure in automated tests;
2. expose build identity and version-stamped logs;
3. propagate correlation context and support the synthetic end-to-end probe;
4. exchange/enforce protocol range plus interface/tool-schema compatibility;
5. implement CI evidence for N/N-1 first-party skew;
6. emit bounded journal evidence needed by Fabric;
7. reuse the existing staged baseline/self-update recovery machinery while adding support for a separate local commit-confirmed supervisor that can revert after activation without network/Fabric.

Important existing capability: install-time rollback already stages a baseline wheel and can restore it when installation/runtime verification fails. The missing mechanism is post-activation independent recovery: successful updates currently clear the install transaction/artifacts and restart is scheduled by Runner-MCP itself.

Economic constraint until AIfordable has revenue: **incremental software spend is EUR 0**. Use existing code and free/open-source dependencies only. No paid SaaS, commercial update manager, paid Fleet tier, Mender Enterprise or other paid runtime dependency. Hardware, connectivity and electricity are accepted owner costs; software cost remains time only until revenue supports a new explicit decision.

Status update — 2026-10-05:
- Step 1/A1 COMPLETE via #346 / `c37f60dc...`.
- Step 2/A2 ACTIVE. Initial component/version audit stamping #348 / `c73298e6...`; full aligned BuildIdentity fields on every existing audit row #355 / `98bd8ca0...`.
- A2 is not complete until installed provenance, protocol range/interface digest and cross-hop request reconstruction are proven.
- Next Runner-MCP contribution is to expose/propagate the provenance/protocol/interface facts needed by Fabric A2/A4 without broadening remote authority.

# Runner MCP roadmap

This public roadmap is intentionally infrastructure-neutral. Real deployment details belong only in private configuration.


Handoff policy: `roadmap/ROADMAP.md` is the canonical architectural roadmap; `roadmap/DEPENDENCIES.md` is the canonical cross-stream build/integration order when parallel work exists. GitHub live state wins if either document lags.

Status policy: this roadmap is the architectural source of truth for implemented and remaining phases. `handover/CURRENT_STATE.md` is chronological evidence of completed work, while GitHub CI and release records are authoritative for exact validation results such as test counts.

## Maintenance mode — alpha/MVP core complete

Runner MCP's technical alpha/MVP core is complete and the project is in maintenance mode.

Maintenance-mode rules:

- do not add speculative features merely to keep the roadmap moving;
- accept security fixes, correctness bugs, compatibility work and concrete operator needs;
- preserve the small deny-by-default transport/execution boundary rather than growing into a general remote-control platform;
- keep orchestration, scheduling, provider/API behavior, change planning, higher-level autonomy and fleet-scale control in Runner Fabric;
- deferred items in later phases are not launch blockers and should be revisited only when a real use case justifies them;
- discovery/marketing work is non-blocking and must not cause provider-specific runtime, package, auth or hosting changes.

The canonical public alpha release is v0.1.3. Live acceptance covers bounded first-party control, self-update/restart convergence and deliberate interrupted-install recovery. Remaining open issues are external/owner-controlled follow-up rather than core runtime blockers.

## Cross-cutting — end-to-end operational snapshot

Tracking: #269; cross-repo source of orchestration truth: Runner Fabric #867.

A concrete operator-correctness gap was observed on 2026-10-04: the local Runner MCP test queue could correctly report `0 queued / 0 claimed / 0 running` with all test workers available while the first-party client still reported that systems were busy. Therefore local test-queue idleness must never be presented as end-to-end idleness.

Runner MCP will expose one coarse, read-only, bounded `operational_snapshot` over the existing canonical control path:

`client -> control relay -> Agent Bus -> Runner MCP -> Runner Fabric -> worker/work-unit -> durable result -> acknowledgement`.

The snapshot must, where canonical evidence exists, distinguish queued, claimed/inflight, running, waiting-for-result, waiting-for-ack/replay and retrying work; expose oldest-pending and last-activity age; show bounded worker capacity/saturation and primary/fallback/degraded transport state; and return explicit `unknown` / `not_configured` instead of false green when a layer cannot be observed.

Runner MCP must not create a second queue, scheduler or orchestration state store. Runner Fabric remains the owner of orchestration truth; Runner MCP performs only bounded validation/projection. The tool exposes no payloads, prompts, file names, host paths, endpoints, credentials, raw logs, arbitrary queue browsing, shell, process or network authority.

Acceptance requires a synthetic and live-observable case where the local test queue is idle while upstream relay/Agent-Bus/Fabric work is pending to report the system as non-idle and attribute the correct layer; a truly idle path must converge to clear across all observable layers. One coarse snapshot call is preferred over many small status calls.

## Cross-cutting — AI fault containment with proportional security gates

Runner MCP assumes that an AI/client can misunderstand instructions, hallucinate, follow prompt
injection, call the wrong tool, or otherwise request an unsafe action. The model/client is never
the final authority.

The execution boundary must therefore preserve fast autonomous work where mistakes are contained
while applying stronger deterministic checks only as blast radius increases.

### Operating zones

- **Green / contained:** read-only inspection, safe file reads, predefined tests, bounded logs and
  other actions confined to declared project/runtime limits should remain automatic and must not
  require human approval merely because an AI requested them.
- **Controlled:** staging mutation, known managed service/release actions, migrations and equivalent
  bounded operations require deterministic policy, fresh-state validation, exact plan/target
  binding and replay/fencing protection. Human approval is required only where policy says so.
- **Protected:** production mutation, database restore/destructive recovery, credential/security
  policy changes, emergency-stop changes and equivalent high-blast-radius actions require
  independent operator authority and are not enabled merely by client or agent text.

### Security invariants

- AI/client text expresses intent only; deterministic Runner MCP code decides whether a predefined
  capability exists and is authorized.
- Forbidden capabilities must be absent, disabled or technically unreachable, not merely described
  to the model as "do not call this".
- Tools accept bounded semantic identifiers, not arbitrary shell, executable, host path, endpoint,
  environment, service/process or credential input.
- Mutations revalidate current state immediately before execution and remain bound to the exact
  approved plan/target/revision.
- Approval cannot be self-asserted by the requesting AI/client and must be independently derived.
- Repository/document/tool output is untrusted data and cannot grant capability, weaken policy or
  satisfy approval through prompt injection.
- The caller cannot modify the emergency-stop, approval, audit, authentication or policy boundary
  that governs the caller's own action.
- Executors receive the minimum OS/network/credential authority needed for the bounded operation.
- Mutations verify postconditions and preserve recovery/rollback semantics where applicable.
- **Security friction is proportional to blast radius:** safe read/edit/test loops should remain
  fast and automatic; expensive/human gates belong at trust boundaries, not on every development
  step.

This cross-cutting rule strengthens the existing deny-by-default design. It does not add any new
production, shell, credential or restore authority.

## Cross-cutting — optional Runner Fabric coarse work-unit transport

The transport foundation is implemented on `main` via PR #111. Runner MCP may expose exactly three
coarse Runner Fabric tools when private loopback configuration is present:
`fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`.

This integration preserves the product boundary:

- Runner MCP owns MCP authentication/transport, bounded request/response validation, rate limiting,
  existing operator/safety gates and bounded audit;
- Runner Fabric owns orchestration, work-unit policy/state, capability/fencing decisions, change
  plans, validation/repair, commit/push, provider/API-budget behavior, idempotency and recovery;
- the bridge is absent when unconfigured and may not introduce generic shell, Git, GitHub,
  filesystem, provider or arbitrary polling primitives;
- endpoint/token/provider/private-host details remain private and may not escape through tool
  output, audit detail or exceptions;
- transport sessions are isolated per calling thread and response identity/revision/state
  relationships fail closed.

Live activation and end-to-end proof are complete. Issue #110 is closed after a real first-party
client invocation traversed `client -> Runner MCP fabric_run_work_unit -> private Fabric MCP ->
trusted work-unit service`, followed by bounded get/cancel/operator-safety reconciliation. The
former upstream Runner Fabric durability/Agent-Bus qualification gate is also complete. The merged
transport layer must not be rebuilt.

Agent Bus remains the normal runtime-control path, direct GitHub choreography is fallback/bootstrap,
and broad remote-host tools are break-glass only. No plugin/client convenience may add generic shell,
Git/GitHub, filesystem, provider or credential authority.

## Phase 0 — repository and design

Establish repository structure, security baseline, threat model, configuration model, handover notes, dependency policy, and public-repository hygiene controls.

## Phase 1 — minimal MCP server

Implement Streamable HTTP, authentication, health endpoint, project registry, structured audit logging, request identification, basic rate limiting, `list_projects`, and `project_status`.

## Phase 2 — safe file access

Add allow-listed project file reads, metadata, pagination, path traversal protection, symlink escape protection, secret deny-lists, and file-size limits.

## Phase 2.5 — operator safety and rollback policy

Before enabling mutating tools:

- require an external operator emergency-stop mechanism;
- keep future operator actions read-only until retention policy is explicitly confirmed;
- retain code releases using both a minimum count and minimum age;
- retain pre-migration backups separately from code releases;
- treat database point-in-time recovery as a separate retention control;
- allow only one code rollback step per approved action;
- prohibit automatic production database restores;
- require explicit human approval before any database restore;
- require recovery/preflight metadata before migration, deploy, or rollback.

## Phase 3 — controlled test runner

Implemented design:

- predefined test profiles only;
- absolute executable paths and argument arrays with `shell=False`;
- project-relative working directories;
- bounded concurrency, timeout and log size;
- asynchronous jobs with status and paged logs;
- explicit cancellation;
- external operator-stop observation;
- process-group cleanup;
- scrubbed secrets and private paths in logs;
- persisted safe job metadata and interrupted-job recovery;
- restricted environment passthrough;
- short per-job private `TMPDIR` paths for local IPC/socket based test runtimes, with 0700 permissions and terminal cleanup;
- declarative `playwright` test runtime support that injects only a privately configured shared browser cache into the isolated job environment;
- no automatic execution of untrusted public-fork code without stronger sandboxing.

## Phase 3.5 — packaging and onboarding

Make the safe core usable without reading or editing source code:

- `runner-mcp setup` interactive private configuration;
- local/public setup modes with safe local defaults;
- explicit retention confirmation;
- `status`, `doctor` and emergency-stop commands;
- project add/list/remove commands;
- test-profile add/list/remove commands;
- pytest and Ruff profile presets;
- explicit token rotation only;
- non-root `install.sh`;
- user-first README and Quickstart;
- private config permission checks and atomic project-config updates.
- install/runtime preflight must verify the exact Python interpreter, venv support, pip usability/version, packaging backend availability, dependency compatibility and post-install import/bytecode integrity before enabling the installed command; known-bad or incompatible environments fail closed before service activation.
- clean-install validation must cover a minimal Ubuntu-like host where `python3-venv` may be absent and must exercise the real installed CLI after dependency resolution, including detection/recovery guidance for corrupted or incompatible `.pyc`/marshal state.

Service auto-start packaging is implemented with a preferred non-root systemd-user backend plus a managed cron fallback for headless accounts without a usable user bus. Both keep fixed components, explicit watcher bootstrap, duplicate-supervisor protection and foreign-state protection. Privacy-safe guided connectivity is implemented; external tunnel/TLS/reverse-proxy provisioning remains operator-managed. Task 33 reviewed optional graphical administration and keeps it deferred for the first alpha; any later first slice must be a separate loopback-only read-only dashboard over explicitly allow-listed safe summaries, with no new mutation authority.

## Phase 3.6 — community usability and extension path

Make the existing safe core easier to adopt, understand and extend without changing its trust boundaries:

- project-aware runner-mcp guide command with safe next-step suggestions;
- separate operator/service-account wrapper without secret duplication;
- dedicated user-to-developer extension guide;
- contribution rules that preserve deny-by-default behavior;
- configuration-first extension model;
- built-in adapter extension path before core changes;
- documentation must use placeholders and stay free of real infrastructure values;
- onboarding documents must stay synchronized with implemented features.

Still planned:

- optional graphical administration remains post-alpha/deferred after the Task 33 boundary review; revisit only on concrete operator need, starting read-only/local-only;
- framework adapters only when concrete reusable use cases justify them.

Privacy-safe private-tunnel/TLS/reverse-proxy guidance is implemented. Runner MCP deliberately does not provision external tunnel/TLS/DNS/firewall/proxy state itself.

## Phase 3.7 — GitHub mailbox bridge protocol

Formalize the proven GitHub to Runner MCP transport without turning it into a remote shell:

- public, infrastructure-neutral mailbox protocol documentation;
- strict versioned JSON request model;
- fixed allow-list for project inspection and predefined test execution;
- unknown fields, duplicate keys and oversized requests fail closed;
- no client-supplied shell, executable, path, environment, service or arbitrary MCP tool name;
- migration, deployment and rollback execution are available only through their existing approval IDs; restore remains outside the mailbox allow-list;
- watcher implementation stays private until deployment-specific parts are separated from reusable protocol logic.

Current status:

- the private watcher migration is complete through the shared runtime described in Phases 3.8.3–3.8.7;
- deployment-specific credentials and infrastructure details remain private.

## Phase 3.8 — bridge result envelope and replay protection

Harden the GitHub mailbox transport in both directions:

- strict, versioned result envelope;
- bounded result size, nesting, collection count and string length;
- fail-closed unknown fields and duplicate JSON keys;
- conservative redaction of credentials, environment metadata, paths, hosts, URLs, executables, commands and service-unit details;
- safe error codes instead of raw exception/process output;
- canonical SHA-256 request fingerprints;
- local replay ledger that stores no project/profile/path/credential/result content;
- duplicate request IDs never execute twice;
- request-ID reuse with changed content fails closed;
- corrupt, oversized, capacity-exhausted or symlinked replay ledgers fail closed;
- ledger file permissions restricted to the service account.

Current status:

- the shared validator, result envelope and replay lifecycle are integrated into the public watcher runtime and proven through the later 3.8.x phases.

## Phase 3.8.1 — task-completion feedback

Make asynchronous work observable to the operator without expanding execution authority.

Implemented public contract:

- strict terminal completion events: succeeded, failed or cancelled;
- deterministic event IDs derived from a private source identifier, giving transports a stable deduplication key without exposing the source identifier itself;
- fail-closed source/operation binding for test, migration, deployment and rollback job classes;
- test completion requires a predefined profile; unrelated job classes cannot attach one;
- project/profile/event identifiers use safe bounded shapes;
- attention state is derived from terminal status rather than trusted from a sender;
- duplicate JSON keys, unknown fields, non-standard JSON constants and oversized events fail closed;
- completion payloads contain no paths, hosts, URLs, credentials, service names, environment values or raw logs;
- notification delivery is explicitly separate from task execution: delivery retries may never rerun the operational action;
- mailbox permissions and action allow-lists are unchanged.

Implemented notification runtime and private proof:

- an optional private GitHub-issue notifier observes strict persisted terminal test, deployment/rollback and migration jobs without calling any execution path;
- notifier bootstrap deliberately skips historical completions;
- deterministic event IDs are used both in a private 0600 delivery ledger and as remote notification markers;
- existing remote markers are reconciled instead of posted again;
- notification failures remain retryable independently from task execution;
- one fresh predefined test job was proven end to end to produce exactly one user-facing notification, and a repeated notification cycle produced no duplicate;
- the built-in notifier no longer requires a repository-specific self-hosted Actions runner.

Next:

- keep heartbeat/stale-request recovery separate from notification delivery;
- map any future asynchronous Runner MCP job class to the same completion-delivery runtime only when its persisted terminal metadata can be consumed without widening execution authority.

## Phase 3.8.2 — watcher resilience and restart recovery

Make the private mailbox transport observable and restart-safe without widening the mailbox action allow-list.

Implemented public foundation:

- replay ledger lifecycle now distinguishes `claimed` from `completed`;
- legacy replay entries without a lifecycle state are treated conservatively as `claimed`;
- a request is marked completed only after its safe result is durable;
- restart recovery distinguishes processable, already-resulted, ambiguous-claim and missing-result states;
- ambiguous claimed work is never rerun automatically;
- a completed ledger entry with a missing transport result is never rerun automatically;
- sanitized heartbeat states are limited to `healthy`, `backlog` and `degraded`;
- heartbeat output exposes only bounded counts and oldest-pending age, never request contents or infrastructure metadata;
- stale/backlog thresholds are bounded;
- duplicate heartbeat observations fail closed;
- transient transport retry is bounded to timeout/rate-limit/unavailable failures;
- authorization and invalid-response failures are not automatically retried;
- transport retry policy never authorizes operational action replay;
- local operator recovery can resolve an already-claimed missing-result request by publishing a terminal safe `RECOVERY_REQUIRED` result without invoking the executor;
- the recovery command requires an existing exact replay record, refuses an existing durable result, preserves the cursor, and finalizes a claimed ledger entry only after the safe failure result is durable;
- a strictly valid request that has never been claimed can be explicitly abandoned by a local operator, producing an `OPERATOR_ABORTED` result without invoking the executor;
- a malformed historical request can be quarantined only when it is in the current backlog, has no result, every sibling request has a matching durable result, and the request head remains unchanged through final verification;
- malformed-request quarantine fetches only bounded bytes from the fixed mailbox path and does not weaken normal protocol parsing;
- no recovery path exposes a generic replay, ledger-reset or cursor-reset control;
- a normal watcher cycle performs subsequent reconciliation where applicable.

Operational proof covers migrated claim -> execute -> persist -> complete ordering, sanitized heartbeat publication, restart-safe reconciliation and one live malformed legacy-request quarantine with zero replay. Explicit operator recovery paths have regression coverage for persistence failure, protocol validity, exact confirmation and cursor/head races.

Next:

- keep notification delivery and heartbeat/stale recovery independent;
- extend operator recovery only when a new fail-closed state has a provable non-replay resolution; never add a generic replay/reset switch.

## Phase 3.8.3 — transport-neutral bridge processor

Move reusable watcher orchestration into the public package without publishing deployment-specific transport details.

Implemented foundation:

- strict request parsing happens before replay claim or execution;
- replay claim happens before any Runner MCP action;
- duplicate completed requests return without execution;
- duplicate claimed requests become an ambiguous recovery state and are not executed;
- executor interface contains only the six mailbox-allow-listed actions;
- no arbitrary MCP tool name, shell, executable, path, environment or service name is accepted by the processor;
- `run_tests` uses an explicit `run_tests_to_completion(project, suite)` executor method;
- executor exceptions become generic safe failure envelopes without raw exception text;
- unsupported/unsafe executor output becomes a bounded `UNSAFE_RESULT` failure;
- results are scrubbed/serialized before the transport-specific result sink sees them;
- durable result persistence happens before replay lifecycle completion;
- result-persistence failure leaves the request claimed and returns safe recovery material rather than rerunning the task;
- replay-finalization failure after durable persistence is reported as recovery-required rather than triggering execution again.

Still transport-specific/private:

- mailbox repository/branch selection;
- credentials;
- polling/webhook mechanics;
- result-file naming/location;
- notification destination;
- supervisor/service configuration.

Current status:

- the processor is integrated with the hardened GitHub transport and watcher coordinator in Phases 3.8.4–3.8.7; the private pilot migration and end-to-end proof are complete.

## Phase 3.8.4 — hardened GitHub mailbox transport

Provide a reusable GitHub transport without putting deployment-specific credentials or infrastructure details in the public repository.

Implemented foundation:

- fixed GitHub API host; callers cannot supply an arbitrary endpoint;
- repository and branch/ref identifiers are strictly validated;
- request, result and heartbeat locations are fixed below the mailbox root;
- GitHub credentials remain runtime-only and are never serialized into mailbox data;
- API responses are size-bounded;
- duplicate JSON keys and non-standard JSON constants from GitHub fail closed;
- wrapped GitHub base64 content is accepted only after strict validation;
- request payload identity must match its mailbox filename;
- result publication is create-once and idempotent only when existing content is identical;
- conflicting existing result content fails closed;
- result transport failures map into the BridgeProcessor persistence-recovery boundary;
- heartbeat create/update uses bounded validated public heartbeat JSON only;
- HTTP authorization, rate-limit, timeout, conflict and availability failures are classified without returning raw GitHub response content;
- no GitHub SDK or paid external service is required.

Current status:

- the generic coordinator and private-runtime integration are implemented in Phases 3.8.5–3.8.7;
- credentials, repository/ref selection and supervisor configuration remain private.

## Phase 3.8.5 — incremental watcher coordinator

Combine the public GitHub transport, bridge processor, replay lifecycle and heartbeat contract into a restart-safe watcher loop.

Implemented foundation:

- transient GitHub transport retries are bounded to 2 and 5 seconds after the original attempt;
- authorization and invalid-response failures are never automatically retried;
- request discovery uses a strict fast-forward compare from a private local cursor instead of rescanning historical mailbox contents;
- compare input is limited to validated 40-hex commit SHAs;
- request-file deletes, renames, nested paths, malformed IDs and oversized compare sets fail closed;
- first use is explicitly uninitialized and executes nothing;
- explicit bootstrap records the current request head and deliberately skips historical requests;
- local cursor uses restrictive permissions, file locking, symlink refusal and optimistic expected-SHA advancement;
- an existing durable result is reconciled into the replay ledger without executing the action;
- claimed requests without a result are never automatically rerun;
- completed requests with a missing result are never automatically rerun;
- persistence/finalization failures keep the cursor behind so the next cycle reconciles safely;
- malformed requests block cursor advancement instead of being silently skipped;
- heartbeat publication stays independent from operational task success;
- heartbeat delivery failure never rewinds an already-advanced cursor or reruns an action;
- non-request commits can advance the cursor without executing work.

Current status:

- the coordinator is combined with the loopback MCP executor and private runtime in Phases 3.8.6–3.8.7; restart/reconciliation proof is complete;
- completion delivery remains an independent idempotent subsystem.

## Phase 3.8.6 — loopback MCP bridge executor

Move the remaining pilot-specific MCP handshake and test polling into reusable public code without exposing a generic remote-control interface.

Implemented foundation:

- local MCP endpoint is restricted to HTTP(S) loopback hosts and the exact `/mcp` path;
- credentials in endpoint URLs, query strings and fragments are rejected;
- bearer token, session ID and test job ID shapes are bounded and validated;
- MCP response bytes are bounded;
- JSON and SSE payloads reject duplicate keys, non-standard constants, malformed UTF-8 and ambiguous multi-event responses;
- transport, JSON-RPC and tool failures become generic `BridgeExecutionAdapterError` values without raw server details;
- the public executor exposes exactly the six bridge operations;
- generic MCP tool dispatch stays private and internally allow-listed;
- internal `test_status` polling is used only to finish a previously allow-listed `run_tests` request;
- test logs are never fetched by the bridge executor;
- terminal test output is reduced to project, suite and status;
- polling interval and overall wait time are bounded.

Current status:

- private-config watcher migration and restart/reconciliation proof are complete in Phase 3.8.7;
- clean-environment demo validation and completion notification proof are also complete; remaining connectivity/onboarding work is tracked separately.

## Phase 3.8.7 — private-config watcher runtime and CLI

Wire the public GitHub transport, replay ledger, cursor, watcher and loopback MCP executor together without putting deployment-specific values into the repository.

Implemented foundation:

- GitHub repository, request ref, result ref and token live only in the private 0600 runtime environment;
- mailbox configuration is validated before atomic persistence;
- mailbox status reveals only configured/not-configured state;
- the GitHub token is entered through a hidden prompt and is not accepted as a CLI argument;
- mailbox removal deletes only the four mailbox environment values;
- setup overwrite preserves database and mailbox secrets even when rotating the Runner MCP bearer token;
- replay ledger and cursor files are derived inside the private configuration directory;
- `github-watcher bootstrap` explicitly starts at the current request head and skips historical requests;
- `github-watcher once` processes one bounded incremental cycle and prints only safe counts/state;
- `github-watcher run` provides continuous polling with bounded intervals;
- request polling and heartbeat publication have separate cadences;
- heartbeat defaults to a slower cadence and is also published on watcher-state transitions;
- heartbeat delivery remains independent from operational task execution.

Private deployment proof:

- the pilot poller has been replaced by the shared `runner-mcp github-watcher run` runtime in a private deployment;
- explicit bootstrap started at the current request head without historical replay;
- fresh protocol-v1 inspection requests, queue/worker observability and asynchronous test execution were proven end to end;
- restart/reconciliation preserved the cursor and replay ledger without duplicate execution;
- the legacy pilot poller is disabled in that deployment;
- completion-notification transport remains a separate capacity concern.

Current status:

- the independent exactly-once completion-notification proof and clean-environment demo validation are complete;
- remaining private-connectivity/TLS onboarding stays in the onboarding/launch phases.

## Phase 3.8.8 — controlled multi-project concurrency

Remove global serialization from routine bridge and test work without widening execution authority.

Implemented foundation:

- bounded mailbox request workers with a separate maximum in-flight batch;
- request acceptance separated from long-running test execution;
- persistent logical queues per project with fair round-robin scheduling;
- bounded global test-worker capacity and bounded global/per-project queue capacity;
- conservative defaults: two test workers globally and one active test per project;
- explicit per-project `max_parallel_tests` plus per-profile `parallel_safe` opt-in;
- queued, claimed and running lifecycle states before terminal test results;
- safe queue/worker/job observability and queued/running cancellation;
- malformed or recovery-required mailbox requests do not block independent work in the same batch, while cursor advancement remains fail-closed;
- GitHub result writes keep only a short serialized critical section;
- loopback MCP clients are thread-local so concurrent watcher workers do not share mutable MCP session state;
- existing shell, path, environment, service-name and arbitrary-tool injection boundaries remain unchanged;
- migration, deployment, rollback and restore remain outside the mailbox allow-list;
- authenticated MCP request capacity defaults to a bounded 600 requests/minute so status polling and mailbox concurrency do not become a new global bottleneck;
- request rate, test-worker capacity and queue capacity remain separate independently enforced controls.

Capacity can later grow by increasing bounded worker settings or adding execution capacity behind the same request/job protocol. Protocol clients do not need to change.

See `docs/CONCURRENCY.md` for defaults, scheduling, observability and Runner MCP versus GitHub Actions guidance.

## Phase 3.8.9 — bounded operational bridge

Extend the GitHub mailbox from inspection/tests into existing Runner MCP operational capabilities without introducing a generic remote shell or bypassing local safety controls.

Implemented foundation:

- bounded scrubbed test-log pages through `job_log`;
- configured service alias listing/status/start/stop/restart, never arbitrary systemd unit names;
- backup listing and on-demand configured PostgreSQL backups;
- read-only migration status, deployment plans, release lists and rollback plans;
- approval-plan request/status through opaque IDs;
- migration/deployment/rollback execution only with an already-approved short-lived approval ID;
- deployment and rollback job status through validated opaque job IDs;
- per-action strict argument schemas, bounded list/log ranges and fixed loopback MCP tool mapping;
- database restore, PITR, production actions, shell/argv/path/env injection and approval granting remain outside the mailbox authority.

This phase is specifically intended to remove routine dependence on general-purpose remote-control software. GitHub remains a transport; Runner MCP remains the local authorization and execution boundary.

Next:

- prove the expanded operational bridge live against one read-only operation and one low-risk configured mutation on the upgraded private runtime;
- preserve separate human approval for migration/deploy/rollback.

Runner MCP read-only observability and commit-pinned self-operations are implemented separately in Phases 3.8.10–3.8.11 rather than exposing package-manager or process-control primitives.

## Phase 3.8.9a — shared Playwright test runtime

Make browser-based E2E profiles work inside Runner MCP's isolated test environment without weakening HOME/TMPDIR isolation.

Implemented foundation:

- test profiles can declare a fixed runtime of `default` or `playwright`;
- the Playwright runtime receives only `PLAYWRIGHT_BROWSERS_PATH`, sourced from private Runner MCP configuration;
- the configured browser-cache path must be absolute, exist as a directory and not itself be a symlink;
- the browser-cache path is treated as a private path for log scrubbing;
- missing browser runtime fails closed before test execution;
- no arbitrary browser path can be supplied through the mailbox or test request.

This is intended for shared Chromium/Playwright installations on persistent self-hosted runners while preserving per-job HOME/TMPDIR isolation.

## Phase 3.8.10 — runtime observability bridge

Expose Runner MCP's own health/configuration state through fixed, read-only bridge actions so routine diagnosis no longer needs general-purpose remote access.

Implemented foundation:

- `runtime_status` returns package version, safety mode, emergency-stop state, bounded worker/queue capacities and whether test/database/deployment/approval subsystems are configured;
- `runtime_doctor` returns only bounded PASS/WARN/FAIL-style checks and generic details;
- no private paths, URLs, hostnames, credentials, service units, environment values or raw process output are returned;
- both actions are fixed no-argument protocol-v1 actions and map only to local MCP tools;
- result publication still uses the existing bridge scrubber, replay ledger and create-once result lifecycle.

Next:

- prove the runtime observability actions live after the private runtime is upgraded.

Mutating self-operations remain separate from read-only diagnosis and are implemented as commit-pinned operations in Phase 3.8.11.

## Phase 3.8.11 — commit-pinned Runner MCP self-update

Remove routine dependence on general-purpose remote-control software without introducing generic package or process control.

Implemented foundation:

- `self_update(commit)` accepts only one full lowercase 40-character commit ID for the configured canonical Runner MCP repository;
- the target commit must be reachable from `origin/main`, and source synchronization remains clean-worktree, exact-commit and staging/test gated;
- existing fixed `lint` and `unit` profiles must both pass before installation;
- validated update source is staged as a private wheel before installation; wheel building and installation use the active Python runtime with fixed offline/no-dependency pip arguments, no shell and no caller-supplied path/argv/environment;
- when a previously installed commit is known, its clean source is staged as a private recovery wheel before source synchronization, while the per-project source guard remains held across recovery staging, target sync, lint/unit validation, target staging and installation;
- a private 0600 install-transaction marker is durable before the in-place package mutation; runtime status exposes only a bounded `install_recovery_pending` boolean and overlapping self-updates fail closed while it exists;
- target package installation is verified in a fresh Python process before it is accepted;
- a caught target install/import failure automatically reinstalls and verifies the recovery wheel and restores the exact prior source commit when both package and source rollback can be proven; successful automatic recovery is reported as `install_rolled_back` without scheduling activation;
- a first/bootstrap install failure, process interruption during package mutation, failed rollback, or unfinalized transaction remains `install_recovery_required` and blocks further self-update instead of pretending the environment is intact;
- a persisted rollback-capable install transaction can be recovered only through the local `runner-mcp self-update-recovery` operator command; it requires the emergency stop to be active, reuses only the privately staged baseline wheel, restores the exact baseline commit from `origin/main`, re-verifies the installed runtime and clears the transaction only after package/source/state recovery is proven;
- the local recovery path refuses first/bootstrap transactions without a known baseline and refuses to overlap pending activation recovery; no recovery action is exposed through the mailbox or MCP tool surface;
- local `status` exposes only `clear`, `REQUIRED` or `INVALID` install-recovery state, while `doctor` warns on a valid pending transaction and fails on corrupt/unsafe transaction state without exposing commits or artifact paths;
- same-commit requests still verify the exact commit against `origin/main`, but then complete without package mutation or restart;
- the build backend required by the deliberate `--no-build-isolation` wheel path is an explicit runtime dependency rather than an implicit build-environment assumption;
- update jobs and installed-commit state are persisted privately with restrictive permissions;
- server, GitHub watcher and completion watcher activate new code through fixed component-specific self-reexec flows;
- activation creates fixed create-once restart markers for all three components; a failed component re-exec restores its marker instead of silently consuming the restart request;
- runtime status exposes only whether activation remains pending and the bounded number of fixed pending components; another self-update is blocked until those markers are cleared;
- server activation uses bounded retries, while watcher/notifier failures preserve their marker so existing systemd/cron supervision can safely retry on restart;
- `self_update_status(job_id)` exposes only bounded persisted state;
- read-only `runtime_status` keeps the broader observability fields and adds self-update readiness/state; `runtime_doctor` remains separate;
- the loopback bridge explicitly allow-lists `runtime_status`, `runtime_doctor`, `self_update` and `self_update_status`;
- protocol validation treats `self_update_status` as an exact job-id-only action, and direct/self-update entry points reject uppercase or abbreviated commit identifiers;
- arbitrary repository/ref selection, package-manager arguments, install paths, process commands, service identifiers and restart commands remain unavailable.

Next live-proof lane (tracked by #108):

- bootstrap the current recovery-capable baseline once on the private Runner MCP host through the normal dependency-resolving path;
- prove same-commit/no-op and one forward commit-pinned self-update through the bounded operating model;
- deliberately fail/retry one activation and fault-inject one package-install interruption only after the recovery-capable baseline is confirmed, proving that durable recovery state blocks overlap and can be cleared only by the existing bounded/local recovery path;
- keep dependency-set changes explicit because self-update intentionally never resolves or installs dependencies; a dependency-set change still requires an explicit compatible bootstrap path;
- do not describe in-place pip mutation as atomic: the transaction marker makes interruption detectable and fail-closed, while automatic rollback is claimed only for caught failures where both package and source restoration are verified;
- publish only scrubbed categorical evidence and public commit/workflow references; no private host identity, paths, services or credentials.

## Phase 3.9 — public launch readiness

Prepare Runner MCP for free, responsible discovery without changing its security boundaries.

Implemented launch-readiness foundation:

- Runner MCP remains the product identity under the AIfordable umbrella;
- README leads with the problem, safety boundary and architecture;
- Quickstart remains the full guided path while a separate five-minute local demo provides a shorter evaluation path;
- root security-reporting policy added;
- public changelog and release checklist added;
- reusable factual launch copy prepared for GitHub and developer communities;
- privacy-safe GitHub bug/feature forms and a security-focused pull-request template added;
- package metadata improved for future distribution;
- discovery metrics remain platform-level; no application marketing telemetry is added;
- no paid advertising, paid hosted CI or paid hosted infrastructure is a hidden dependency; standard free CI for this public repository is acceptable when it carries no private secrets.
- clean Ubuntu 24.04 / Python 3.12 CI now exercises the documented five-minute demo end to end, including installation, setup, doctor, predefined test-profile configuration, emergency stop and loopback health check;

Canonical publication completed:

- PyPI package `aifordable-runner-mcp==0.1.3` is published;
- official MCP Registry identity `io.github.Blacksp1d3r/runner-mcp` version `0.1.3` is published;
- GitHub pre-release `v0.1.3` is aligned with exact release commit `0aa013c279128e22fbd53be32c35bced3ae26834` and carries wheel + sdist assets;
- protected publish workflow run `36962568072` completed PyPI, official Registry and GitHub pre-release publication successfully;
- public GitHub description/topics and first-party canonical discovery links are live;
- mcp.so community submission is complete;
- secondary directories must reuse the canonical identity/install/auth metadata rather than inventing alternatives.

Remaining discovery work is intentionally non-blocking:

- Glama listing discovery, maintainer claim and metadata verification are complete; Glama hosting/release/Gateway remain intentionally unused;
- Smithery is deliberately skipped unless it exposes a repository-only path that preserves the canonical self-hosted architecture unchanged;
- AllMCPs listing ownership is verified through the free README path; no paid boost/featured placement is justified;
- stale third-party directory metadata is tracked separately in #263 and must not trigger package/runtime changes;
- one technical launch post remains deliberately deferred until `aifordable.com` is ready enough to serve as the public umbrella/landing page.

## Phase 4 — staging service management

Implemented core design:

- private service aliases mapped to systemd-user units;
- no arbitrary unit names supplied by MCP clients;
- safe alias listing without unit/health-URL disclosure;
- status and optional HTTP health checks;
- independent opt-in for start, stop and restart;
- all mutating actions pass the operator safety guard;
- emergency stop leaves status available but blocks service mutations;
- subprocess execution uses a fixed systemctl argument array with `shell=False`;
- no sudo or generic system-service control.

Task 41 provides the shared bounded text-redaction primitive. Task 47 is now integrated as a local/private `service-log` reader with explicit per-service `allow_log_read` opt-in, fixed bounded `journalctl` tailing and no MCP/mailbox/Agent-Bus log action. Any remote disclosure remains separately deferred to Task 51 review.

## Phase 5 — backups and migrations

Implemented core design:

- PostgreSQL-only database configuration with private `RUNNER_MCP_DB_*` credentials;
- DSN entered through hidden CLI prompt and kept out of project YAML;
- private backup root/project directories and 0600 dump/metadata files;
- `pg_dump` custom-format backups with DSN in child environment, never argv;
- safe backup metadata listing without dump paths or contents;
- predefined migration status/apply profiles with `shell=False`;
- bounded and scrubbed migration output;
- pre-migration backup required before migration apply;
- safety guard rechecked after backup and before migration;
- failed migration keeps the recovery point and never auto-restores;
- Task 44 adds the strict private durable migration-job substrate and `MIGRATION_JOB` completion source; Task 49 is now integrated as an additive `start_migration_job` / `migration_job_status` contract with distinct `migration_async` human approval while preserving synchronous `apply_migrations` and deployment-triggered migrations;
- local read-only restore preflight validates one private PostgreSQL archive without database connection or restore authority;
- local CLI retention preview strictly validates private release/backup state and reports protected or potentially eligible records without deleting or rewriting data;
- CLI database and migration configuration without manual YAML editing.

Not implemented yet:

- database restore execution remains deferred after Task 37: the current architecture does not prove a separately prepared empty recovery target, complete database-writer quiescence, application cutover, `pre_restore` retention semantics or semantic post-restore verification;
- WAL archiving/PITR orchestration and verification;
- automatic/unattended retention pruning;
- backup pruning remains deferred pending a separate crash-safe pair-deletion contract;
- local one-release pruning is implemented by Task 43 after Task 48 added the shared cross-process release lock: local CLI only, one freshly eligible non-migration orphan per short-lived plan, typed confirmation, durable quarantine transaction and fd-safe deletion; backups and automatic pruning remain deferred.

## Phase 6 — staging release engine

Implemented core design:

- staging-only deployment configuration;
- clean Git HEAD as the only deploy source;
- no client-supplied branch/ref/commit or arbitrary build shell;
- fixed Git argv with hooks/fsmonitor disabled;
- safe Git archive extraction with repository symlinks rejected;
- private release root, releases directory and runtime HOME;
- required test profiles before release creation;
- source HEAD/cleanliness rechecked after tests and before migrations;
- optional Phase 5 migration orchestration;
- atomic `current` symlink activation;
- configured service restart plus mandatory health check;
- one automatic code rollback after failed activation only when no migration was applied;
- no automatic rollback after database migration;
- persisted asynchronous deployment jobs and restart-interruption handling;
- MCP `plan_deploy`, `deploy_staging`, and `deployment_status`;
- CLI deployment configuration without manual YAML editing.

Still deferred:

- production deployment;
- framework-specific build/adapters;
- release pruning;
- manual historical rollback selection (Phase 7).

## Phase 7 — rollback engine

Implemented core design:

- safe release metadata listing with current/previous/commit/timestamp state;
- retention-protection reporting using both minimum count and minimum age;
- local advisory retention preview protects current/direct rollback/reference/migration-recovery relationships and never treats manual backups as automatically eligible;
- fail-closed release metadata validation and permission checks;
- direct previous release is the only rollback target;
- global strict MCP input validation rejects unknown arguments;
- rollback blocked when current release crossed a database migration boundary;
- asynchronous persisted rollback jobs;
- deploy and rollback jobs mutually exclude each other per project;
- atomic one-step release switch plus service restart and health verification;
- failed rollback health reactivates the original current release when safe;
- no database restore and no automatic multi-step cascade.

Still deferred:

- automatic release pruning remains deferred; Task 43 implements only one local/manual non-migration orphan release outside the retained rollback chain per confirmed plan;
- arbitrary historical target selection remains deferred after the Task 35 boundary review; older history is reached only through fresh direct-previous one-step approvals with health revalidation;
- production rollback;
- database restore/recovery workflow.

## Phase 8 — multi-project adapters

Implemented core design after Tasks 38–39:

- built-in `generic` and `python` adapters are deny-by-default and expose only bounded capability metadata;
- execution layers are project-generic after configuration is resolved;
- no dynamic adapter/plugin loading from project configuration is allowed;
- built-in non-custom test/migration presets are materialized through typed fixed adapter recipes rather than framework-specific branches in generic configuration code;
- Python-specific project-local executable discovery and fixed pytest/Ruff/Alembic argv construction live behind the Python adapter boundary;
- `custom` remains the explicit local-operator path with existing executable validation and no shell command string;
- unknown or ambiguous built-in presets fail closed.

New projects should normally require configuration/adapters rather than core changes. Additional framework adapters remain separate reviewed additions rather than dynamic plugins.

## Phase 9 — approval and risk gates

Implemented:

- short-lived persisted approval plans for migration, deploy and rollback;
- approval request/status available through MCP, but approval itself only through local CLI;
- explicit local confirmation phrase;
- approval bound to action, project and cryptographic plan fingerprint;
- single-use consumption and replay prevention;
- default ten-minute TTL with strict 60–1800 second bounds;
- deployment approval pinned to clean Git commit;
- migration approval requires and binds a clean Git HEAD;
- rollback approval pinned to current and direct previous release;
- runtime race checks reject changed deploy/rollback targets;
- mutating project actions restricted to `staging`;
- production remains read-only.

Connectivity decision:

- prefer OpenAI Secure MCP Tunnel for private ChatGPT/OpenAI connectivity where supported;
- keep Runner MCP private/loopback and use outbound HTTPS rather than opening inbound firewall ports;
- a hosted multi-user relay comparable to commercial remote MCP services is optional future infrastructure, not part of the MVP.

## Phase 10 — optional restricted command templates

Only if concrete use cases remain unmet, add tightly allow-listed executable templates under a sandboxed account. No free-form root shell.

## MVP completion

The MVP is complete when one pilot project can be inspected, tested, backed up, migrated, deployed to staging, health-checked, and rolled back without a general remote-shell dependency, while all actions remain auditable and secrets stay inaccessible.


## Cross-project Infrastructure Authority invariant

Runner-MCP consumes the canonical AIfordable Infrastructure + Credential Authority and does not own a separate fleet/server truth. Bounded operations must resolve scoped customer/site/host/runtime/service identity/credential binding and freshness before infrastructure mutation. Stable asset IDs are technical identity; env-var names and Linux usernames are implementation bindings, not host identity. Unknown, stale or conflicting context fails closed.

Authority: `Blacksp1d3r/AIfordable/docs/INFRASTRUCTURE_AUTHORITY.md`.
