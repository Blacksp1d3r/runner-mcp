# Voorstellen: broncode-architectuur en onderhoudbaarheid

Deze bevindingen komen uit eigen inspectie plus een gerichte doorlichting
van `src/runner_mcp/`, `tests/`, `install.sh`, `install-operator.sh` en
`config/projects.example.yml`. Alle regelverwijzingen zijn actueel op het
moment van schrijven. Nogmaals: dit zijn **observaties, geen wijzigingen** —
er is niets aan de code aangepast.

Belangrijk om vooraf te zeggen: dit zijn allemaal onderhoudbaarheids- en
DX-opmerkingen (developer experience), **geen** kritiek op de expliciete
veiligheidsgrenzen (geen `shell=True`, geen database-restore, enz.) — die
zijn bewust en goed gedocumenteerd, en blijven met deze voorstellen
onaangetast.

## 1. `server.py` is één grote functie

`build_mcp()` (server.py:260–1421) is een enkele functie van ~1160 regels
die (a) alle managers instantieert én (b) alle 38 `@mcp.tool()`-handlers als
geneste closures definieert. Er is geen scheiding tussen "dependencies
opzetten" en "tools registreren" — om één tool te vinden of te wijzigen moet
je door de hele functie scrollen.

**Voorstel:** splits in een `_build_dependencies(settings)` die een klein
dataclass/namespace teruggeeft, en een reeks `register_<domain>_tools(mcp,
deps)`-functies per toolgroep (bv. `register_file_tools`,
`register_test_tools`, `register_service_tools`,
`register_deployment_tools`, `register_bridge_tools`). Dat maakt elke groep
los testbaar en los leesbaar, zonder de bestaande registratievolgorde of
gedrag te veranderen.

## 2. Herhaalde try/except/audit-boilerplate in toolhandlers

Zo'n 19 toolhandlers herhalen dezelfde vorm:

```python
try:
    result = X()
except SomeError as exc:
    audit(...)
    raise ValueError(str(exc)) from None
```

(bv. server.py:774-784, 789-795, 800-806, 811-821, 826-836, 968-975,
1134-1141, 1203-1210). Elke toolcategorie heeft bovendien een eigen lokale
`_audit_*`-closure die hetzelfde soort werk doet.

**Voorstel:** een decorator of contextmanager zoals `@audited_tool(name=...,
errors=(...))` zou ~150 regels duplicatie schrappen én het structureel
onmogelijk maken om audit-logging te vergeten bij een nieuwe tool — nu is
dat een menselijke discipline-eis per nieuwe handler.

## 3. `Settings.from_mapping()` herhaalt env-parsing 12x

server.py:67-215 herhaalt "parseer int/pad uit env-variabele, gooi
`RuntimeError` met specifieke boodschap" een stuk of 12 keer (o.a. regels
76-82, 94-96, 98-107, 109-119, 121-129, 131-133, 135-168).

**Voorstel:** kleine helpers `_env_int(name, default, lo, hi)` en
`_env_abs_path(name)` zouden dit blok ongeveer halveren en het risico op
kopieerfouten in foutmeldingen verkleinen.

## 4. `cli.py`: 1585 regels, 80 subparsers, herhaalde bevestigingslogica

`cli.py` bevat 80 `add_parser(...)`-aanroepen en 23 `cmd_*`-dispatch-
functies, elk met hetzelfde `if args.x_action == "list": ... elif == "add":
... elif == "remove": ...`-patroon (cli.py:302-356, 387-439, 442-493,
495-529, 531-569, 571-610).

Het destructieve-bevestigingsblok:

```python
expected = f"REMOVE {...}"
input(f"Type {expected} to continue: ")
```

is letterlijk 6x gekopieerd (cli.py:348-349, 427-428, 480-481, 520-521,
560-561, 598-599).

**Voorstellen:**
- een gedeelde `_confirm(expected: str) -> None`-helper verwijdert ~30
  regels duplicatie en garandeert consistente bewoording/gedrag bij elke
  destructieve actie;
- overweeg `cli.py` op te splitsen in een `cli/`-package met één module per
  commandogroep (`cli/project.py`, `cli/deployment.py`,
  `cli/github_mailbox.py`, …) plus een dunne `cli/__main__.py` die de
  parser samenstelt. Dat is een grotere refactor, maar bij 19
  topleveltcommando's met samen tientallen subcommando's begint één bestand
  de praktische navigatiegrens te naderen.

## 5. `config_manager.py`: herhaald CRUD-patroon

`config_manager.py` (1039 regels) bevat ~10 bijna-identieke add/remove-
paren (`add_project`/`remove_project`, `add_test_profile`/
`remove_test_profile`, `add_service_config`/`remove_service_config`,
`add_database_config`/`remove_database_config`,
`add_migration_config`/`remove_migration_config`,
`add_deployment_config`/`remove_deployment_config`), elk met hetzelfde
recept: `_load_for_edit` → dict muteren → `ProjectRegistry(...)` →
`validate_codes()` → `_save_registry`.

