# Clean Ubuntu installer proof boundary

This document defines the remaining reproducible proof for the clean installer after the runtime-integrity hardening merged through PR #161. It does not grant package-manager authority to Runner MCP.

## What CI already proves

Normal validation proves the installer fails closed when venv support is unavailable, rejects an unsupported pip floor, performs repeated fresh-process critical imports, performs repeated CLI smoke calls and does not activate the launcher after an integrity failure.

Those deterministic tests are not evidence that an arbitrary private host is healthy.

## Bounded installer execution

The source installer now treats package installation and post-install runtime
smoke checks as bounded operations.

- package installation has a 600-second default wall-clock limit;
- each runtime import/CLI smoke process has a 30-second default wall-clock limit;
- local operators may lower or raise those limits only within 1..3600 seconds;
- timeout exit 124 is reported explicitly as a timeout;
- exit 139 is reported explicitly as `SIGSEGV`, with guidance to stop reinstall
  loops and verify runtime/host integrity;
- a failed or timed-out install never creates the public `runner-mcp` launcher.

These bounds do not turn an unstable host into a healthy one. They make failure
finite and unambiguous enough for the operator to stop before activation.

## Separate clean-image proof

A clean-image validation may use an ephemeral Ubuntu 24.04 CI/container environment to prove the documented operator bootstrap sequence when `python3-venv` is initially absent.

The proof must be outside Runner MCP runtime authority:

1. establish that the image initially cannot create the required venv;
2. install the distribution's venv prerequisite through CI/bootstrap setup, not through Runner MCP or MCP/Agent Bus;
3. invoke the normal `install.sh` with no private host values;
4. require the installer import/CLI stress gates to pass;
5. invoke `runner-mcp --help` from the installed launcher;
6. discard the environment.

## Security boundary

The validation workflow may contain a fixed package-bootstrap command because the CI image is disposable and the workflow itself is repository-reviewed. No package name, repository, command, path or privilege operation becomes caller-selectable at runtime.

The product installer must continue to fail with guidance when venv support is absent; it must not silently call apt, sudo or another package manager.

## Private-host proof remains distinct

Even a green clean-image proof does not clear the live host incident that showed intermittent process corruption. Private-host recovery/diagnosis remains a local operator task under #108/#155 and must not be marked healthy from CI evidence.

## Acceptance

- disposable Ubuntu 24.04 environment;
- explicit initial missing-venv assertion;
- fixed bootstrap of only the OS venv prerequisite;
- normal installer succeeds afterwards;
- launcher exists only after runtime stress succeeds;
- no credentials/private infrastructure;
- no new MCP/mailbox/Agent-Bus/package-manager action;
- clean-image result and private-host integrity status remain separately reported.

## Source-only release metadata comparisons

