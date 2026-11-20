# #520 — Verzegelde, eenmalige Incus-ACL-intrekking (broncontract)

## Reikwijdte

Deze code is **uitsluitend een GitHub-bronkandidaat**. Ze installeert of
activeert **geen** privileged helper, sudoers-regel, service, timer, worker,
Incus-ACL of extra authenticatielaag. Het is geen generieke root-shell en kan
niet via de gewone Runner-MCP-toolcatalogus worden aangeroepen.

Het bestand scripts/incus_acl_cleanup_once.py gebruikt uitsluitend de
Python-standaardbibliotheek. Het importeert niets uit de Runner-MCP-installatie
of een door de worker beschrijfbare venv. Het accepteert exact **nul**
CLI-argumenten. Eén bij installatie door de operator verzegeld root-eigen
beleid op een vaste plaats bevat de private host-, socket- en gebruikersbinding.
Dit beleid is geen tweede inventaris: de identiteiten moeten exact overeenkomen
met de bestaande centrale AIfordable-topologie en **werkelijk** hostbewijs.

## Gesloten runtimecontract

- Een geattesteerde echte fysieke host, OS-root, executable onder volledig
  root-beheerde ouders, mode 0500 en checksum uit private root-owned
  installatiebinding zijn verplicht. Gebruik /usr/bin/python3 met -I en -S;
  nooit de service-venv of een onbetrouwbare systeem-PYTHONPATH.
- De private binding heeft mode 0600, één link en uitsluitend bekende velden:
  schema, vaste korte hostidentiteit, serviceaccountnaam/UID/primair GID,
  verwachte Incus-socket en socketgroep, digest van de geïnstalleerde bron.
  Caller-input, tokens, omgevingsvariabelen of MCP-velden kunnen die gegevens
  niet instellen. Geen tweede authenticatie- of privilegebeheersysteem.
- De socket en alle voorouders moeten root-beheerd zijn, zonder
  groeps-/wereldschrijfbare directories. Vereist zijn Unix-socket,
  root-eigenaar, exact verwacht GID, mode 0660, één link, en dezelfde
  socketgeneratie voor en na de operatie.
- De enige toegestane POSIX ACL is de gewone basis user::rw-, group::rw-,
  other::---, eventueel mask::rw- en hoogstens één tijdelijke named grant
  user:<verzegelde UID>:rw-. Extra users, groups, defaults, duplicaten
  of afwijkend masker => STOP **vóór elke ACL-wijziging**.
- Alleen in die toestand mag de vaste setfacl -b de uitsluitend toegestane
  tijdelijke grant en het achtergebleven masker verwijderen; deze
  helper heeft geen grant- of serviceactivatiehandeling.
- Daarna onafhankelijke readback: exact basis-ACL, identieke socketgeneratie
  en echte negatieve schrijfbevoegdheid als serviceaccount via runuser.
  Onbekend => STOP, nooit een verondersteld PASS.
- Een tweede aanroep na succesvol herstel is idempotent zonder wijziging.
  Na een onderbreking vereist hervatten opnieuw alle oorspronkelijke gates.

Een toekomstige MCP-route kan hoogstens een **onafhankelijk geïnstalleerde en
gekwalificeerde** vaste root-owned helper aanroepen; bij ontbrekende of
afwijkende generatie blijft privileged_helper_unavailable de uitkomst.
Deze bron-PR voegt GEEN zulke route toe. Voor een echte installatie moeten
vooraf doelhost, proces/venv/revisie, installatiedigest, root-custody,
opname in de bestaande herstelprocedure, negatieve toegangstests, exacte
ACL-baseline en een onafhankelijke operatorvrijgave worden geattesteerd.

## Tests en bewijsgrens

