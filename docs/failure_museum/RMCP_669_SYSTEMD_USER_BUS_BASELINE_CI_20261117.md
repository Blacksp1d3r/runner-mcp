# Runner-MCP #669 — CI-begingeneratie zonder systemd-userbus (17 november 2026)

## Incident

De eerste echte systemd-gebruikersservice-proef gebruikte de historische
Python-wheel **0.1.174** om een eigen GitHub-hosted testunit te starten. De
distributie- en directe HTTP-procesproef waren geslaagd, maar de statusactie
via de oude `ServiceManager` gaf `ServiceManagerError`.

- Originele fout: [Clean Ubuntu #44103844441](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44103844441), `DISPOSABLE_SYSTEMD_STOP: ServiceManagerError`.
- Eenmalige gericht toegevoegde status-only diagnose: [#44104622573](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44104622573). Echte testunit `LoadState=loaded`, `ActiveState=inactive`, `MainPID=0`; `MCP_DISPOSABLE_SYSTEMD_DIAG_STATUS_READ=FAILED`. Geen privéstatus of stdout/stderr gepubliceerd.
- De oude bron `SystemdUserBackend._run` stripte de voor `systemctl --user` noodzakelijke `XDG_RUNTIME_DIR`; het kandidaatpatch was juist **nog niet** geïnstalleerd in de baseline 0.1.174. De testcase kon de nieuwe oplossing daardoor onmogelijk aantonen.

## Oorzaak en correctie

Geen mislukte A7-autorisatie en geen defecte geïnstalleerde unit:
de test verwarde de **historische baseline-backend** met de **nieuwe
kandidaat-backend**. Er is geen willekeurige bus, root-toegang of extra
servicecontroller geïntroduceerd.

1. Bron 0.1.175 geeft alleen `XDG_RUNTIME_DIR=/run/user/<effectieve UID>`
   door aan de vaste `systemctl --user`-argv; caller-env wordt genegeerd.
2. De historische, originele 0.1.174-wheel blijft byte-identiek; alléén
   binnen disposable CI wordt zijn vaste eigen testunit via reeds bestaande
   `systemctl --user` gestart en teruggezet.
3. Voor beide 0.1.175-servicegeneraties moet juist de **echte nieuwe**
   geregistreerde `ServiceManager.action` starten/herstarten en
   `ServiceManager.status` plus echte HTTP/PID/startticks kloppen.
4. De testcleanup stopt uitsluitend de eigen testunit vóór de tijdelijke
   installatie- en configuratiebytes verdwijnen.

## Acceptatiebewijs en grenzen

Op [PR #1004 HEAD `0e0895fa7aedaeb9ae1c6813168a87fa9c8cff15`](https://github.com/Blacksp1d3r/runner-mcp/commit/0e0895fa7aedaeb9ae1c6813168a87fa9c8cff15)
hebben [Clean Ubuntu #44105391678](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44105391678),
[validation #44105391672](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44105391672)
en [attributie #44105391693](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44105391693)
alle **TERMINAL SUCCESS**. Vier echte versies, twee kandidaat-ServiceManager-
herstarts en geverifieerde kernel- en HTTP-generaties PASS.

**GEEN** productie-update, originele A7-cutover, historische 0.1.88-serving
activering, geautoriseerde SQL-ACK of fysieke reboot. De oude service-manager-
route mag niet als generieke productie-workaround worden geïmplementeerd.
De onafhankelijk vastgestelde #866-cronflakiness hoort bij de bestaande
#866-eigenaar en het bestaande #866 Failure Museum, niet bij deze oorzaak.

## Volgende historische baselinetest: 0.1.88 (2026-11-17)

Dezelfde systemd-userbusfout heeft ook de **onveranderde** bron van 0.1.88:
er is geen vaste `XDG_RUNTIME_DIR` in zijn historische ServiceManager. De nu
**geslaagde**, extra CI-test koppelt rechtstreeks `systemctl --user` uitsluitend
aan de eigen CI-wegwerpunit bij beide historische 0.1.88-stappen. Voor de twee
0.1.175-stappen moet de echte `ServiceManager.action` zijn huidige vastgepinde
userbus en geregistreerde servicealias gebruiken. [Clean Ubuntu #44121305525](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/44121305525)
is TERMINAL SUCCESS over `0.1.88→0.1.175→0.1.88→0.1.175`.
Geen vervangende historische wheel voor de originele host is vrijgegeven,
en geen oorspronkelijke server, A7 of cronunit gewijzigd. De uit de publieke
GitHub-commit opnieuw gebouwde 0.1.88-testwheel heeft uitdrukkelijk GEEN
bewezen gelijkheid met de echte serverinstallatie.
