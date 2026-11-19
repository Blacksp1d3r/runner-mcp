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