De module tests/test_incus_acl_cleanup_once.py gebruikt uitsluitend
**synthetische ACL's** en gesimuleerde procesaanroepen. Gedekt zijn normale
grant, al ontbrekende grant, achtergebleven masker, onbekende named
gebruiker/groep/default, verkeerde host/UID/socket/mode/inode, bronhash,
private binding, argumentinjectie, niet-geïsoleerde Python, mislukte
setfacl en ontoereikende negatieve toegang of readback.

Dit is GEEN fysieke root-test. De bestaande eerste RF999-campagne en het
geslaagde exacte ACL-herstel blijven als aparte canonieke bewijzen in
Runner-Fabric #999. AIfordable #227/#390, Q7, A7 en andere servers blijven
buiten de wijzigingen van deze bron-PR.


## 2026-11-20 — afzonderlijke host-root socketbrug (SOURCE ONLY, GEEN INSTALLATIE)

**Waarom:** fysieke #520-bewijzen tonen dat de user-systemd MCP-service host-UID 0
niet kan zien in de eigen user namespace en dat `NoNewPrivileges=1` blijft
gelden. De oude `sudo -n`-brug kan daarom niet veilig in-process werken.
De bestaande A7 systemd-root-actor is uitsluitend een vaste recovery-tick,
niet een geauthenticeerde Incus-actuator. Hergebruik zou A7-autoriteit onjuist
uitbreiden; er is géén bewezen geschikte bestaande host-root-aanroep.

**Gekozen minimale bronkandidaat:** één **systemd system** socket
`runner-mcp-incus-acl-revoke.socket` met `Accept=yes`, die per aanvraag
één kortlevend root-owned `runner-mcp-incus-acl-revoke@.service` start.
Dat is geen extra relay, scheduler, tunnel, algemene controller of
authenticatiedienst. De bronbestanden zijn templates, niet geïnstalleerd.

- De bestaande geauthenticeerde MCP-tool behoudt exact nul argumenten,
  dezelfde openbare resultaatschema's, bestaande audit en
  `normalActivationEnabled=false`. Er is geen `sudo`, root-owned stat
  of aanname over de overflow-UID in het userns-proces.
- De client verzendt uitsluitend een vaste protocollijn met 128 bits
  willekeurige *correlatie-ID*, geen autorisatietoken, pad, gebruiker, ACL,
  command of servicekeuze. De rootservice weigert elke andere structuur.
- De rootgrens gebruikt Linux `SO_PEERCRED`, geverifieerde oorspronkelijke
  user-unit/cgroup, exacte éne proces-PID en startgeneratie,
  `NoNewPrivileges=1` en de bestaande root-private host-/owner-policy.
  De geautoriseerde originele OS-principal is niet gelijk aan 'ieder
  systeemproces met dezelfde UID'. Extra peers/cgroup-processen worden
  geweigerd; voor UID-/procesgeneratiedrift nooit automatische fallback.
- De rootservice controleert in de **host** user namespace, root-owned
  bestandouders, exacte permissies en SHA-256 van de al geïnstalleerde
  helper vóór de vaste `python3 -I -S`-aanroep. Alleen die helper kan een
  ACL verwijderen en controleert zelf de Incus-socket/inode/ACL en negatief
  toegangsbewijs; nooit een ACL-grant.
- Een root-only, `0700` statusmap en `0600` fsync-ledger bewaken de
  correlation-ID. De nieuw aangemaakte ledger-mapvermelding wordt
  apart gefsynct; de eerste `PENDING` wordt vóór uitvoering duurzaam
  bewaard; na gevalideerde helperuitvoer krijgt ze `PASS` en pas dan
  komt de begrensde ACK. Exacte replay krijgt dezelfde ACK zonder tweede
  helperaanroep. Een cached PASS geldt uitsluitend voor dezelfde, opnieuw
  geverifieerde root-owned Incus-socketgeneratie en werkelijk afwezige
  uitgebreide POSIX-ACL; een latere grant/ACL-wijziging maakt de oude
  replay-ACK ongeldig. Een nieuwe unieke aanvraag mag de vaste helper
  opnieuw oproepen. Onderbroken/afwijkende status blijft `PENDING` en
  blokkeert nieuwe uitvoeringen tot onafhankelijk operatorherstel.
  Rootservice audit schrijft alleen vaste uitkomsten in bestaande journald;
  bestaande MCP-audit blijft onafhankelijk van de rootledger.