A clean Ubuntu installer check for source-only release-roster and bounded in-memory Q7 bundle code (for example #739) verifies that the resulting package remains installable and that the fixed launcher still passes import/CLI smoke checks. It does **not** independently authenticate GitHub release pins, qualify immutable package bytes on the serving host, or establish an A6 journal, offline A7 rollback, installation authority or original-client ACK. These remain separate fail-closed operational gates.

For the 33-asset Q7 consistency child, the clean-image job also remains wholly synthetic: no actual private release asset, credential, signed metadata authority or persistent runtime slot is imported. Completion of this job is a packaging compatibility observation only, never evidence that a protected old generation can be restored after a disconnected control-path failure.


## Werkelijke manuele update- en rollbackproef op een disposable serviceproces

De bestaande \`clean-ubuntu-install-proof\`-workflow voert in een aparte
niet-root Linux-venv een handmatige distributieovergang uit van 0.1.174 naar
0.1.175, een terugrol en een herupgrade. De wheels worden uitsluitend uit de
vaste PR-baseline en de PR-kandidaat gebouwd. Iedere volgende transitie gebruikt
\`pip --no-index --no-deps\` zodat na de eerste installatie geen afhankelijkheden
stilzwijgend opnieuw opgehaald worden.

Na iedere stap start de bestaande \`runner-mcp serve\`-CLI een echte nieuwe
Uvicorn-server op een tijdelijke **loopback**poort. De test observeert de
HTTP-healthroute, \`X-Runner-MCP-Loaded-Version\`,
\`X-Runner-MCP-Instance-ID\`, de werkelijke Linux-PID/startticks en de Python-
executable. De vorige server en luistersocket moeten gestopt zijn voordat de
volgende release wordt geïnstalleerd. De private CI-configuratie en het
gegeneerde testtoken bestaan uitsluitend in de verwijderbare testwerkmap.

Dit bewijst uitsluitend de werking van het normale CLI-serviceproces in de
disposable GitHub-hosted omgeving. Het is **geen** productie-installatie,
root-kwalificatie van de originele A7-actor, systemd-overgang, geauthenticeerde
SQL-bevestiging of herstelproef van een fysieke host. Een groene workflow mag
nooit op zichzelf deploymentbevoegdheid verlenen.

## ServiceManager-busbinding en echte systemd-userdistributieproef (alleen CI)

De bestaande SystemdUserBackend gebruikt nu alleen
`XDG_RUNTIME_DIR=/run/user/<effectieve UID>` en negeert
caller-controlled XDG-/DBus-waarden. Registry, service-allowlist en
operatorstop houden ongewijzigd hun normale bevoegdheidsgrenzen.

De bestaande disposable Python 3.12-proef maakt één tijdelijke
`runner-mcp-669-disposable-manual.service` zonder enable of bootpersistentie.
ServiceManager.action start of herstart daadwerkelijk `runner-mcp serve` over
`0.1.174 → 0.1.175 → 0.1.174 → 0.1.175`, met een echte controle dat na
installatie eerst nog het vorige geladen serverproces leeft. Vervolgens
moeten unitbron, MainPID, kernelstartticks, HTTP-health, geladen versie en
instance-ID overeenstemmen. Opruimen stopt de unit vóór verwijderen van
wheel- en configuratiebestanden.

Geen cron→systemd #866 cutover, A7, productie, reboot of updatebevoegdheid.


**Historische baselinegrens (disposable test):** versie 0.1.174 bevat de
nieuwe gefixeerde user-busverbinding nog niet. Op de wegwerp-runner start of
herstart de bestaande directe `systemctl --user` de eigen testunit voor
precies die historische release, zonder het oude wheel te wijzigen. Pas op
0.1.175 worden de echte geregistreerde `ServiceManager.action` en
`ServiceManager.status` gebruikt. Uitvoer onderscheidt nadrukkelijk de
markers `LEGACY_TEST_ONLY_CONTROL` en `REGISTERED_MANAGER_ACTION`.
Er is geen productiefallback toegevoegd.


## Historische 0.1.88-broncheck tegen dezelfde nieuwe systemd-servicebeheerder

De bestaande disposable CI bouwt nu ook een wheel uit de **vaste historische
GitHub-broncommit** `ce327e5db688fe6bae835a4c181824320f01f762`
(`pyproject.toml` versie `0.1.88`) en doorloopt daarna dezelfde echte
`0.1.88 → 0.1.175 → 0.1.88 → 0.1.175`-installatie-, CLI-,
HTTP-proces- en systemd-usercyclus. Oude versie: vaste systemd-fixturemanager;
nieuwe versie: geregistreerde `ServiceManager.action`. De eerdere
`0.1.174`-proef blijft ongewijzigd en moet afzonderlijk PASS blijven.

**Bronbewijs is geen originele installatiewheel.** Deze oude versie is niet
publiek getagd als `v0.1.88`, en de gegenereerde testwheel is nooit
aangetoond byte-identiek aan de verbonden `0.1.88` of aan root-gekwalificeerde
A7-installatiebytes. Geen live update, releasepromotie, originele rollback,
cron→systemd-cutover of nieuwe autorisatie volgt uit CI.
