# RMCP F30 — Local-bundles TOCTOU bij laatste directorypromotie (2026-11-06)

## Context en risico

De bestaande `FabricUpdateManager.stage_local_bundle(exact_commit)` bouwt al een
gecontroleerde Fabric-bundel in de **inactieve**, bestaande eigenaar-private
`local-bundles/.incoming-<uuid>/source/bundle`. De functie keek eerst of de
doelmap `local-bundles/<exact commit>` bestond en promoveerde de bundel later
met `os.replace(bundle, target)`. Dat was een *time-of-check/time-of-use*
(TOCTOU): twee makers konden dezelfde `target.exists()==False` zien. Bij
een nieuw, inmiddels bestaande **lege** doelmap kan een directory-replace
de andere maker verdringen. Dat is onacceptabel voor reproduceerbare immutable
release-custody en onafhankelijk rollback-bewijs.

Geen bekende productie-overschrijving bewezen; dit is een brononderzoek en
een synthetisch geteste risicoklasse, **geen** claim van een live incident.

## Oorzaak, herstel en hergebruikt onderdeel

- De losse voorafgaande `target.exists()` is alleen een informatieve hint,
  nooit de beslissende exclusiviteitscontrole.
- Runner-MCP had reeds een Linux
  `renameat2(RENAME_NOREPLACE)`-primitive in
  `fabric_release_private_custody._promote_noreplace` voor historische Q7.
- [Runner-MCP PR #942](https://github.com/Blacksp1d3r/runner-mcp/pull/942),
  bron 0.1.141, heeft diezelfde primitive hergebruikt in de bestaande manager.
  Alleen een geldige `.incoming-<32 lowercase hex>/source/bundle` onder de
  gecontroleerde private `local-bundles`-root kan naar exact de 40-hex commit
  promoveren. `root` en `incoming` zijn eigenaar-privé 0700; de afzonderlijk
  met `O_NOFOLLOW` geopende `source` en `bundle` mogen het normale Git-mode
  0755 hebben, **niet** groeps- of wereldbeschrijfbaar zijn. Er is geen
  install-, token-, daemon- of alternatieve updaterroute gemaakt.
- Een gelijktijdige doelmap wordt nu **atomair geweigerd** en niet overschreven.
  De bestaande actieve `bundle/`, `slots/` en `transaction.json` blijven
  onafhankelijk.

## Tests en gedocumenteerde regressie

- Eerste exacte-head CI voor de PR had **1 falende bestaande integratietest**
  tegenover **4.579 geslaagde tests**: een gedisposeerde Git-clone creëert
  `source` normaal met 0755, terwijl de eerste patch onnodig 0700 vereiste.
  Dit was een nieuwe compatibiliteitsregressie, geen werkelijke storing van
  Qwen/Claude/Fabric.
- Gerichte correctie: privé-ouder `incoming` vereist 0700, lagere
  Git-mappen hebben dezelfde eigenaar en mogen nooit door anderen beschrijfbaar
  zijn; 0755 is toegelaten. Nieuwe positieve test controleert precies 0755.
- Finale exacte-head CI van broncommit
  `d57e12c480dcc5edf83677268ec1ca95e3edc4df`:
  Runner MCP validation
  [#42221040779](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42221040779)
  **SUCCESS**, Clean Ubuntu
  [#42221041071](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42221041071)
  **SUCCESS**, attribution
  [#42221041052](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42221041052)
  **SUCCESS**. De volledige suite, packaging, release reservation, disposable
  real systemd en einddemo slaagden. Squash merge
  `ebe687b75c1ed7a2979966a43e0fb7e3a97c032f`.
- Positieve en negatieve scenario's in
  `tests/test_fabric_update_local_noreplace.py`: eerste stage,
  normale Git-modes, lege/gelijktijdig aangemaakte doelmap,
  dubbele commit, symlinks op elk tussenpad, onveilige schrijfpermissies,
  partiële stage en behoud van eerdere actieve en herstelbestanden.

## Herhaling voorkomen

Gebruik bij immutable bundle-promotie een **atomaire NOREPLACE-operatie op
pinned owner-private directory descriptors**, nooit alleen
`if not exists: os.replace`. Geef `source`/Git-werkmappen niet
ondoordacht 0700 als de bestaande Git-interface veilig 0755 aanmaakt:
private ouder en schrijfpermissies zijn de werkelijke eigenschap.

Deze bronwijziging is geen originele hostattestatie. Ze herstelt niet
automatisch ontbrekende generieke Fabric-releaseondertekening, exacte
serving-wheel identiteit #669, #341 lokaal herstel, Fabric A6 #942 / A7 #943
of originele client-result+ACK. Qwen V3 en Claude hebben hun eigen werkstromen,
geen server of dienst werd in deze sessie gewijzigd.

## Operationele toolblokkering (afzonderlijk)

Tijdens de bron-PR werd een batch voor documentupdates door de platform-
veiligheidscontrole gestopt; de letterlijke geredigeerde fout en readback zijn
duurzaam in de PR-beschrijving opgenomen onder `TOOL_BLOCK_V1`. De geweigerde
`handover/SESSION_HANDOFF.md`-update is niet opnieuw via een ander transport
uitgevoerd. Dit Failure Museum is een **ander, nieuw onderbouwd technisch
dossier** in het reeds bestaande projectgeheugen, niet een omweg voor die
weigering.
