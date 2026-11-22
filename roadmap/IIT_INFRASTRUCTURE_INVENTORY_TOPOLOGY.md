# IIT — Infrastructure Inventory & Topology (Runner-MCP)

Status: ROADMAP / operatorbesluit 2026-11-22; geen live installatie- of wijzigingsautorisatie.
Hoofdeigenaar: Runner-MCP / bestaande Verified Fleet Facts P1 (#950).
Integratiehouder: Runner-Fabric Verified Fleet Facts (#2062), met **VFS-V1 #2084 als enige eerste actieve end-to-end slice**.
Verwante autoriteit: AIfordable infrastructure authority (#428), canonical fact envelope (#819).
Horizon: eigen machines nu; ontwerp geschikt voor 100–1.000+ hosts en 100+ AI-sessies later.
Deze publieke roadmap bevat uitsluitend architectuur en synthetische voorbeelden. Operationele host-/klantdetails blijven in de bestaande private owner-authority.

## 1. Bindend eigenaarsbesluit

Eén AI-opvraagbare actuele infrastructuurinventaris, **zonder afhankelijkheid van chatgeheugen**.
Elke AI (ChatGPT, Claude, Qwen) vraagt via dezelfde begrensde Runner-MCP-toegang het bestaande facts-overzicht op. Niet telkens zelf alle hosts opnieuw scannen.

- Runner-MCP owns platform-adapters, lokale read-only inventarisatie en MCP-readtools.
- Linux-inventarisatie loopt via een bestaande Runner-MCP-agent en **systemd oneshot/timer**; geen extra permanente monitoringdaemon.
- De **bestaande** Agent Bus/uitgaande controleverbinding is het beoogde transport. Klantservers openen geen inkomende beheerpoort.
- AIfordable owns stabiele asset-/klant-/site-ID's, parent-relaties en declaratieve gewenste toestand. Runner-Fabric owns read-cache, vergelijking, impact en toekomstig operatorgestuurd updatebeheer.
- De operator wil **machineleesbare JSON op de eigen private Git** als canonieke, duurzaam versiebeheerde inventarisweergave en wijzigingshistoriek. Geen NetBox, osquery, Ansible, nieuwe centrale database, betaald SaaS, nieuwe tunnel, tweede scheduler, tweede agent-bus of parallelle registry.
- Bestaande AIfordable YAML registry en Fabric infrastructure-topology/v1 zijn al autoriteit/consumers. **Niet parallel twee schrijfauthorities maken**: het bestaande YAML-register blijft de enige declaration-writer totdat een aparte, bewezen en expliciet goedgekeurde migratie naar JSON is voltooid. In de tussentijd ontstaat JSON uitsluitend als gevalideerde projectie van bestaande declaraties plus onafhankelijke observations.
- Git bevat **niet iedere heartbeat** en is niet de lage-latentie operationele cache. Gebruik de reeds geplande/aanwezige F10 latest-facts projection voor snelle reads; JSON in private Git bewaart semantische gewijzigde declaraties, snapshots, en beperkte bewijsverwijzingen.
- Geen installatie of upgrade, **ook niet op testsystemen**, zonder de voorafgaande expliciete eigenaarstoestemming. Alleen-lezen inspectie en source-only code/CI/roadmap mogen afzonderlijk voorbereid worden. Niet zelfstandig opruimen, unit installeren/activeren, rebooten of productie wijzigen.
- Prioriteit: **een werkend eind-tot-eind resultaat**; optionele toekomstige beveiligingsuitbreidingen pas daarna. Bestaande noodzakelijke autoriteits-/identiteitsgrenzen behouden.

## 2. Bestaand werk — HERGEBRUIKEN, niet dupliceren

| Bestaande bron | Gebruik / grens |
| --- | --- |
| Runner-MCP #489, #950, #951 | Platformneutrale bounded adaptergrens; geen tweede framework |
| Runner-MCP #952 | Minimale Linux-lezer voor OS, boot, process, systemd, sockets, werkelijk geladen artifact |
| Runner-MCP #953 | Windows SCM/CIM/Hyper-V/TCP-owner reader; geen Linux-aannames |
| Runner-MCP #954 | macOS uitsluitend contract/HOLD zonder echte host |
| Runner-MCP #665/#669 | Tool-schema, bronrevisie, actieve build-provenance; onbekende digest is geen geverifieerde versie |
| Runner-MCP bestaande tunnel_topology_heartbeat | Bestaande primaire tunnel-identiteit/autoriteit; **geen** volledige fleet-package/servicecollector |
| Runner-MCP #866 | Bestaande systemd-rolmigratie; geen tweede autostartlaag |
| Runner-Fabric #2062 / #2084 | Facts-integratie en minimale eerste echte host→cache→get_facts-acceptatie |
| Runner-Fabric #2071 / #2068 / F10 | Geauthenticeerde ingest, gedeelde vluchtige projectie, read-only get_facts |
| Runner-Fabric infrastructure-topology/v1 | Canonieke bestaande node-/edgebindings; compatibel behouden |
| AIfordable #428/#819 | Asset IDs, parent/tenant scope, gewenst register, OS-neutraal fact-envelope |
| Runner-Fabric #924 / Runner-MCP #341 | Bestaande updater, dependencyimpact, recovery; geen nieuwe updater |
| I7 / bestaande private Git-provider | Doel voor private JSON-commits; eerst exacte actieve bron-, integriteits- en herstelstatus kwalificeren |

De huidige Runner-MCP-connector of GitHub-bronversie zegt op zichzelf niet welke software op een specifieke fysieke host werkelijk geladen is. Vóór claims: exacte host + proces-generatie + bron/evidence verifiëren. Reeds bestaande JSON- en YAML-identiteiten niet hernummeren.

## 3. Eén logisch inventarisregister; drie gescheiden toestandslagen

1. **Declared / expected:** door AIfordable beheerde host-, VM-, service-, klant-, site- en verbindingsrelaties; gewenste softwareversie en toegelaten functie. Alleen declaratieve wijzigingen via eigenaar/goedgekeurde route.
2. **Observed:** door de juiste geregistreerde host zelf gemeten actieve toestand: OS, kernel, hardware, capaciteit, geïnstalleerde pakketten, service status, geladen artifact, processen, listeners, netwerkwaarnemingen. Met bron, boot/generation, timestamp/TTL en confidence. Host-selfreport = OBSERVED, niet automatisch VERIFIED.
3. **Verified:** afzonderlijk bevoegde control-path/readback/handshake/witnessbewijs voor de betreffende claim. Een TCP-socket, HTTP 200, hostname, Git revision of host-eigen handtekening alleen is nooit algemeen bewijs van de geladen code of end-to-end werking.

Mogelijke statussen: DECLARED, OBSERVED, VERIFIED, STALE, CONFLICT, UNKNOWN, UNSUPPORTED, UNREACHABLE en RECONCILE_REQUIRED. Scope-specifieke betekenis, bron, evidence-referentie en verificatietijdstip blijven zichtbaar. Bij offline cacheverlies geen onterechte groenstatus.

### Logische private JSON-layout (illustratief, geen aanmaakbesluit)

~~~text
infra/
  topology.json            # alleen-lezen projectie van huidige declaratieve autoriteit
  observations/
    <asset-id>.json         # laatst vastgelegde feitensnapshot, niet de live heartbeat
  index.json               # gegenereerde compacte samenvatting voor index/AI
  changes/
    ...                    # semantische configuratiewijzigingen, geen periodieke heartbeatcommits
~~~

Geen klantgegevens, private coördinaten, credentials, host-private paden, procesargumenten of grote ruwe eventlogs in **publieke** repositories of AI-antwoorden. De **eigen Git** voor operationele inventaris is privé, met scoped toegang. Alleen benodigde metadata en veilige bewijsreferenties opnemen.

### Illustratief, synthetisch observation-envelope

~~~json
{
  "schema_version": "infra/observation/v1",
  "asset_id": "asset:example-001",
  "service_id": "service:example-001",
  "field": "runtime.version",
  "value": null,
  "status": "UNKNOWN",
  "source": "runner-mcp/local-readonly",
  "boot_generation": null,
  "observed_at": null,
  "received_at": null,
  "ttl_seconds": 900,
  "authority_revision": null,
  "evidence_ref": null
}
~~~

Dit is enkel een **view-/serialisatievoorbeeld**. Het echte wire-contract wordt hergebruikt van AIfordable #819 en Fabric #2084, niet opnieuw als concurrerende envelop bedacht. Null betekent niet gecontroleerd, niet nul of bewezen afwezig.

## 4. Feiten die de bestaande native collector moet kunnen tonen

- Identiteit: stabiele asset-ID, parent fysieke host / VM / container, klant/site/omgeving, platform, boot- of instance-generatie; geen identificatie uitsluitend uit hostname of IP.
- OS: distributie/build, kernel, CPU-architectuur, cores, RAM, schijven/filesystems/inodes, vrije capaciteit en hardwarecompatibiliteit.
- Software: pakketnaam, installed version, **running/loaded version**, desired version **apart**, bronrevisie/digest alleen als bewezen, gebruikte runtime en functie/servicerol.
- Uitvoering: systemd-unit-scope/eigenaar/ActiveState/MainPID/startticks op Linux; SCM/Windows-processen op Windows; afzonderlijke guest/container namespace.
- Netwerk: poort/protocol, lokaal bindadres/namespace, luisterproces en actuele connecties; logisch expected edge apart van gemeten socket en onafhankelijke peer-verificatie.
- Gebruiksdoel: owner-keurige korte beschrijving waarom een softwarecomponent bestaat; vermoedelijk ongebruikt/oud altijd eerst als candidate, nooit op basis van naam/versie automatisch verwijderen.
- Wijzigingen: last observed / received / verified, versie-/proces-/bootgeneratieverschillen, geteste compatibiliteit, reden en bewijsverwijzing.

Procesverbindingen zijn vluchtig: een ontbrekende TCP-sessie betekent **niet** dat de declared afhankelijkheid is verwijderd. nftables/conntrack mogen op Linux optionele waarnemingsbronnen zijn wanneer reeds beschikbaar, **niet** verplicht op iedere Linux-host en nooit als Windows-API.

## 5. Windows Worker en geneste VM's

- De fysieke Windows-host heeft geen systemd, Linux procfs, nftables of conntrack. Gebruik de bestaande Runner-MCP Windows adapter (#953), native SCM/CIM en Get-NetTCPConnection / Windows API's voor momentopnames.
- **Microsoft Sysmon Event ID 3** kan later processen en historische netwerkconnecties aanvullen. Sysmon is optioneel, niet inbegrepen/actief veronderstellen; Event ID 3 moet expliciet aangezet/geconfigureerd worden en kan veel events produceren. **Sysmon installeren/activeren vereist apart expliciet eigenaarsakkoord.** Zonder toestemming native Windows read-only facts en expliciet beperkte geschiedenis.
- Windows planning via bestaande Windows Task Scheduler of reeds aanwezige toegestane Windows servicevoorziening, pas na expliciete install-/activeringstoestemming. Geen systemd op de Windows-host en geen nieuwe Windows-agent enkel om het schema te vullen.
- Linux-VM's op een Windows Hyper-V-host worden met de Linux systemd-benadering verzameld; de fysieke Windows-host, zijn Hyper-V VM's, Incus guests en containers zijn **verschillende assets** met parent-child-relaties. Geen verwarring op basis van servicenaam.
- macOS blijft HOLD totdat een echte behoefte bestaat (#954).

## 6. Bestaande uitgaande transportketen en timing

- Hergebruik de huidige Runner-MCP / Agent Bus-route; geen nieuwe inkomende klantpoorten, aparte SSH-poller, SQL-relay of externe SaaS.
- De bestaande snelle topology-heartbeat blijft een controle voor tunnel/binding. **Overlaad die niet** met volledig software-inventarisbeheer en verhoog zijn frequentie niet om package listing mogelijk te maken.
- Beoogde cadence na bewezen éénhostpilot: status, capaciteit, systemd en listeners ongeveer elke 15 minuten via begrensde, gespreide systemd oneshot timer; software-/pakketversies dagelijks; gerichte refresh na eigen deployment/reboot als reeds veilig beschikbaar. Frequenties zijn configureerbare beleidsvoorstellen, geen nu te activeren timers.
- Verzending met host- en bootgeneratie, sequence, observed_at/received_at, digest, omvanglimieten; idempotent, replay/out-of-order veilig en offline buffer/reconcile **via bestaande Agent Bus-capaciteit** voor zover geverifieerd. Niet blind aannemen dat de huidige relay elke benodigde operatie al ondersteunt; bewijs eerst werkelijke write→ACK.
- De centrale **bestaande** F10 latest-view cache dient informatieve reads zonder hostscan. Cacheverlies veroorzaakt STALE/UNKNOWN en maximaal één gerichte refresh (single-flight), niet een full fleet scan.
- Eigen private Git bevat declaratieve wijzigingen en compacte snapshots in batches; alleen relevant verschilde feiten committen, nooit elke 10-secondenheartbeat en nooit 96.000 commits/dag. Git is duurzaam naslagwerk, geen realtime message queue.
- Eén aangewezen writer/projector per declaratieve of snapshotcategorie; geen conflicterende per-host Gitwriters.

## 7. UI en MCP-readinterface

Eerste gebruikerwaarde: meerdere chats/sessies stellen dezelfde vraag en krijgen identieke actuele feiten + bron + tijd zonder nieuwe hostinspects.

Hergebruik eerst de get_facts-API van Fabric #2068 via Runner-MCP; geen duplicaat met andere semantiek. Eventuele dunne MCP-aliases alleen wanneer ze echte gebruikswaarde bewijzen:
- infra_overview: compacte filters/totalen en stale/attention per scope.
- infra_get: één host/service/edge inclusief geïnstalleerd/actief/gewenst.
- infra_diff: declared versus observed, of betekenisvolle verschillen tussen twee waarnemingen.
Later optioneel: impact van service/verbinding en verouderde componenten via **bestaande** Fabric-vorming en Fleet Update Plane. Bounded filtering en paginatie; nooit standaard alle ruwe 1.000-hostreports in één AI-context.

Na een geslaagde facts-pilot: projectagent-instructie toevoegen dat actuele versies/hostbindings **eerst** via Runner-MCP/get_facts worden gelezen in plaats van uit chatgeheugen afgeleid. Zolang API niet werkt, geen fictief werkende tool in AGENTS.md beloven.

## 8. Schaalontwerp: 1.000 hosts / 100+ AI-sessies

- Vaste asset-ID, tenant scope, shard per host/scope, schema + versiecompatibiliteit.
- Gejitterde systemd-timers, event-delta's, begrensde payload/queue, backpressure, batch-Gitcommits en verandering op semantische keys.
- 1.000 hosts bij 15-minutenperiodiciteit = 96.000 observaties/dag; **niet** gelijk aan 96.000 Gitcommits.
- Ingest/dedup en cache single-flight: 100 identieke fact-reads veroorzaken 0 extra hostscans zolang geldig; bij TTL-verval maximaal één gedeelde refresh per key.
- Verdeel het eigenaarschap van customer/sites, host-identity, instances en servicegeneraties; één defecte host blokkeert andere hosts niet.
- Ontwerp dit nu, implementeer pas later de schaal-infrastructuur nadat de éénhostpilot waarde en prestatieverbetering bewezen heeft (Fabric #2084).
- Uitbreiding via 1 echte host → 10 → 100 → 1.000 **gesimuleerde** hosts voor throughput, geheugen, Git-groei, reconnect en queue-verlies; 1.000 echte hosts zijn niet geclaimd of vereist voor V1.

## 9. Verband met selectieve updates (LATER)

Dit inventarisregister is input voor bestaande Fleet Update Plane (Fabric #924, Runner-MCP #341) en Fabric Cockpit F17: beheerder kiest op verzoek expliciet managed programma, runner of component/verbinding, doelversie en doelen. **Geen automatische of periodieke software-installatie.**

- Eigen machines kunnen na operatorselectie kandidaat zijn; later per tenant/abonnement/product-release selecteren (premium features zijn niet altijd nieuwe binaries).
- Voor iedere doelserver: CPU/architectuur, memory, diskruimte/inodes, staging/rollbackmarge, afhankelijkheden, geïnstalleerde vs geladen bron, data-/config-/schemacompatibiliteit en herstelroute verifiëren.
- Na expliciet toegestane update: echte functie- en gegevenscontrole; daarna alleen werkelijk overbodige releases, downloads en tijdelijke artefacten opruimen of veilig in bestaande goedgekeurde opslag bewaren. Minimaal benodigde rollbackgegevens behouden; geen nieuwe automatische back-upcyclus.
- Runtime-facts zijn **geen** mutatieautorisatie: relevante operationele update- en recoverygates blijven apart.

## 10. Afwerkvolgorde — zonder nieuw werk naast bestaande werkstromen

**S0 — Reconciliatie (read-only, eerste handeling):** controleer bestaande issues #950–#953, #489, #669, Fabric #2084/#2062/#2071/#2068, AF #428/#819, huidige branches/PRs, topology JSON en private Git / I7-gezondheid. Reuse bestaande data- en API-contracten; rapporteer ontbrekende schakel met exacte code-eigenaar. Geen duplicaat-epic, geen tweede Gitserver.

**S1 — Minimum schema en Linux reader (source-only):** #951 slechts de noodzakelijke fields; #952 slechts één bestaande geregistreerde Linux host en één service. Echte runtime-versie alleen wanneer loaded artifact/owner bewezen; UNKNOWN anders. Tests voor bootwissel, PID-hergebruik, namespace, missende service, fout schema en ontbrekende bevoegdheid.

**S2 — Eén werkende end-to-end keten:** juiste host → Runner-MCP → bestaande uitgaande/Agent Bus route → Fabric ingest/latest-view (#2071) → get_facts (#2068) → twee onafhankelijke AI-reads met hetzelfde timestamp/revision; tweede read 0 extra hostscans. Meet eerst bestaande tijd/call baseline en daarna winst. Geen verplichte Git- of Sysmon-activatie om read-only proof te halen.

**S3 — Private Git JSON aansluiting:** pas na de juiste eigen Git-provider en herstel/availability read-only gekwalificeerd zijn; valideer één declaration→JSON projectie, één echte geverifieerde snapshotswijziging, idempotente batchcommit, dedup en herstel na herstart zonder writes naar publieke GitHub hostdata. De private Git-repo blijft uitwisselbare source provider; geen verplicht vastpinnen van runtime op een specifieke Git-webimplementatie.

**S4 — Extra Linux-hosts en Windows:** één volgende echte Linux-host; daarna Windows-native #953 en eigen Hyper-V-guest relaties. Sysmon als afzonderlijke optionele vervolgstap na expliciete installatie-/activeringsgoedkeuring. Geen uitrol naar alle machines voordat elke vorige stap end-to-end bewezen is.

**S5 — Drift, serviceimpact en schaal:** eenvoudige observed-vs-declared-vs-verified diff via bestaand Fabric, filterbare MCP-reads; daarna synthetische 10/100/1000-host lastproeven en pas dan verdere schaaluitbouw. Later F17 operatorbeeld en vraaggestuurde updates via bestaand werk.

## 11. Minimale acceptatie / STOP-criteria

- Eén echte host/service levert een geldig, privacyveilig fact met identiteits-, versiegeneratie-, tijd-/TTL- en bronlabel aan de bestaande centrale projectie.
- Eén AI leest hetzelfde fact tweemaal / twee chats zonder tweede hostscan; stale/offline/tegenstrijdig wordt nooit groen of VERIFIED.
- Een daadwerkelijke reboot of service-update maakt alleen de relevante fact(s) stale en laat de nieuwe geverifieerde procesgeneratie terugkomen.
- Eén betekenisvolle wijziging komt exact éénmaal in de bestaande private JSON/Git-view, zonder logspam, verlies van data of conflict met YAML-authority; enkel wanneer S3 uitgevoerd is.
- Windows host/Hyper-V parent-VM-relatie is juist; Sysmon vereist niet om baseline Windows facts te tonen.
- Geen update, installatie, service-activatie, globale scanner, netwerkopening, periodieke back-up of verwijdering door deze roadmap. Daarvoor altijd afzonderlijke expliciete eigenaarstoestemming.
- Exacte issues, commit/test-evidence en blokkade terugmelden; geen DONE claim op alleen PR-merge of synthetische test.

## 12. Overdracht aan uitvoerende chat

Start bij **Runner-MCP #950** en **Fabric VFS-V1 #2084**; controleer eerst actuele branch-/issueclaims en bestaande bron. Lever een hergebruikmatrix met ontbrekende E2E-schakel. Begin uitsluitend met S0 en daarna kleinste veilige source-only S1/S2. Niet meteen 1.000-host infrastructuur, Windows Sysmon of private Git deploy bouwen. Nooit installaties of upgrades zonder aparte expliciete eigenaarstoestemming. Update bestaande eigenaar-issues en maak korte, testbare PR's, met echte status en evidence.

**Roadmapbesluit = plan, niet operationele activering.**
