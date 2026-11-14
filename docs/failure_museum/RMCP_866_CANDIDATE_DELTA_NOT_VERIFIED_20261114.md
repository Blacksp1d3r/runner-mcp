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
