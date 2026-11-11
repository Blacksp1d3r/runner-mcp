# RMCP — Hersteltransactie kan door tweede updater overschreven worden (2026-11-07)

## Symptoom / risico
`SelfUpdatePackageInstaller.begin_transaction` controleerde via `pending_transaction()` dat geen lokale hersteltransactie bestond en publiceerde vervolgens `self-update-install-transaction.json` via `os.replace`. Die twee acties zijn niet atomair. Publiceert een andere updater een transactie tussendoor, dan kon de latere writer het herstelbewijs van de eerste update ongemerkt vervangen. In een onbewaakte updateketen verliest de eerste campagne zijn herstelbasis. Dit was een **broncodebevinding**, geen bewezen productie-incident en geen uitgevoerde twee-host update.

## Verifieerbaar herstel
[PR #964](https://github.com/Blacksp1d3r/runner-mcp/pull/964) hoofdbranch `ecb5a52d3b6517c0787cbf2eafa924ca6ffcc2df`, versie 0.1.155, hergebruikt dezelfde transactie en maakt de definitieve publicatie met één `os.link(temp, target, follow_symlinks=False)` zonder vervangen. Bij al bestaand doel of ontbrekende ondersteuning STOP. Tijdelijke bron wordt alleen na een geslaagde link vrijgegeven. Bestaande bestands- en directory-`fsync`, schema, private modus 0600 en recovery-procedure blijven.

## Negatieve tests / begrenzing
Twee regressies in de bestaande `tests/security/test_self_update_install.py` injecteren respectievelijk een geldige concurrerende transactie ná de begincontrole en een niet-beschikbare atomische link. Geen oorspronkelijk record wordt gewijzigd; onveilige fallback wordt geweigerd. Officiële PR-head 7/7 CI-controles geslaagd, met echte disposable systemd, schone Ubuntu-installatie, volledige vijfminutendemo en artifact na alle basischecks. **Dit bewijst de bron/CI-correctie, geen originele actieve wheelversie, zelfherstel na reboot, zes echte rollen of oorspronkelijke-client ACK.**

## Tweede foutmodus: verouderde CLEAR verwijdert nieuw herstelbewijs (2026-11-09)

Ook ná de no-replace oplossing van v0.1.155 bleef `clear_transaction()` lockvrij: twee legitieme oude afsluiters konden dezelfde vorige transactie observeren; afsluiter A wist deze, een nieuwe updater maakt zijn eigen transactie, afsluiter B wist vervolgens de **nieuwe** transactie. Een controle op pad of inode gevolgd door `unlink()` is geen atomaire compare-and-delete. Dit was een **bronanalyse**, niet een vastgestelde productiegebeurtenis.

**Afgesloten bron/CI-fix:** [PR #967](https://github.com/Blacksp1d3r/runner-mcp/pull/967) 0.1.157, squash/main `b024cb565954f652ccd23c47a9f3a422210c2526`. De bestaande ene transactie blijft de herstelbron; BEGIN en CLEAR verkrijgen dezelfde permanente owner-private Linux-`flock` op exact dezelfde directory/inode. Verkeerde uid, mode, symlink, hardlink, conflict of ontbrekende flock sluit de actie fail-closed. CLEAR vereist de oorspronkelijke job-ID en kan geen nieuwe/andere record verwijderen. Na procesverlies wordt de kernel-lock vrijgegeven en blijft het bestand voor hergebruik bestaan.

**Tests:** exact-head [validation 42660259230](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42660259230) SUCCESS met 4.734 pytest, Ruff, release-reservering, systemd en clean 5-minutendemo; schone Ubuntu [42660259218](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42660259218) en attribution [42660259310](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42660259310) SUCCESS. Regresstests voor verkeerde afsluiter/nieuwe job, concurrerende writer, illegale lockeigenschappen, geblokkeerde/ontbrekende kernel-lock en automatische vrijgave na procesexit. Geen nieuw updater-/lockbeheersysteem.

**Beperking:** origineel `github-runner` serving 0.1.88/loaded wheel #669 blijft historisch; 0.1.157 is niet bewezen live geïnstalleerd. A6 off-target #942, A7 onafhankelijke offline rollback #943, echte campagnegebonden oorspronkelijke-client ACK open. CI-artifact en gemergede bron geven geen productierechten.

## Voorkomen van herhaling
Een voorafgaande `exists`-/`pending`-controle is geen exclusieve lease en nooit voldoende vóór een vervangende filesystempublicatie. Gebruik de bestaande atomische no-replace-functie op hetzelfde filesystem en test een echte concurrent tussen preflight en publicatie. Maak geen tweede updater, journal of privilegepad. Voor echte automatische uitrol blijft originele service-identiteit, externe A6, zelfstandige A7 en ACK vereist.