**Voorstel:** een generieke `_mutate_project(config_dir, project, mutator)`
zou het grootste deel hiervan kunnen absorberen.

## 6. Geen `logging`-gebruik in de hele codebase

In ~15.300 regels `src/runner_mcp` wordt de standaard `logging`-module
nergens gebruikt. Langlopende achtergrondprocessen (`github_watcher.py`,
`completion_delivery.py`, `github_mailbox.py`) hebben geen operationele
logging — alleen de JSONL-audittrail (op toolcall-niveau) en CLI-`print()`.

**Praktisch gevolg:** als een watcherproces onder systemd vastloopt, heb je
buiten `audit.jsonl` niets om te debuggen. Dit is geen veiligheidsprobleem
(de audittrail bevat bewust geen gevoelige data), maar wel een operationeel
gat.

**Voorstel:** een bewust minimale `logging`-laag (stdout/stderr, door
systemd/journald opgevangen) voor watcher-lifecycle-events (start, stop,
cyclus begonnen/klaar, fouten) — zonder de bestaande scrubbing-garanties
van de audittrail te wijzigen.

## 7. Enkele plekken waar de fout volledig verdwijnt

- `github_watcher.py:621-624`: `except Exception: # noqa: BLE001` verwerpt
  de eigenlijke exceptie volledig (zelfs `str(exc)` wordt niet bewaard) en
  fabriceert een generieke `AMBIGUOUS_CLAIM`-observatie. Dat is bewust
  fail-closed, maar de echte oorzaak is achteraf onherleidbaar.
- Vergelijkbaar patroon (zwijgend falen zonder details) bij
  `deployment_jobs.py:328` en `test_runner.py:1025`.

**Voorstel:** bewaar minstens `type(exc).__name__` (geen bericht, geen
stacktrace) in een lokaal debug-logregel, zodat een operator bij herhaalde
`AMBIGUOUS_CLAIM`-gevallen tenminste een foutcategorie heeft zonder dat er
gevoelige inhoud lekt.

## 8. Het "atomic private write"-patroon is 8x los geïmplementeerd

Het patroon "schrijf privébestand atomisch via tempfile + `os.replace` +
0600/0700-permissies" is **niet gedeeld**, maar apart geïmplementeerd in
minstens 8 bestanden: `onboarding.py:222`, `config_manager.py:92`,
`bridge_replay.py:204`, `completion_delivery.py:348`,
`cron_autostart.py:267`, `database_manager.py:199/236`,
`deployment_jobs.py:114`, `deployment_manager.py:240/498`,
`test_runner.py:201`, `github_watcher.py:144`, `autostart.py:256` — in
totaal 80 chmod-aanroepen met `0o600`/`0o700` verspreid over de codebase.

**Risico:** een toekomstige bugfix aan dit patroon (bv. een
fsync-volgorde-probleem) moet N keer apart worden toegepast, met kans op
inconsistentie.

**Voorstel:** een gedeelde `runner_mcp/secure_io.py` met één
`atomic_write_private(path, content, mode=0o600)`-functie die alle
bovenstaande aanroepplekken vervangt. Dit is een mechanische refactor met
laag risico (het gedrag blijft identiek) maar hoge onderhoudswinst.

## 9. Ontbrekende docstrings

333 van de 380 publieke (niet-`_`) functies in `src/runner_mcp` hebben geen
docstring (~88%), inclusief bijna alle `cmd_*`-handlers in `cli.py` (regels
94, 138, 172, 191, 274, 302, 359, 387, 442, 495, 531, 571, 635, 682) en de
publieke add/remove/list-API van `config_manager.py`. Geen van
`server.py`, `cli.py`, `config_manager.py` of `deployment_manager.py` heeft
een moduledocstring, ondanks dat dit de belangrijkste integratie-
oppervlakken zijn.

