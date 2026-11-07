# RMCP — Hersteltransactie kan door tweede updater overschreven worden (2026-11-07)

## Symptoom / risico
`SelfUpdatePackageInstaller.begin_transaction` controleerde via `pending_transaction()` dat geen lokale hersteltransactie bestond en publiceerde vervolgens `self-update-install-transaction.json` via `os.replace`. Die twee acties zijn niet atomair. Publiceert een andere updater een transactie tussendoor, dan kon de latere writer het herstelbewijs van de eerste update ongemerkt vervangen. In een onbewaakte updateketen verliest de eerste campagne zijn herstelbasis. Dit was een **broncodebevinding**, geen bewezen productie-incident en geen uitgevoerde twee-host update.

## Verifieerbaar herstel
[PR #964](https://github.com/Blacksp1d3r/runner-mcp/pull/964) hoofdbranch `ecb5a52d3b6517c0787cbf2eafa924ca6ffcc2df`, versie 0.1.155, hergebruikt dezelfde transactie en maakt de definitieve publicatie met één `os.link(temp, target, follow_symlinks=False)` zonder vervangen. Bij al bestaand doel of ontbrekende ondersteuning STOP. Tijdelijke bron wordt alleen na een geslaagde link vrijgegeven. Bestaande bestands- en directory-`fsync`, schema, private modus 0600 en recovery-procedure blijven.

## Negatieve tests / begrenzing
Twee regressies in de bestaande `tests/security/test_self_update_install.py` injecteren respectievelijk een geldige concurrerende transactie ná de begincontrole en een niet-beschikbare atomische link. Geen oorspronkelijk record wordt gewijzigd; onveilige fallback wordt geweigerd. Officiële PR-head 7/7 CI-controles geslaagd, met echte disposable systemd, schone Ubuntu-installatie, volledige vijfminutendemo en artifact na alle basischecks. **Dit bewijst de bron/CI-correctie, geen originele actieve wheelversie, zelfherstel na reboot, zes echte rollen of oorspronkelijke-client ACK.**

## Voorkomen van herhaling
Een voorafgaande `exists`-/`pending`-controle is geen exclusieve lease en nooit voldoende vóór een vervangende filesystempublicatie. Gebruik de bestaande atomische no-replace-functie op hetzelfde filesystem en test een echte concurrent tussen preflight en publicatie. Maak geen tweede updater, journal of privilegepad. Voor echte automatische uitrol blijft originele service-identiteit, externe A6, zelfstandige A7 en ACK vereist.
