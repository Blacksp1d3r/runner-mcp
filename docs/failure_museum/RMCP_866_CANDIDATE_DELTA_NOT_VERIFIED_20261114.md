# Runner-MCP #866 — In-memory cron-kandidaat leek consistent zonder exact éénrolsverschil

- Datum: 2026-11-14
- Scope: bestaande systemd-migratie #866; `src/runner_mcp/autostart.py` en cron-source preview
- Ontdekt bij: broncode-inspectie van gemergde bronversie 0.1.173; **geen productiefout waargenomen**
- Correctie: [PR #1000](https://github.com/Blacksp1d3r/runner-mcp/pull/1000), source 0.1.174; mergecommit `2686f2ebc6f0d8e999b410cf35a04a1da6b46df6`

## Wat kon fout gaan

De nieuwe `assess_single_peer_migration_checkpoint` vergeleek de kandidaat-cronbytes met de door de aanroeper gerapporteerde cronbytes en controleerde originele rollback-SHA, proces-/unit-/lock-/ACK-toestand. Zij **herberekende het feitelijke verschil tussen oorspronkelijke crontab en kandidaat niet**. Een onbetrouwbaar of per ongeluk verkeerd samengesteld in-memory `SinglePeerSystemdMigrationPreview` kon de verkeerde cronregel verwijderen of een vreemde cronregel herschrijven en tegelijk zijn eigen onjuiste waarneming daarop laten aansluiten. De functie zou dan ten onrechte `consistent=True` melden, maar gaf zelfs toen **nooit** `next_action_authorized=True`. Er is geen bewijs dat een fysieke host zo'n foutief plan heeft uitgevoerd.

## Oorzaak en begrensd herstel

Alleen interne consistentie is niet voldoende voor een migratievoorstel; de goedkeuringsvoorwaarde moet de **specifieke, byte-exacte éénrolswijziging** onafhankelijk toetsen. De pure helper `_exact_single_role_cron_delta` eist daarom één herkenbare managed bronrol binnen het oorspronkelijke begrensde cronblok, exact één verwijderde regel, onveranderde overige bytes en identieke executable/config-dir in cron en source-gerenderde `ExecStart`. De bestaande controle roept deze helper fail-closed aan vóór een fase PASS kan krijgen. Testgevallen verwijderen bewust een verkeerde rol, wijzigen de vreemde regel of voegen cronregels toe. Alle moeten STOP melden.

## Bewijs, beperkingen en herhalingspreventie

De officiële exact-head CI van PR #1000: [validation 43586169404](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169404), [Clean Ubuntu 43586169460](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169460) en [attribution 43586169471](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/43586169471) terminal SUCCESS; Ruff, 4.812 pytest, release-artifact en vijfminutendemo PASS. Op echte **disposable** Linux combineert de nieuwe CI echte bron-gerenderde zesrollen-cron, één bron-unit, alle zes fasechecks en byte-exact volledig cronherstel: `M2_DISPOSABLE_SOURCE_RENDERED_SIX_ROLE_PHASE_CHECKPOINT_ROUNDTRIP=PASS`. Eerdere acht M2-markers PASS.

**No-repeat regel:** controleer niet alleen de waarneming versus een intern voorstel, maar ook het voorstel versus de onafhankelijke, pinned oorspronkelijke bron/rol en volledige vreemde cronregels. Een PASS in deze **niet-activerende** controle is geen bewijs van originele hostidentiteit, real imported wheel, procesgeneratie, Fabric-ACK, A7-offline-rollback of een geslaagde productiemigratie. Het originele `github-runner` cron/systemd/A7/Agent Bus/updatepad werd niet gewijzigd.

## Aanvulling 2026-11-14 — onbruikbare uitvoerder tijdens herstel mag bronvalidatie niet afzwakken

Tijdens draft [PR #1003](https://github.com/Blacksp1d3r/runner-mcp/pull/1003) faalde de eerste **alleen GitHub-hosted disposable** negatieve proef doordat het testharnas na `chmod 000` van de eigen nep-executable opnieuw `plan_single_peer_systemd_migration` aanriep. De bestaande veilige `_validate_executable` weigerde terecht: `AutostartError: Runner MCP executable is unavailable`. Geen productie-incident, geen A7-actie.

**Correctie/no-repeat:** leg volledige originele crontab, byte-exacte kandidaat, bron-gerenderde unit en SHA256 vast **vóór** foutinjectie. Na de fout mag het herstelharnas nooit de kapotte uitvoerder opnieuw als bruikbare bron interpreteren; herleid het read-only fasestadium uit de vooraf vastgelegde testbron en verifieer actuele cron, unit, PID, flock en ACK apart. Een aparte, slechts in de bestaande disposable GitHub Actions-runner toegelaten `recover_failed_peer`-testroute voert exact éénrollen-disable, unitverwijdering en cronherstel met fase-readback uit. Een nog gezonde worker en zelfs een aangepaste vreemde cronregel leiden vóór wijziging tot STOP. Exact source commit `4d10d538a92a8327b4f9b1409e822e258487f4cf`, marker `M3_DISPOSABLE_BOUNDED_EXECUTOR_FOREIGN_CRON_DRIFT_DENIED=PASS`. **Geen** productie-uitvoerder of nieuwe bevoegdheid en originele automatische updates bleven buiten scope.

## Aanvulling 2026-11-14 — onderbreking na disable en vervalste cronblokregels

Bij de voorbereiding van een éénrolsherstel was de toestand 'unit bestaat,
maar is na succesvolle disable niet meer enabled en nog niet verwijderd'
niet als afzonderlijk herstelcheckpoint vastgelegd. Een herstartte executor
zou daardoor mogelijk een anders geobserveerde fase aantreffen en veilig
STOP moeten geven, maar niet kunnen aantonen wat de volgende stap is.

**Fix op draft PR #1003:** `peer_disabled_idle` is nu een expliciete alleen-lezen
fase, met ongewijzigde bron-/cron-/unit-/PID-/lock-/ACK-controles. De test-only
GitHub-hosted actor onderbreekt de werkelijke proef na `disable --now`,
start een nieuw proces en kwalificeert exact de resterende bronstatus vóór
unitverwijdering en byte-identiek cronherstel. CI-markers van de eerdere
integraaltest: `M3_DISPOSABLE_INTERRUPTED_AFTER_DISABLE_CHECKPOINT=PASS` en
`M3_DISPOSABLE_INTERRUPTED_DISABLE_RESUME_AND_EXACT_CRON_ROLLBACK=PASS`.
Een extra negatieve CI-proef weigert gewijzigde vreemde cronregels na
onderbreking, zonder een tweede supervisor of gevaarlijke systeemwijziging.

Een onafhankelijke broncontrole vond eveneens dat de eerdere
mixed-backend-parser regels zonder `* * * * *`-prefix binnen het managed
cronblok oversloeg. Een verzonnen `PATH`-/`SHELL`-regel kon zo binnen een
intern gelijklopende bron/candidate-snapshot verborgen blijven. Dat is
een **broncontractfout**, geen waargenomen exploit of wijziging op de
oorspronkelijke server. De parser vereist daarom exact de door de renderer
toegekende `MAILTO=""`-regel gevolgd door herkenbare per-rol-jobregels.
Regressies met extra PATH/SHELL, andere cronuitvoering en commentaar
moeten voortaan STOP opleveren; deze negatieve tests zijn op de draft
toegevoegd. Laatste head-CI apart verifiëren voordat het bewijs 'voltooid'
mag worden genoemd.

**No-repeat:** nooit herstellen vanaf de veronderstelling dat 'disabled'
hetzelfde betekent als 'absent'; observeer beide fasen afzonderlijk en
herkwalificeer de terugweg. Valideer het héle beheerde cronblok, niet alleen
de geselecteerde regel en interne gelijkheid van twee aangeleverde snapshots.
Ook deze uitbreiding autoriseert geen A7/prod-migratie.

## Aanvulling 2026-11-14 — tijdelijke symlink in testharnas: is-enabled-check te vroeg

In de extra negatieve disposable test werd het **eigen** uitgeschakelde
systemd-unitbestand tijdelijk vervangen door een symbolische link.
De eerste scriptvariant controleerde `systemctl --user is-enabled` juist
terwijl het unitpad opzettelijk was verwisseld. Dat is geen stabiele meting
van het oorspronkelijke unitbestand; de CI stopte na
`M3_DISPOSABLE_INTERRUPTED_AFTER_DISABLE_CHECKPOINT=PASS`, zonder
duidelijke volgende fase. Geen productieactie; de EXIT-trap ruimde
testassets op.

De verwachte veiligheidsbeslissing blijft ongewijzigd: de herstelactuator
moet de onbetrouwbare symlink afwijzen nog vóór unit-unlink of cronwrite.
De correctie brengt de bronstatus- en `is-enabled=disabled`-controle
uitsluitend **ná terugplaatsing van de eerder gepinde test-inode**, niet
tijdens de bewust vervalste unitpadfase. Nieuwe exacte-head [PR-checkruns](https://github.com/Blacksp1d3r/runner-mcp/pull/1003/checks)
is niet nodig als bron van waarheid; gebruik de PR-checkruns van de
daadwerkelijke commit. Op code-head
`cdd5df7427b8f49ba42a10fcb9b8a8d73d694bbb`:
`M3_DISPOSABLE_DISABLED_PEER_SYMLINK_DRIFT_DENIED=PASS`,
`M3_DISPOSABLE_RESUME_WITH_FOREIGN_CRON_DRIFT_DENIED=PASS`,
Ruff en 4.851 pytest PASS.

**No-repeat:** bij bewuste sabotage van een unitpad nooit de managerstatus
van die gesaboteerde naam behandelen als betrouwbaar bewijs van de
oorspronkelijke unit. Verifieer eerst dat de bronidentiteit terug is,
meet daarna opnieuw; de test-only actor blijft fail-closed. Geen
aantoonbare originele-hostfout, geen automatische A7- of productiemigratie.

## 2026-11-15 — false-negative negatieve cronbronproef door gequote tijdsvelden

Bij aanvulling van de zuivere M3 `assess_single_peer_mixed_backend_status` met
canonieke validatie van **alle** behouden cronrollen (niet alleen de
uitgesloten peer) genereerde de eerste nieuwe testfixture de vijf
letterlijke `*`-veldnamen via `shlex.quote`. Die functie voegde
onbedoeld quotes aan de cron-tijdvelden toe. De al bestaande
managed-block-validator wees vervolgens terecht die niet-canonieke
tijdvelden af met `original_managed_block_unqualified`, **vóór** het
beoogde nieuwe controlepunt `original_cron_role_unqualified`. Vijf
parametrische regressies op de eerste code-HEAD `a1d7804d4ec4a1a023f6c2a3bfea7939c75f0981`
faalden daarom uitsluitend op de verwachte foutcode. De overige
**4.851** tests slaagden. Dit was geen productie-/hostincident en
bewijst geen veiligheidsprobleem in de nieuwe parser.

**Correctie:** het testschema vormt nu de vijf cron-tijdsvelden letterlijk
als `* * * * * ` en shell-escapet uitsluitend de argv-argumenten ná
die velden. De bestaande rolbroncontrole, productierenderer,
installer en A7-code blijven onaangeroerd. De nieuwe exacte code-HEAD
`79e0c578548273310982e1c65758c4212e1ec6f0` bereikte in
officiële Ruff+pytest **4.856 PASS** en de echte disposable Linux
systemd-proef **SUCCESS**. Overige workflows kunnen pas als PASS
worden gemeld wanneer hun eigen jobs terminal zijn.

**No-repeat:** een negatieve bronproef moet de overige geldige
syntax **byte-identiek** behouden, anders test ze een oudere/andere
fail-close-gate. Verifieer bij elke negatieve CI-test zowel de
verwachte STOP als de specifieke foutcode en actualiseer de testcase
niet door de doelvalidatie kunstmatig te versoepelen. Dit werk verandert
geen live cron, geen unit, geen A7-bevoegdheden en geen release-reservering.

## 2026-11-15 — tweede éénrolsherstelonderbreking na unit-unlink, voor crontab

De bestaande bronstatus `rollback_ready` was al leesbaar/planbaar,
maar op de wegwerp-Linux-host werd nog niet getest of een **nieuw proces**
het herstel na het verwijderen van de unit kon hervatten zonder een
eerder gemuteerde vreemde cronregel te overschrijven.

Nieuwe afgebakende CI-proef in het **bestaande** script: pauzeer na
eigen unit-unlink en `daemon-reload` met vijfrollen-cron intact.
Verifieer de oude read-only `rollback_ready`-planner, laat een
testmatige vreemde cronregel ná die planner wijzigen, eis STOP vóór
de oude `crontab -`, en controleer dat de vreemde regel behouden
blijft. Herstel daarna uitsluitend de fixture-kandidaat en herneem
met een **derde** onafhankelijke procesaanroep tot exact origineel
zesrollen-cronherstel en `rollback_confirmed`.

Deze test laat nadrukkelijk de fysieke race tussen de allerlaatste
`crontab -l` en een erop volgende `crontab -` open: Linux crontab
biedt geen bewezen gedeelde CAS met onbekende andere schrijvers.
De test bewijst **niet** dat parallelle cronacties atomair kunnen
worden teruggedraaid. M3/live en A7 blijven onbevoegd/ongewijzigd.
Registreer werkelijke PASS-markers pas na officiële CI-terminatie.

## 2026-11-17 — #866 brede CLI-remove kon beide gemengde beheerders wissen (SOURCE-FIX)

Bij read-only review van de bestaande `cmd_autostart` op draft #1003
werd een **nieuwe, afzonderlijke bronafwijking** vastgesteld:
`autostart status` en `reconcile` wezen gemengd cron/systemd al af,
maar `autostart remove` vroeg eerst één brede bevestiging en voerde
daarna onafhankelijk `remove_cron_services()` EN
`remove_user_services()` uit. Een gemengde éénrols-M3-toestand kon
zo het nog benodigde cron-schema én de systemd-peer verwijderen, ondanks
het bestaande strikt rolgebonden herstelvoorstel.

**Causale, beperkte correctie:** `cmd_autostart` weigert nu het
algemene `remove` direct bij beide managed supervisorclaims, dus
**vóór** de operatorbevestiging en vóór beide mutatoren. Er is
geen nieuwe productie-uitvoerder, geen wijziging van de daadwerkelijke
rolgebonden rollback of de bron-/ACK-/lockgates. Bestaande normale
één-backendverwijdering blijft behouden.

**Regressie:** negatieve CLI-test stelt een verboden prompt en beide
mutatoren op expliciete exception in gemengde toestand en verwacht
code 2 zonder wijzigingen. Positieve regressie bewijst dat de
bevestigde één-cron-backendverwijdering nog het verwachte resultaat
geeft. De eerder bestaande één-systemd-confirmatietest blijft relevant.
Exacte code/CI ACCEPTATIE volgt alleen na terminale GitHub-readback;
geen claim dat deze afwijking ooit op een originele server werd
uitgevoerd. Public-source-fout, geen vastgestelde productie-uitval.

## 2026-11-17 — cron-only remover: vreemde bytes versus bestaande installer-separator

**Bronbevinding, géén gemeld live incident.** Het bestaande
`remove_cron_services()` herbouwde vreemde cronregels met
`splitlines()/join` en schrapte aan het einde vreemde lege regels.
De eerste source-fix op draft [#1003](https://github.com/Blacksp1d3r/runner-mcp/pull/1003),
commit `cee15ae0`, behield alle bytes buiten het managed blok, maar
hield ook de ene lege regel vast die de bestaande installer zelf vóór
een end-anchored managed blok toevoegt. De officiële validation
[#44161450337](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44161450337)
faalde terecht op
`test_managed_cron_roundtrip_preserves_independent_hourly_review`:
**1 FAIL / 4.881 PASS**. De real-systemd-proef bleef SUCCESS.

**Causale correctie:** op codecommit `938e8fb2` blijven vreemde
tekstbytes behouden. Alleen wanneer een end-anchored managed blok
exact één herkenbare, losse lege scheidingsregel heeft na een niet-lege
vreemde regel, wordt die bekende legacy-separator mee verwijderd.
Meerdere vreemde lege regels en commentaar vóór/na een managed blok
blijven onaangeraakt. De bestaande reviewer-roundtriptest en twee
nieuwe regressietests dekken de relevante gevallen.

Officieel op `938e8fb2`: **4.883 pytest PASS**, Ruff PASS,
echt disposable systemd-user PASS, schone Ubuntu-installatie PASS
en commit-attributie PASS; de vijfminutendemo en artifactbouw hebben
eigen terminal bewijs nodig. De productiecron en systemd-eigenaars
zijn niet aangeraakt, mixed-mode removal blijft DENY, en geen
automatische of handmatige oorspronkelijke hostcutover werd uitgevoerd.

**No-repeat:** een generieke bytebehoud-fix moet het historisch
installatieformaat en zijn gegenereerde scheidingsregel apart toetsen.
Een mislukte roundtrip niet oplossen met een versoepelde test of
het strippen van alle vreemde lege regels. De bestaande
`install_cron_services()` kan historische vreemde lege eindregels
bij installatie nog normaliseren; herstel van reeds verloren bytes
mag nooit worden geclaimd.
