# Runner-MCP Failure Museum — GitHub-watcher-cursorstatus veranderde opslag (2026-10-28)

Eigenaar: bestaande [Runner-MCP #616](https://github.com/Blacksp1d3r/runner-mcp/issues/616), onder #531. Broncorrectie [PR #876](https://github.com/Blacksp1d3r/runner-mcp/pull/876) in 0.1.108. Geen bewezen live installatie.

## Oorzaak

De bestaande `GitHubWatcherCursorStore.read()` gebruikte dezelfde `_open()`-schrijfroute als `initialize/advance`, met `O_RDWR|O_CREAT` en onvoorwaardelijke `fchmod(fd, 0o600)`. Alleen status lezen kon daardoor een ontbrekende cursor aanmaken en rechten van een bestaand bestand aanpassen. Op een alleen-lezen volume kon deze uitleesfunctie ten onrechte mislukken zelfs wanneer het bestaande statusbestand leesbaar was.

## Herstel

De bestaande leesroute opent een aanwezig privébestand nu met `O_RDONLY` (en de bestaande no-follow-beveiliging), zonder `O_CREAT` of `fchmod`. Bij een ontbrekende cursor blijft het resultaat `None` en wordt niets aangemaakt. Onveilige eigenaar/rechten worden gemeld zonder stille reparatie; ongeldige UTF-8 levert een begrensde fout op. `initialize` en `advance(expected_sha,new_sha)` behouden de expliciete schrijf- en cursor-CAS-functie.

## Acceptatie en preventie

PR #876 laatste head `e0f5a7aa22876c20d39aaa44b93331dcfd7eb095`, squash `6762f8681dcbf42916713bf67b43ec193195e594`. GitHub attribution #40644954823, schone Ubuntu #40644954709 en volledige validatie #40644954710 (Ruff, pytest, release, clean demo) **SUCCESS**. Synthetische regressies controleren geen creatie, geen chmod, uitsluitend lees-flags, weigering zonder rechtenherstel en ongeldige bestandsinhoud. Testfixtures voor inhoudfouten zijn expliciet 0600: gewone 0644-testbestanden zouden anders uitsluitend de eerdere eigenaarscontrole testen.

**Voorkoming:** status- en inspectie-operaties mogen geen writer-open en onbedoelde reparatie delen met muterende operaties. Test afwezig en niet-schrijfbaar maar leesbaar opslagpad apart van een echte bootstraphandeling.

**Niet bewezen:** origineel actieve watcher op github-runner heeft bron v0.1.108 niet aangetoond. #616 blijft OPEN: geen quarantainebewuste veilige cursorfastforward, geen terminale immutable poison-bewijzen, geen volledig head/CAS/worker-resultaat+ACK of productieherstel. #615/#617 en Fabric blijven eigenaar van hun bestaande grenzen.
