# Verbetervoorstellen Runner MCP

Deze map is toegevoegd op verzoek van de gebruiker na het lezen van de volledige
roadmap, alle documentatie (README, QUICKSTART, AGENTS.md, CONTRIBUTING,
CHANGELOG, `docs/*`, `security/*`, `handover/CURRENT_STATE.md`), de broncode
onder `src/runner_mcp/`, de tests, de install-scripts en de CI-workflow.

**Er is niets aan de bestaande repository veranderd.** Deze map bevat alleen
voorstellen/observaties, geen implementatie. De lokale testsuite is wel
uitgevoerd (niet gewijzigd) om een aantal claims te verifiëren: `pytest`
geeft momenteel **685 passed, 1 warning** en `ruff check .` geeft **All
checks passed**, op een verse Python 3.12-venv.

## Overzicht van de bestanden

| Bestand | Onderwerp |
| --- | --- |
| [ROADMAP.md](ROADMAP.md) | Structuur, leesbaarheid en inhoud van `roadmap/ROADMAP.md` |
| [CODE.md](CODE.md) | Architectuur en onderhoudbaarheid van de Python-broncode |
| [DOCS.md](DOCS.md) | Consistentie en kwaliteit van de documentatie |
| [UX.md](UX.md) | CLI, installatie en "gebruik"-ervaring |
| [TESTING_CI.md](TESTING_CI.md) | Tests, CI en releaseproces |
| [QUICK_WINS.md](QUICK_WINS.md) | Kleine, snel te doen concrete fixes |

## Algemene indruk

Runner MCP is ongewoon volwassen voor een pre-alpha project: de
veiligheidsgrenzen zijn overal expliciet gedocumenteerd, de testsuite is
groot (685 tests) en groen, `ruff` is schoon, er staan geen TODO/FIXME/HACK-
markers in de code, en elke fase van de roadmap heeft een duidelijke
"implemented / still deferred"-structuur. De belangrijkste
verbeterpotentie zit niet in "dingen die kapot zijn", maar in:

1. **omvang en navigeerbaarheid** — de roadmap (573 regels, 28 fases) en een
   paar broncodebestanden (`cli.py`: 1585 regels, `server.py`: 1421 regels)
   zijn functioneel prima maar zwaar om in één keer te overzien;
2. **documentatie-drift** — een paar concrete cijfers/claims lopen uiteen
   tussen bestanden (zie DOCS.md);
3. **onboarding-ervaring** — het venijnige verschil tussen "makkelijk voor
   iemand die de threat model al begrijpt" en "makkelijk voor een nieuwe
   gebruiker" (zie UX.md).

Zie de losse bestanden voor details en concrete voorstellen per onderwerp.