Dit is geen verplicht "commentaar overal"-punt (het project volgt bewust
een stijl van weinig commentaar, wat op zichzelf prima is), maar een korte
one-line moduledocstring bovenaan de vier genoemde bestanden ("Dit bestand
bevat de MCP-toolregistratie / de CLI-dispatch / …") zou de eerste
oriëntatie voor nieuwe bijdragers merkbaar versnellen.

## 10. Adapter-extensiepad is minder pluggable dan de docs suggereren

`adapters/registry.py:14-17` hardcodet `_ADAPTERS` als een privé
module-dict met alleen `GenericAdapter()` en `PythonAdapter()`. Er is geen
`register_adapter()`-entrypoint en geen `importlib.metadata`
entry-points-gebaseerde plugin-discovery.

`docs/USING_AND_EXTENDING.md` beschrijft "Level B — built-in adapter" als
extensiepad en zegt expliciet "Adapters must be registered in code" — dus
dit is een **bewuste** keuze (geen dynamische imports, veiligheidsgrens),
geen bug. Maar de praktische consequentie is dat een derde partij die een
adapter wil toevoegen, het geïnstalleerde package moet forken/patchen, niet
gewoon een nieuw bestand kan droppen. Dat mag zo blijven om
veiligheidsredenen, maar zou expliciet benoemd mogen worden in de docs in
plaats van impliciet te blijven ("adapters zijn per ontwerp
niet-pluggable; nieuwe adapters vereisen een pull request tegen dit
package").

Kleine bijkomstige verbetering: `get_adapter()` (registry.py:24-28) gooit
een generieke `AdapterError("Unknown or disabled project adapter")` zonder
de geldige ID's te noemen — een foutmelding die de bekende adapter-ID's
opsomt (`generic`, `python`) is net iets bruikbaarder voor iemand die een
typefout maakt.

## 11. Testdekking

De testsuite is groot en overwegend goed verdeeld over de brongoden
(`test_runner`, `deployment_manager`, `config_manager`, `database_manager`,
`service_manager`, `approval_manager`, `source_control`, `file_access`,
`operational_safety` hebben allemaal eigen, vaak omvangrijke testbestanden).
Een paar concrete observaties:

- `audit.py` (36 regels) heeft geen eigen testbestand — alleen indirect
  meegetest via integratietests. Voor zoiets kleins en fundamenteels
  (append-only audittrail, bestandspermissies) is een klein direct
  testbestand (`test_audit.py`) goedkoop en verhoogt het vertrouwen dat de
  audittrail zelf niet stiekem breekt.
- `server.py` (1421 regels) heeft geen eigen unittestbestand; het wordt
  alleen indirect gedekt via `tests/integration/test_mcp_http.py`,
  `tests/unit/test_auth.py` (14 regels) en
  `tests/security/test_http_security.py`. De ~15 validatietakken in
  `Settings.from_mapping()` (server.py:67-183) hebben geen eigen unittest.
- `tests/unit/test_adapters.py` is met 58 regels vrij dun voor
  `adapters/` als geheel (registry, base, generic, python samen) — juist
  omdat dit het gedocumenteerde uitbreidingspunt is, zou hier iets meer
  dekking passen (bv. expliciete tests voor "onbekend adapter-ID faalt
  closed" en "symlinked marker wordt genegeerd").
- `tests/unit/test_cli.py` is met 1378 regels substantieel, maar het is de
  moeite waard om gericht te checken of `cmd_migration_config`,
  `cmd_deployment_config` en de `adapter capacity`/`inspect`-paden evenveel
  aandacht krijgen als de vroegere, kleinere commando's.

## 12. `install.sh` / `install-operator.sh`

Beide scripts zijn al goed: `set -euo pipefail`, symlink-checks,
regex-validatie van de service-gebruikersnaam, en een
eigendoms-/herkenningscheck voordat een bestaande wrapper wordt
overschreven. Kleine verbeterpunten:

- `install.sh` geeft geen melding bij een herinstallatie ("al
  geïnstalleerd, wordt opnieuw geïnstalleerd") en heeft geen `--help`.
- `install.sh` controleert niet vooraf of `python3 -m venv` beschikbaar is;
  op een minimale Debian/Ubuntu-image zonder `python3-venv` komt de fout
  als ruwe pip/venv-traceback in plaats van een duidelijke "installeer
  python3-venv"-melding.
- Geen van beide scripts biedt een uninstall-pad of een post-install
  zelftest (bv. `runner-mcp --version` uitvoeren om te bevestigen dat de
  installatie werkt) — nu merk je een kapotte install pas bij `runner-mcp
  setup`.
- `install-operator.sh` neemt aan dat `sudo` aanwezig/geconfigureerd is
  voor `SERVICE_USER`, maar controleert dat nooit vooraf
  (`command -v sudo`); het faalmodus is een ruwe "sudo: command not
  found" in plaats van een script-eigen foutmelding.

## 13. `config/projects.example.yml`

Het voorbeeld is correct en volgt het schema, maar toont slechts een
deel van het echte configuratie-oppervlak: geen `database.migrations`-blok
(terwijl `deployment.run_migrations: false` impliceert dat migraties een
echte feature zijn), geen tweede `test_profiles`-item (bv. naast "lint" ook
een "test"-profiel), en geen voorbeeld van
`allowed_services`/`health_expected_status`/`health_timeout_seconds`.

Er staan ook geen inline-commentaarregels in — een nieuwkomer die dit
bestand kopieert heeft geen in-file aanwijzing welke velden verplicht vs.
optioneel zijn, of een verwijzing naar `runner-mcp project add` als
aanbevolen manier om configuratie te genereren in plaats van dit bestand
met de hand te bewerken.

## Prioritering (mijn inschatting)

Als er beperkte tijd is, zou ik in deze volgorde pakken:

1. **#8 (gedeelde secure_io-helper)** — laag risico, mechanisch, sluit een
   reëel onderhoudsrisico.
2. **#2 en #4 (audited_tool-decorator, `_confirm`-helper)** — laag risico,
   voorkomt toekomstige "vergeten audit-call"-bugs.
3. **#6 (basale logging voor watchers)** — geen architectuurwijziging,
   directe operationele winst.
4. **#1 en #4-refactor (server.py/cli.py opsplitsen)** — waardevol maar
   groter, alleen doen als er toch nieuwe tools/commando's bijkomen.
