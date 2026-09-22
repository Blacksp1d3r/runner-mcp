# Voorstellen: CLI, installatie en gebruikservaring

Deze bevindingen komen uit het daadwerkelijk installeren van het project
(nieuwe venv, `pip install -e '.[dev]'`), het draaien van `--help` op
diverse niveaus, en het doorlezen van QUICKSTART.md/DEMO.md als "nieuwe
gebruiker".

## 1. De CLI is functioneel compleet maar heeft een steile leercurve

`runner-mcp --help` toont **19 topleveltcommando's**
(`setup, status, doctor, guide, emergency-stop, project, test-profile,
service-config, database-config, migration-config, deployment-config,
adapter, approval, autostart, completion-notifier, completion-watcher,
github-mailbox, github-watcher, serve`), waarvan meerdere weer 3-6
subcommando's hebben (`github-watcher` alleen al: `bootstrap, once, abandon,
quarantine, resolve, run`). Dat is inhoudelijk gerechtvaardigd — elke groep
komt overeen met een apart, goed gedocumenteerd stuk functionaliteit — maar
voor een eerste-keer-gebruiker is de oppervlakte groot.

De QUICKSTART compenseert dit al goed door een lineair pad te geven
("1. Get Runner MCP" t/m "8. Start Runner MCP locally"), en `runner-mcp
guide` bestaat specifiek om project-bewuste vervolgstappen te tonen. Dat is
een sterk ontwerp. Twee aanvullende suggesties:

- **Shell-completion.** `argparse` ondersteunt dit niet natief, maar een
  `argcomplete`-integratie (of een handmatig gegenereerd
  bash/zsh-completion-script als onderdeel van `install.sh`) zou de
  19×gemiddeld-3-subcommando's-oppervlakte een stuk toegankelijker maken
  zonder de CLI-structuur te wijzigen.
- **`runner-mcp guide` als standaard bij `runner-mcp` zonder argumenten.**
  Op dit moment vereist `runner-mcp --help` een expliciete `--help`-vlag;
  overweeg om `runner-mcp` zonder subcommando dezelfde output als `guide`
  te tonen (of op zijn minst een duidelijke hint "run `runner-mcp guide`
  for next steps") in plaats van de standaard argparse-foutmelding
  "the following arguments are required".

## 2. Geen `--json`/machine-leesbare output-modus

Alle CLI-commando's (`status`, `doctor`, `project list`, `queue_status`
via MCP, enz.) produceren mensvriendelijke tekstuele output. Voor een
project dat zich expliciet richt op "AI clients" als primaire gebruiker
van de MCP-laag (en waar de CLI vooral door een menselijke operator wordt
gebruikt), is dat een bewuste en logische keuze. Toch is er geen manier om
bijvoorbeeld `runner-mcp status --json` te scripten voor monitoring/
alerting buiten de MCP-laag om (bv. in een cronjob die een Slack-bericht
stuurt bij `doctor`-falen).

**Voorstel:** een optionele `--json`-vlag op `status`, `doctor` en
`queue_status`/`worker_status`-achtige commando's, die dezelfde
veiligheidsgaranties behoudt (geen private paden/credentials) maar
machine-leesbaar is. Dit is een additieve wijziging die niets aan bestaand
gedrag verandert.

## 3. Foutmelding bij ontbrekend subcommando

Bijvoorbeeld `runner-mcp github-watcher` zonder verder argument geeft de
standaard argparse-foutmelding. Omdat `github-watcher` zes subcommando's
heeft met substantieel verschillend risicoprofiel (`run` = continu proces,
`abandon`/`quarantine`/`resolve` = destructieve herstel-acties), zou een
korte een-regel-samenvatting per subcommando in de foutmelding zelf (in
plaats van pas na `--help`) de operator sneller naar de juiste keuze
sturen. Dit is een kleine polish, geen structureel probleem — `--help`
geeft de informatie al netjes.

## 4. Demo en Quickstart zijn goed, maar de "vijf minuten"-belofte is optimistisch

`docs/DEMO.md` heet "Five-minute local demo" en is stap voor stap
uitstekend geschreven. In de praktijk (zoals ook `scripts/demo-smoke.sh`
laat zien) omvat het: Python-venv aanmaken, dependencies installeren,
`setup`-wizard doorlopen, `doctor`/`status`/`guide`, testprofiel toevoegen,
emergency-stop testen, server starten, health-check pollen. Dat is
inhoudelijk correct maar op een gemiddelde machine met een koude pip-cache
realistisch eerder 8-12 minuten dan 5, vooral door de `pip install -e
'.[dev]'`-stap (dependency-resolutie + build).

Dit is geen belangrijk probleem — "vijf minuten" is een marketingclaim, geen
technische garantie — maar het zou de eerste indruk kunnen beschadigen als
een nieuwe gebruiker de klok meeneemt. Overweeg "quick" of "guided" in
plaats van een harde tijdsclaim, of voeg een voetnoot toe ("tijd is
afhankelijk van netwerksnelheid voor de eerste dependency-installatie").

## 5. `runner-mcp doctor` en `status` verbergen bewust private paden — goed, maar mist een "waarom faalt dit"-verwijzing

Beide commando's zijn expliciet ontworpen om geen private paden/credentials
te tonen (een sterk, consistent gedocumenteerd veiligheidsprincipe). Het
inherente spanningsveld is dat een operator die een `doctor`-fout probeert
te debuggen, soms exact het private pad nodig heeft om het probleem te
vinden (bv. "permissiefout op configuratiebestand X"). Voor zover uit de
documentatie blijkt lost Runner MCP dit al netjes op door generieke,
categoriale foutmeldingen te geven zonder paden — dat is de juiste afweging
qua veiligheid. Eventuele verbetering: een `doctor --verbose`-modus die
expliciet waarschuwt "dit toont private lokale paden, deel deze output niet
publiekelijk" voordat het meer detail toont, voor het geval een operator
echt vastzit. Dit zou optioneel en expliciet opt-in moeten blijven om het
bestaande veiligheidsprincipe niet te verzwakken.

## 6. Operator-wrapper (`install-operator.sh`) is knap, maar onderbelicht in README

De service-account/operator-account-scheiding (`install-operator.sh`) is
een doordachte oplossing voor een reëel operationeel probleem (Runner MCP
draait onder een dedicated service-account, de mens logt in via een ander
account). README.md noemt dit kort in de "I just want to use it"-sectie,
maar het concept "waarom zou ik dit ooit nodig hebben" wordt pas in
QUICKSTART.md sectie 2.5 uitgelegd. Voor een nieuwe lezer die snel README
scant, is niet meteen duidelijk of dit voor hen relevant is.

**Voorstel:** een half-zin extra in README direct bij de
`install-operator.sh`-vermelding: "Sla dit over als je Runner MCP gewoon
onder je eigen gebruikersaccount draait" — zodat de meerderheid van de
lezers (single-account-gebruikers) meteen weet dat ze dit kunnen negeren.

## 7. Layout van de repository zelf

De top-level indeling (`docs/`, `security/`, `roadmap/`, `handover/`,
`config/`, `scripts/`, `src/`, `tests/`) is logisch en consistent met wat
elk document belooft. Twee kleine observaties:

- `handover/` bevat op dit moment één bestand (`CURRENT_STATE.md`). Een
  map voor één bestand is niet fout, maar als dit bestand niet groeit naar
  meerdere handover-documenten, zou het net zo goed op het hoogste niveau
  kunnen staan (`CURRENT_STATE.md` naast `CHANGELOG.md`). Omgekeerd: als de
  bedoeling is dat hier per grote milestone een apart bestand bijkomt, zou
  dat expliciet gedocumenteerd mogen worden (bv. in AGENTS.md, dat al zegt
  "Update handover/CURRENT_STATE.md after meaningful milestones" — dat
  bevestigt dus dat één continu bijgewerkt bestand de bedoeling is, wat de
  losse map enigszins overbodig maakt).
- `scripts/` bevat twee bestanden (`demo-smoke.sh`,
  `release-artifact-smoke.sh}`) die beide alleen door CI worden aangeroepen.
  Een korte `scripts/README.md` (twee zinnen: wat elk script doet en dat ze
  door CI worden gebruikt, niet handmatig) zou voorkomen dat een lezer ze
  per ongeluk aanziet voor door de gebruiker uit te voeren hulpscripts.
