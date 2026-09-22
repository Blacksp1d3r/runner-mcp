# Snelle, laag-risico verbeteringen

Een samengevatte lijst van de concrete punten uit de andere bestanden in
deze map die het meeste effect leveren voor de minste moeite/risico. Elke
regel verwijst naar het bestand met de volledige uitleg.

| # | Voorstel | Effect | Risico | Detail |
| --- | --- | --- | --- | --- |
| 1 | CI-statusbadge toevoegen aan README.md | Direct zichtbaar vertrouwenssignaal | Vrijwel nul | [DOCS.md](DOCS.md) §3 |
| 2 | `needs: validate` toevoegen aan de `demo-smoke`- en `release-artifact`-CI-jobs | Bespaart CI-tijd bij rode commits | Vrijwel nul | [TESTING_CI.md](TESTING_CI.md) §1 |
| 3 | Eén regel "Implements roadmap Phase X.Y" bovenaan elk `docs/*.md` | Navigatie tussen roadmap en detaildocs in beide richtingen | Vrijwel nul | [DOCS.md](DOCS.md) §5 |
| 4 | Statustabel (fase/status/link) bovenaan `roadmap/ROADMAP.md` | Roadmap in 10 seconden scanbaar i.p.v. 10 minuten | Vrijwel nul | [ROADMAP.md](ROADMAP.md) |
| 5 | Eén verwijzende zin: welk document leidend is bij afwijkende cijfers (roadmap vs. handover) | Voorkomt toekomstige verwarring | Vrijwel nul | [ROADMAP.md](ROADMAP.md), [DOCS.md](DOCS.md) §1-2 |
| 6 | Gedeelde `_confirm(expected)`-helper in `cli.py` i.p.v. 6x gekopieerde bevestigingslogica | Consistentie, minder duplicatie | Laag (mechanisch) | [CODE.md](CODE.md) §4 |
| 7 | Gedeelde `atomic_write_private()`-helper (`secure_io.py`) i.p.v. 8x losse implementatie | Eén plek om een toekomstige bugfix toe te passen | Laag (mechanisch, gedrag ongewijzigd) | [CODE.md](CODE.md) §8 |
| 8 | Basale `logging` voor watcher-lifecycle (start/stop/cyclus/fout) | Operationele debugbaarheid zonder gevoelige data te lekken | Laag | [CODE.md](CODE.md) §6 |
| 9 | `install.sh`: controleer `python3 -m venv` vooraf, geef duidelijke melding | Betere foutmelding op minimale images | Vrijwel nul | [CODE.md](CODE.md) §12 |
| 10 | Inline commentaar + extra velden in `config/projects.example.yml` | Nieuwe gebruikers snappen het voorbeeld sneller | Vrijwel nul | [CODE.md](CODE.md) §13 |
| 11 | Eigen klein testbestand voor `audit.py` | Fundamentele module krijgt directe, snelle dekking | Vrijwel nul | [CODE.md](CODE.md) §11 |
| 12 | Halve zin in README bij `install-operator.sh`: "sla over bij single-account-gebruik" | Voorkomt onnodige verwarring bij de meerderheid van lezers | Vrijwel nul | [UX.md](UX.md) §6 |

Grotere, waardevollere maar risicovollere refactors (het opsplitsen van
`server.py`/`cli.py`, een `audited_tool`-decorator, een pluggable
adapter-registry) staan in [CODE.md](CODE.md) met hun eigen afweging —
bewust niet in deze "quick wins"-tabel omdat ze meer overleg en testwerk
vragen dan een quick win rechtvaardigt.
