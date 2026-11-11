# Runner-MCP Failure Museum — toolcatalogusversie en concurrente main bij #269 (2026-10-28)

**Eigenaar:** bestaand [Runner-MCP #269](https://github.com/Blacksp1d3r/runner-mcp/issues/269). **Herstel:** [source PR #881](https://github.com/Blacksp1d3r/runner-mcp/pull/881), merge `3e80a62fd28dc8a80010f9ca27bc15b77da25816`. **Geen live installatie.**

## Wat misging

- Toevoegen van een nieuwe geregistreerde MCP-tool maakte de bestaande statische `docs/operations/TOOL_CATALOGUE_BASELINE.json` onvolledig. De eerste CI wees dit correct af (source ≠ goedgekeurde inventaris).
- Na bijwerken van de baseline vereiste de release reservation gate nog steeds de **actuele** PR-basis. Een andere werkstroom had intussen de bestaande systemd-documentatie via #880 gemerged, zonder bronversie te wijzigen. De vorige branch-head had de oudere basis; geen codefout en geen reden om de releasecontrole te versoepelen.
- De derde CI passeerde Ruff en vrijwel alle pytest-tests, maar `tests/unit/test_tool_catalogue_attestation.py` had het oude **hardgecodeerde totaal 106**. Na toevoegen van `operational_snapshot` was het goedgekeurde exacte aantal **107**; 4.258 andere tests waren groen.

## Correctie

- Registreer nieuwe toolnamen expliciet in de bestaande, exact gesorteerde en geattesteerde baseline. Geen dynamische wildcard, automatische acceptatie of introspectie tijdens dispatch.
- Herbaseer de **bestaande** PR met een Git-tree op de actuele `main`; behoud wijzigingen van de andere eigenaar in ROADMAP/CURRENT_STATE/SESSION_HANDOFF. De 9 bron- en metadatafiles van #269 werden apart gekopieerd, zonder andere bestanden te overschrijven; force-with-lease beschermde de PR-head.
- Laat de bestaande test de broncatalogus vergelijken met de **exacte goedgekeurde baseline** en de daarin vastgelegde ondergrens. Geen vaste numerieke verwachting naast dezelfde canonieke inventaris.

## Acceptatie

Finale exact-head `8f3784f7ec66633e9531e2014e5bce1fd9c060b2`: [commit-attributie #40647727328](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40647727328), [schone Ubuntu-installatie #40647727361](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40647727361), [volledige CI #40647727455](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40647727455) **SUCCESS**, inclusief releaseartefact en clean demo. Versie 0.1.110 is GitHub-bron; oude originele server **niet** bijgewerkt.

**Preventie:** bij een nieuwe MCP-tool in één bronwijziging de toolcatalogus, exacte inventaristest en vier versie-metadata meebewegen. Bij concurrerende `main` eerst vaststellen welke paden de andere agent wijzigde; restack met behoud van werk en nieuwe exact-head CI. Tests mogen niet losstaande aantallen introduceren die automatisch verouderen. Geen omzeiling van release-/CI-poorten, geen tweede autoriteit.