- Unit-sandbox: afzonderlijke root-owned service, `NoNewPrivileges=yes`,
  geen userns-verzwakking van MCP, alleen AF_UNIX, capability-set
  CAP_FOWNER/CAP_SETUID/CAP_SETGID voor bestaande helper en zijn
  negatieve-accountcheck, beschermd systeembestandssysteem en uitsluitend
  gespecificeerde schrijfgrenzen. **Of alle sandboxinstellingen de echte
  setfacl/runuser-proef toelaten is nog NIET fysiek bevestigd.**

**Bedreigingen/restrisico:** Een gekaapte oorspronkelijke MCP-server met
geldig peerproces kan de *enige* vaste ACL-intrekking aanvragen en daarmee
een lopende toegestane kwalificatie onderbreken; de helper kan nooit rechten
toekennen. Een ongeautoriseerd lokaal proces, verkeerde cgroup/PID,
vreemde host of gewijzigde helper moet DENY krijgen. Een proces dat het
oorspronkelijke user-unitproces of host-root volledig compromitteert, valt
buiten de bewijsclaim; de root-ACK is niet gelijk aan een onafhankelijke
off-host audit. Bewijs van bestaande menselijke hostpolicy is vereist vóór
actie. De procedure verleent geen generieke root-toegang.

**Gescheiden eigenaarstoestemmingen vóór fysieke wijziging:**

1. Nieuwe privileged installatie: **NIET GOEDGEKEURD**. Afzonderlijk
   eigenaarsbesluit vereist voor exact de root-owned bronscriptinstallatie,
   twee systemd-units, één vaste root-only ledger/state directory en het
   owner-gecontroleerde Unix-socketbestand. Kost: €0 extra; geen nieuwe
   softwarepakketten en geen wijzigingen aan A7/Incus-service/MCP-hardening.
   Eerst controle rootgrens, echte PID/poort/venv/release, unit-manager,
   onafhankelijke terugzetmogelijkheid en root-owned SHA vooraf.
2. Na goedgekeurde installatie: synthetische test en geïsoleerde
   socket-canary; één authenticated originele MCP no-op en onafhankelijke
   basis-ACL/negatieve owner-access/audit/ACK. **Geen ACL grant.**
3. Een echte tijdelijk toegestane named ACL grant + revoke met zes
   beschermde gasten onveranderd vereist **een tweede, aparte expliciete
   eigenaarstoestemming**. Test denial/replay, unitrestart, onderbreking,
   incidentreconciliatie en rollback met onafhankelijke readback.

**Rollback bij een installatie:** maak eerst onafhankelijke, byte-identieke
kopieën van exact bestaande systemd/rollback-, policy- en ACL-toestand.
Bij fouten: stop/disable uitsluitend de nieuwe socket en de nieuwe
eenmalige executor, herleid de MCP-tool fail-closed; laat rootledger,
bestaande root-helper, originele user-service, A7 timer en Incus/socket
onaangeroerd voor forensiek. Indien MCP-code al apart is geactiveerd:
gebruik uitsluitend de werkelijk gepinde vorige release en originele
same-unit rollback, met health/PID/poort/NNP readback. Geen brede
systemd/cron-/ACL-restore of automatische root-ledgeropschoning.

**Niet bewezen door deze bron:** goedkeuring, installatie, werkende socket
met huidig userns, werkelijk root-ACL-no-op, toegestane grant/revoke,
crashherstel, host-herstart, audit/ACK vanuit de oorspronkelijke MCP-client.
#520 blijft OPEN tot **alle** acceptatiecriteria in canoniek issuecommentaar
7044318943 feitelijk PASS zijn. Geen duplicaat van AIfordable-topology.
