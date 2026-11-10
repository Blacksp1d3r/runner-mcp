## 0.1.158 — #669 ZIP en SHA256 van originele wheel aan één inode binden (SOURCE MERGED/CI PASS, LIVE WAIT)

- De al bestaande private originele-wheelcapture las ZIP-leden en volledige wheel-SHA via twee aparte path-opens. Als een wheel ertussen wordt vervangen door een wheel met dezelfde Python-modulebytes maar andere metadata, kon de ontvangstkopie een verkeerde gecombineerde originele SHA/moduleverklaring bewaren.
- De bestaande helper gebruikt nu een enkele `O_NOFOLLOW`-descriptor, controleert stat/inode/generatie vóór en na beide lezingen, en weigert vervangen/gewijzigde wheelbytes zonder receipt. Eén negatieve swap-injectie bewaart ook de oorspronkelijke create-once-, 0600- en fsync-contracten. Geen nieuwe opslag, signing of updater.
- Dit is uitsluitend SOURCE/CI-acceptatie. Originele fysiek bewaarde 0.1.88-wheel en 3.614-file A7-runtime-restore niet herhalen; actuele live geladen wheel/source en formele A7 zesrollen/campagne-ACK blijven open.

---

## 0.1.157 — #341 originele hersteltransactie met gedeelde owner-lock en jobgebonden cleanup (BRONKANDIDAAT)

- **Concrete oorzaak:** na de eerder gemergede atomische publicatie met `os.link` kon `clear_transaction()` nog een inmiddels door een andere job gepubliceerde hersteltransactie verwijderen. Een controle op pathname of inode gevolgd door `unlink` is geen atomaire compare-and-delete.
- **Beperkte correctie:** de **bestaande** owner-private `self-update-install-transaction.json` blijft de enige herstelbron. BEGIN én CLEAR houden nu dezelfde Linux `flock` op een blijvend 0600-bestand naast die bestaande transactie vast. Foutieve eigenaar/permissies/symlink/hardlink, ontbrekende lock of concurrente houder = STOP zonder lockvrije fallback. Crash/procesverlies laat de kernel-lock los; geen tweede updater, scheduler, relay of controller.
- **Job-identiteit:** CLEAR heeft een verplichte exacte 32-hex job-ID; een oude afsluiter weigert een nieuwe/andere transactie en bewaart de bytes. Drie bestaande `SelfUpdateManager`-afsluiters geven uitsluitend hun oorspronkelijke job-ID door. Nieuwe tests: vreemde job, twee afsluiters/nieuwe generatie, exclusieve BEGIN/CLEAR, alias of vreemde permissies, ontbrekende kernel-lock, ongeldige job-ID en automatische lockvrijgave na procesexit. Bestaande baseline- en herstelcontracten blijven gelden.
- **Grenzen:** alleen bron/CI, géén automatische inzet op de oorspronkelijke `github-runner`, Black/A6/A7, Claude, Qwen of SQL. Originele live wheel #669, A6 off-target journal #942, A7 offline rollback #943 en echte updatecampagne-ACK blijven afzonderlijk open.

## 0.1.155 — #341 hersteltransactie atomair zonder overschrijven (BRONKANDIDAAT)

- Bestaande `SelfUpdatePackageInstaller.begin_transaction` controleerde eerst een afwezige hersteltransactie, maar publiceerde daarna via `os.replace`. Twee concurrerende installateurs konden daardoor een na die controle verschenen originele transactie vervangen en de juiste terugvalbasis verliezen.
- De bestaande `self-update-install-transaction.json` wordt nu via `os.link(..., follow_symlinks=False)` atomair en zonder overschrijven gepubliceerd, gevolgd door verwijdering van uitsluitend de eigen tijdelijke naam en de bestaande directory-`fsync`. Bij conflict of ontbrekende hardlinkondersteuning weigert de installer; geen onveilig `os.replace`-alternatief.
- Twee gerichte regressietests houden een door een tweede updater gepubliceerde geldige transactie byte-identiek en weigeren de publicatie bij ontbrekende atomaire ondersteuning. Alle bestaande transactiepaden en rollback-/safetycontracten behouden. Alleen bron en test; geen nieuwe updater, controller, dienst, hostinstallatie, A7-proef, Ed25519-sleutel of Claude/Qwen-wijziging. Volledige CI/merge en fysiek bewijs blijven afzonderlijke poorten.

## 0.1.154 — #662 kandidaatartifact pas na volledige bestaande demo en systemd-test (BRONKANDIDAAT)

- De reeds bestaande main-release-`release-artifact` job had alleen `needs: validate`. Bij v0.1.152 was het immutable source-artifact al geüpload terwijl de vijfminutendemo later CANCELLED werd; kandidaat ≠ volledige CI-groen. Dezelfde bestaande job krijgt nu `needs: [validate, demo-smoke, disposable-systemd-user]`. Geen nieuwe workflow, runner, uploader, cache, CI-control-plane of artifactopslag.
- Bestaande workflow-test borgt dat echte demo en disposable systemd aan de artifactjob voorafgaan. Version/discovery kandidaat 0.1.154 in vier bestanden. **Exact-head CI en merge nog vereist.** Externe attribution/clean Ubuntu, fysieke owner/host/wheel #669 en A6/A7/ACK blijven afzonderlijke bewijspoorten; geen live update.

## 0.1.153 — #662 actieve main-release CI blijft intact bij latere docs-push (SOURCE/CI MERGED)

- [PR #962](https://github.com/Blacksp1d3r/runner-mcp/pull/962) exact head `aa39aa72e65abc9e8be27d9672d5ce8c9e15e530` **7/7 CI SUCCESS**: validation `42351656313` Ruff + **4708 pytest PASS**, reservering, disposable systemd, artifact en einddemo; clean Ubuntu `42351656367`, attribution `42351656262` beide SUCCESS. Squash MERGED `f79f07e27b5af1d97c7019f298e42c5275af85f9`, PR/main readback bevestigd.
- De twee bestaande `validation.yml`/attribution-workflows annuleren nu alleen verouderde PR-runs, niet reeds **lopende** main-runs bij een latere main/docs-push. Geen nieuw CI-systeem/updater. **Beperking:** GitHub native concurrency kan nog verouderde *wachtende* runs vervangen; iedere source SHA fysiek afwerken is hiermee niet universeel bewezen. Echte activatie blijft #669/#341/Fabric #942/#943/ACK WAIT.

## 0.1.153 — #662 automatische main-releasecontrole behouden wanneer latere commit binnenkomt (BRONKANDIDAAT)

- Bestaande `validation.yml` en `commit-attribution-policy.yml` hadden `cancel-in-progress: true` op hun main-ref concurrencygroep. Een opvolgende, louter documentatiecommit kon daardoor de vorige, werkelijk versiebepalende source-push afbreken vóór de einddemo, zelfs als een exact wheel/sdist-artifact al was opgeslagen.
- Alleen bij `pull_request` worden nu achterhaalde runs geannuleerd; elke main-push houdt zijn eigen bestaande run/commit en blijft in de bestaande concurrencygroep ordelijk afwerken. Geen nieuwe workflow, runner, controller of artifactopslag. De bestaande normale `release-artifact`-job, versiereservering en CI blijven ongewijzigd.
- Feitelijk gereproduceerd: v0.1.152 main push `4155e7f7219139603a167dbaa72abb84694c749b`, validation `42351052147` CANCELLED door volgende docs main push, maar artifact `runner-mcp-candidate-0.1.152-4155e7f7219139603a167dbaa72abb84694c749b` id `13565557686` is wel gepubliceerd; niet gelijkstellen aan complete main-run PASS. Nieuwe regressie beschermt beide workflows. **Exact-head CI en merge voor 0.1.153 nog vereist.**

## 0.1.152 — F30/#341 local stage ZIP/RECORD consistentie CI VOLTOOID / MERGED (7 november 2026)

- [PR #961](https://github.com/Blacksp1d3r/runner-mcp/pull/961) exacte head `ef54623fb6062f18b000345eb0ea68750cb4f10e`: 7/7 CI SUCCESS, Ruff, **4707 pytest PASS**, release-reservering, gebouwd artifact, disposable systemd en volledige demo in [validation 42350814697](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42350814697), Clean Ubuntu 42350814668 en attribution 42350814756 SUCCESS. Squash MERGED `4155e7f7219139603a167dbaa72abb84694c749b`, GitHub main en PR readback bevestigd.
- De drie bestaande `stage_local_bundle`-checkpoints (bestaande opgeslagen bundel, nieuwe builder vóór NOREPLACE, opgeslagen eindbundel) hergebruiken nu de al aanwezige `verify_wheel_records=True`; negatieve repinned wheel+SHA256SUMS-tests weigeren vóór READY/promotie, positieve flows slagen. Geen nieuwe updater of tool.
- **Bron/CI voltooid; productie NIET geïnstalleerd:** originele host/serving-wheel #669, eigenaarpolicy, A6 #942, autonome A7 #943/#341 en original-client ACK blijven hard WAIT. ED productsleutel uitgesteld; Qwen/Claude/SQL ongewijzigd.

## 0.1.152 — F30/#341 bestaande local-stage status ook aan ZIP/RECORD binden (BRONKANDIDAAT)

- Na 0.1.151 was `local_readiness` al strikt maar `stage_local_bundle` nog niet: de route voor een reeds bestaande `local-bundles/<commit>` kon `alreadyStaged=true, bundleReady=true` teruggeven na alleen lokale SHA256SUMS. Ook de verse GitHub-clone/build controleerde vóór en na NOREPLACE nog slechts de lokale hashes. Deze drie bestaande `_validated_bootstrap`-aanroepen gebruiken nu `verify_wheel_records=True` via exact de AL BESTAANDE ZIP/METADATA/RECORD-validator, zonder nieuwe codepaden.
- Synthetische negatieve test voor bestaande eerder opgeslagen wheel+herberekende SHA256SUMS, en geparametriseerde negatieve builder-output die eveneens herpinde checksums bevat; geen GitHub-credentials, subprocess op herhaalde check, install, nieuwe service of transactie. Bestaande positieve stage-idempotentie blijft intact.
- Alle vier version/discoverybestanden kandidaat 0.1.152. **CI/merge nog niet bewezen.** Geen zelfstandige host-/ownertrust, A6 #942, no-NIC A7 #943, oorspronkelijke serving-wheel #669, rollback #341 of originele-client-ACK; ED sleutel uitgesteld.

## 0.1.151 — F30/#341 lokale ZIP/RECORD-hercontrole vóór update (SOURCE/CI MERGED; NIET GEÏNSTALLEERD)

- [PR #960](https://github.com/Blacksp1d3r/runner-mcp/pull/960) gemerged als `22624dbf42c63f6b57d2161eaf88f6050128a6bd` vanaf exact geteste head `920dcf884b0d00c8149464371f867ca5d19a122e`. Alle 7/7 PR-head CI-gates SUCCESS: Validation `42310895233` met Ruff en **4705 pytest PASS**, release-reservering, gebouwd wheel/sdist, disposable systemd en vijfminutendemo; Clean Ubuntu `42310895135` en attribution `42310895172` SUCCESS.
- Hergebruik van de **bestaande** `fabric_release_wheelhouse._wheel_record_check` in `FabricUpdateManager._validated_bootstrap` met opt-in alleen voor `local-custody`: ZIP/METADATA/RECORD herlezen bij `local_readiness`, vóór/na lokale kopie en vóór de bestaande BOOTSTRAP-preflight. Negatieve test vervangt na geldig bewaren het wheel én herberekent SHA256SUMS; digest-only check passeert, volledige ZIP/RECORD-check weigert zonder activatie.
- Bestaande oudere positieve fixtures werden naar werkelijk geldige ZIP/METADATA/WHEEL/RECORD bijgewerkt. Eerste PR-heads faalden terecht op ontbrekende `glama.json`-version parity, Ruff importvolgorde en **5 tests met ongeldige oude fixtures**. Negatieve CI bewaard, oorzaak/aanpak in bestaand Failure Museum.
- **Geen productie-installatie, owner-/CI-/hosttrust, rollback- of ACK-bewijs.** Origineel #669, A6 #942, A7 #943/#341 en echte oorspronkelijke-client result+ACK blijven WAIT; geen nieuwe updater, signer, daemon of Qwen/Claude/SQL-wijziging. ED owner key nog uitgesteld.

## 0.1.150 — F30/#341 GitHub CI-release alleen INACTIEF bewaren, zonder Ed-productiesleutel (SOURCE ONLY)

- Nieuwe private managerroute _stage_github_release_inactive_once hergebruikt de 0.1.149 vaste GitHub Release/tag-admission en complete asset-ID/bytes/BUNDLE/ZIP/RECORD-controle; daarna exact dezelfde bestaande eigenaar-private create-once NOREPLACE bronopslag in local-bundles/<commit>. Geen tweede downloader, opslagformaat, updater of launcher.
- Refactor van de bestaande ondertekende storage: gedeelde _store_verified_inactive_bytes_once met 0700 root/source, 0600 bytes, veilige filesystem-dirs, fsync, digest-readback, renameat2 NOREPLACE. Historische Q7 en optionele Ed25519 signed import blijven intact. Na partiële schrijf-/promotiefout blijft .incoming forensisch bewaard; nooit overschrijven.
- Synthetische 5/33/160 assets + negatieve testmatrix wrong commit/release-ID, corrupt ZIP/manifest, verkeerde root/mode, pre-existing target, herhaalde stage en gekoppelde manager zonder extra metadata-GET. Geen echte host, secrets, service, toolcatalogus, install, active bundle, rollback of ACK.
- Provider SHA en de supplied releasepin zijn GEEN zelfstandig eigenaarbewijs: github_ci_policy_verified/independent_owner_signer_verified/install_authorized/rollback_verified blijven false. Echte host build-identiteit #669, lokale A7 #341/#943, off-target A6 #942 en oorspronkelijke client-ACK blijven vereisten voor installatie.

## 0.1.149 — F30/#341 GitHub-release volledige bytes zonder productie-Ed25519 (SOURCE ONLY)

- Private method FabricUpdateManager._read_exact_github_release_bytes uses the EXISTING exact-tag fixed GitHub Release admission and asset-ID downloader, with per-asset SHA256/size, full BUNDLE/COMMIT_SHA/SHA256SUMS and shared ZIP/METADATA/RECORD verification (5..160 assets). No new updater, no second download client, no ED key, no CLI or public MCP capability.
- GitHub metadata is provider integrity only; NOT an independent owner signature. github_ci_policy_verified=false, independent_owner_signer_verified=false, host installation and rollback unauthorized. Synthetic 5/33/160 checks plus negative cases.
- Owner priority: working automatic updates and usable Qwen and Claude first; independent ED optional afterward. Connected 0.1.88 and original host #669/#341, physical A6 #942/A7 #943 and original client ACK still WAIT. Source merge never equals installation.

## 0.1.148 — F30/#937 exact ondertekende Release → bestaande INACTIEVE NOREPLACE custody (SOURCE ONLY)

- Eén nieuwe private managerstap `_stage_signed_release_description_inactive_once` hergebruikt de v0.1.147 eigenaarspins/Release-body/één metadata-snapshot, dezelfde volledige SHA/manifest/ZIP/WHEEL/RECORD signed-bytecontrole en v0.1.145 eigenaar-private `_stage_signed_release_inactive_once` met O_NOFOLLOW, 0600/0700, fsync en atomaire NOREPLACE. Geen tweede systeem of downloadclient, geen actief slot vervangen.
- Oude private in-memory API blijft identiek via dezelfde getypeerde kandidaat; nieuwe status `download_performed=true` pas na volledig geverifieerde en fsync-gepromoveerde inactieve bron. `owner_authority_proven/install_authorized/rollback_verified/original_client_ack` blijven FALSE.
- Alleen synthetische 5/33 wheel-bundles en 5 negatieve scenario's: ontbrekend signed body/ownerkey, onderbroken transport, symlink-root, bestaand target. Geen nieuwe MCP-tool, geen echte host-/token-/systemd-/Claude-/Qwen-/SQL-wijziging.
- HARD WAIT blijft de echte onafhankelijke owner-signer/Fabric #924 distributie, oorspronkelijke serving-host/wheel #669, herstel #341, fysieke A6 #942/A7 #943, oorspronkelijke issuer result/ACK. Broncode en groene CI zijn GEEN fysieke updatebevoegdheid.

## 0.1.147 — F30/#937 bestaande Release-body → manager signed-bytebatch (SOURCE ONLY)

- De private `FabricUpdateManager._read_verified_signed_release_description_bytes` gebruikt de AL bestaande vaste GitHub Release/tag-GET precies eenmaal om het publieke getypeerde `ReleaseAdmission` én de onbetrouwbare Release-description te verkrijgen; de openbare `release_assets_readiness` blijft identiek.
- Hergebruikt bestaande Ed25519/canonical-Base64 parser (0.1.146), extern vereiste signer/commit/release-ID-pins en dezelfde batch-downloader (0.1.142) voor volledige BUNDLE/COMMIT_SHA/SHA256SUMS/ZIP/WHEEL/RECORD-verificatie; geen tweede API-client, credentialbron of downloadpad.
- Alleen synthetische, in-memory 5/33/160-bestandstests, foutieve body/signature/key/source/release-ID, provider asset-ID/digest-mutaties en partiële downloads; blokkade vóór asset-GET. Geen nieuwe MCP-tool, eigenaarstrust, fysieke custody, start/apply, daemon of actieve servermutatie.
- HARD WAIT: werkelijk onafhankelijk beheerde eigenaarssigner + geactiveerde releasebeschrijving (Fabric #924), originele host/wheel #669, herstel #341 en fysieke A6 #942/A7 #943 met originele result/ACK.

## 0.1.146 — F30/#937 signed Fabric Release-body verifier (SOURCE ONLY)

- Nieuwe strikt private `fabric_release_body_envelope.verify_signed_release_body` haalt een exact Base64-tekstblok uit de al bestaande GitHub Release-beschrijving, ZONDER extra release-asset, nieuwe URL, host- of bestandstoegang. Bron, Release-ID en SHA256 van de public key blijven onafhankelijk vanuit eigenaarbeleid vereist.
- De bestaande Ed25519-verifier controleert de originele bytes en de vaste trusted-key-fingerprint, en vergelijkt daarna ALLE 5–160 assets exact met de al gekwalificeerde `ReleaseAdmission` (IDs, groottes en digests). Dubbele/afwijkende markers, padding, extra regels, ontbrekende handtekening of provider-aanpassingen fail closed.
- Synthetische tests 5/33/160 bestaande wheelcases en 17 ongeldige omschrijvingen. Geen gekoppelde live manager, nieuwe MCP-tool, download, inactieve fysieke import, echte signer of installatie. Fabric #924 independent owner key/distributie en #669/#341/A6/A7/original client ACK blijven HARD WAIT.

## 0.1.145 — F30/#937 signed-release-inactive-custody (SOURCE ONLY)

- Nieuwe private _stage_signed_release_inactive_once hercontroleert Ed25519-rooster, exacte bron/release/key-pins, GitHub metadata en volledig BUNDLE/COMMIT/SHA256SUMS/ZIP/RECORD vóór schijfgebruik. Aangeleverde testpins geven nooit echte eigenaarbevoegdheid.
- Schrijft 5–160 gecontroleerde bestanden in bestaande owner-private root via O_EXCL/O_NOFOLLOW, 0600, fsync en teruglees-SHA; hergebruikt bestaande atomaire NOREPLACE promotie. Onvolledige .incoming blijft voor onderzoek staan; nooit bestaand slot vervangen.
- Alleen fictieve offline tests (5/33 wheels, signer/bytes, symlink, race, onderbroken schrijfactie). Geen MCP-tool, echte download, activatie, install, servers, tokens of Claude/Qwen/SQL-mutaties.
- HARD WAIT: Fabric #924 onafhankelijke echte signer/roster/owner-policy, #669/#341 en A6 #942/A7 #943 + oorspronkelijke result/ACK.

## 0.1.144 — F30/#937 interne ketentest metadata → volledig signed release-batch (SOURCE ONLY)

- De bestaande `FabricUpdateManager` hergebruikt zijn eigen read-only, getypeerde `_read_exact_release_admission` (exact twee vaste GitHub Release/tag-eindpunten) en de in 0.1.142 geteste `fetch_exact_signed_fabric_bundle_bytes` via één uitsluitend **interne** `_read_verified_signed_release_bytes`. Het ondertekende rooster wordt zelfs vóór het eerste metadata-GET gecontroleerd; de batch controleert dezelfde handtekening opnieuw vóór de eerste asset-GET, alle SHA-/groottespins, het volledige manifest en ZIP/METADATA/RECORD. Geen nieuwe URL, downloader, credentialbron, service of API.
- Synthetische testuitbreiding in bestaand `tests/test_fabric_release_asset_batch.py`: fictieve Ed25519-handtekening en 5/33 werkelijke wheel-ZIPs, één exacte bestaande metadata-route, foutieve key/commit/release-ID zonder metadata-GET, gewijzigde GitHub asset-ID zonder asset-GET, onderbroken batch zonder gedeeltelijke release, en statische controle op ontbrekende servertool/stage/activatie-aanroepen.
- Geen download van echte assets, geen inactieve disk-custody, installatie, BOOTSTRAP, launcherwissel, rollback of client-ACK; historisch Q7 en externe `release_assets_readiness` blijven ongewijzigd. De waarden `independently_trusted_key_sha256`, sourcecommit en release-ID moeten later werkelijk **buiten** de aanroeper door eigenaar/Fabric beheerd worden; zelf ondertekenen geeft geen autorisatie.

## 0.1.143 — F30/#937 hergebruik exact Release-metadataresultaat, geen extra API-route (SOURCE ONLY)

- De bestaande `FabricUpdateManager.release_assets_readiness` behoudt haar publieke JSON-status en twee vaste GitHub Release-/tag-ref-verzoeken, maar verkrijgt het resultaat via een interne `_read_exact_release_admission` die het oorspronkelijke getypeerde `ReleaseAdmission`-object teruggeeft. Hiermee kan een toekomstige onafhankelijke signed-releaseverbruiker dezelfde gevalideerde asset-IDs, namen, groottes, SHA-256 en exact commit/release-ID hergebruiken zonder een tweede parser, tokenroute of metadata-downloader te maken.
- Exacte generieke en historische Q7 tags blijven ondersteund; bestaande dubbele 404, providerfout, ontbrekende SHA en tegenstrijdige metadata behouden hun huidige openbare foutcodes. Geen assetbyte-download of schijf-/host-/launcher-/servicemutatie, geen `start_local` of `apply`.
- De bestaande metadata-readiness tests zijn uitgebreid voor het getypeerde resultaat, publieke backwards compatibility en geen onbedoelde download, lokale stage of actieve bundlewissel.
- Nog niet beschikbaar: werkelijk onafhankelijke publisher/eigenaars-signer en policy, getekend echt generiek Release-rooster, host owner/serving-wheel, originele ACK en fysieke A6/A7 herstelbewijzen.

## 0.1.142 — F30/#937 generieke signed assetbyte-batch via bestaande downloader (SOURCE ONLY)

- Binnen de **bestaande** `fabric_release_asset_bytes.py` verifieert `fetch_exact_signed_fabric_bundle_bytes` eerst een exact Ed25519-ondertekend Fabric-rooster met onafhankelijk *aangeleverde* key-fingerprint/commit/release-ID, en vergelijkt dat met de bestaande exact-gevalideerde GitHub Release/tag-metadata **vóór de eerste asset GET**. Daarna hergebruikt hij per file de huidige vaste-repository `fetch_pinned_asset_bytes`. Bij iedere respons hercontrole op bytes/grootte/SHA256; pas bij alle 5–160 assets geslaagd wordt het bestaande full manifest-/SHA256SUMS-/ZIP/METADATA/RECORD-gate doorlopen.
- Volledig in-memory resultaat; geen stage, bestandsschrijfactie, service, updater, daemon, tokenopslag, `start_local`, `apply`, rollback of worker. Bij mislukte byte of providerrespons: vaste veilige foutcode, geen gedeeltelijke resultaten; maximaal 256MiB complete bytes en dezelfde individuele 64MiB-assetlimiet. Bestaande vaste Q7-functies niet gewijzigd.
- Testbestand `tests/test_fabric_release_asset_batch.py`: fictieve Ed25519-sleutels en ZIP-wheels, 5/33/160 items, voor-download-fail-closed identity mismatches, onjuiste/partiële/verstoorde bytes en negatieve ZIP-inhoud. Geen echte download, host, secret of privé-bron gebruikt.
- **GEEN echte onafhankelijke uitgeversbevoegdheid:** extern beleid moet signer/source/release-ID werkelijk vastpinnen. Een zelfgekozen sleutel en Github-digest zijn geen approval. Fysieke S2e custody, #669/#341, Fabric #924/#942/#943 en originele client-ACK blijven open.

## 0.1.141 — F30/#937 veilige atomaire inactieve bundelpromotie, SOURCE ONLY

- In de **bestaande** `FabricUpdateManager.stage_local_bundle` wordt de laatste lokale promotie van een reeds gevalideerde `.incoming-<uuid>/source/bundle` naar `local-bundles/<exact commit>` niet langer met `os.replace` uitgevoerd. Een statuscheck vooraf is gevoelig voor een race: twee actoren kunnen tegelijk constateren dat de doelmap vrij is, waarna `os.replace` zelfs een nadien aangemaakte lege doelmap kan vervangen.
- De nieuwe interne `_promote_inactive_bundle_noreplace` hergebruikt de bestaande Linux `renameat2(RENAME_NOREPLACE)`-primitive uit Q7-custody met vaste relatieve paden en een eigenaar-private open directory-descriptor. De `incoming`-map blijft eigenaar-privé (0700); `source` en `bundle` zijn elk met `O_NOFOLLOW` geopend en mogen, zoals een normale Git-clone, wel 0755 zijn zolang eigenaar/geen groeps- of wereldschrijfrechten gegarandeerd is. De rename is atomair en weigert elke al bestaande bestemming; geen nieuwe updater, download-API of opslagstructuur.
- Nieuwe uitsluitend met pytest-tmp_path uitgevoerde tests bewijzen succesvolle create-once, gelijktijdige doelmaprace, lege/volledige bestaande bestemming, symlink/padinput/mode-inbreuken, onvolledige stage en behoud van `bundle/`, `slots/` en `transaction.json`. Bronwijziging verandert geen Q7 historische custody, release-signatures of actuele servers.
- Dit is **geen** volledig vertrouwde generieke GitHub Release-import. De onafhankelijke Fabric-publisher signer/bronpin, echte bytes, provenance, fysieke A6/A7 en originele ACK zijn afzonderlijke vereisten.

## 0.1.140 — F30/#937 generieke wheelhouse ZIP/METADATA/RECORD-controle (SOURCE ONLY)

- De bestaande `fabric_release_wheelhouse.py` heeft een extra `verify_signed_fabric_wheelhouse` ingang, die eerst de generieke ondertekende 0.1.138 roster- en volledige 0.1.139 byte/BUNDLE/SHA256SUMS-controles hergebruikt en daarna alle 1..156 wheels controleert met de reeds bestaande Q7 ZIP/METADATA/RECORD-lezer.
- De historische vaste Q7-functie `verify_pinned_q7_wheelhouse` blijft 29/29 wheels en 33 assets vereisen en behoudt exact dezelfde resultaatvelden. De algemene variant ondersteunt bijvoorbeeld 5/33/160 assetbundels, test structurele ZIP-fouten en meldt `wheel_metadata_verified=true` enkel over de aangeboden in-memory bytes; onafhankelijke signer-/serverautoriteit, werkelijk gedownloade bytes, private custody en activatie blijven false.
- Geen netwerk, download, bestandsschrijfactie, packageinstallatie, subprocess, update, nieuwe signer, tweede updater of echte rollback. Origineel verbonden Runner-MCP 0.1.88 en A6/A7/ACK blijven fysiek onbewezen.

## 0.1.139 — F30/#937 gedeelde volledige Fabric-bundelcontrole, SOURCE ONLY

- De bestaande `fabric_release_full_bundle.py` controleert voortaan via één gedeelde zuivere routine Q7 én een generieke exact ondertekende Fabric Release (5..160 assets): elke naam, ID, bytes, SHA256, totale grootte, COMMIT_SHA, BUNDLE.json-velden, BOOTSTRAP.py en SHA256SUMS. De bestaande Q7-interface behoudt de vaste 33 bestands-/29 wheelcontracten en ongewijzigd publiek resultaat.
- De nieuwe `check_complete_signed_fabric_bundle` vergelijkt eerst via de reeds gemergede 0.1.138 ondertekende exacte roostermetadata met GitHub, dan de volledige in-memory inhoud tegen de afzonderlijke pins en manifestrelaties. Een juiste bytevergelijking levert alleen `bundle_consistency_only` en expliciete `operator_signer_authority_attested=false`, `wheel_metadata_verified=false`, `local_custody_verified=false`, `download_performed=false`, `mutation_authorized=false`, `rollback_verified=false`, `original_client_ack_proven=false`.
- Nieuwe synthetische regressies voor 5/33/160 bestanden, vervalste manifests/commit, ongeldige SHA256SUMS, veranderde ingelezen bytes en GitHub metadatarijen. Historische Q7 regressies blijven verplichte bronacceptatie. Dit is nog GEEN wheel ZIP/RECORD-inspectie, download, owner-private storage, signer/host authority, update of zelfstandige rollback.

## 0.1.138 — F30/#937 generiek ondertekend Release-rooster, alleen offline SOURCE

- Nieuwe zuivere module `fabric_release_signed_roster.py` hergebruikt de bestaande `inspect_exact_release` voor iedere geldige exacte `fabric-update-bundle-<sha>`. De module controleert Ed25519 op originele bytes, door de aanroeper *onafhankelijk* gepinde publieke-sleutel-SHA256, exacte broncommit en release-ID, versiegebonden repository en verplichte assetset met strikte naam/ID/grootte/digestcontrole.
- Eén pure vergelijking bindt de ondertekende assetinventaris aan echte GitHub Release-metadata. Synthetische negatieve tests omvatten vreemde/verwisselde sleutels, dubbele JSON-velden, te grote documenten, ongeldige assetsets, gewijzigde SHA/IDs en foutieve bron/tag/release-ID. De historische Q7-ondertekening en `fabric_release_signed_import.py` blijven ongewijzigd.
- De uitkomst blijft `match_only`, met `operator_signer_authority_attested=false`, `download_performed=false`, `install_authorized=false`, `rollback_verified=false` en `original_client_ack_proven=false`. Er bestaat nog GEEN gekwalificeerde generieke eigenaar-signing key/provider-binding; het nieuwe schema `runner-fabric/signed-release-roster/v1` is slechts een toekomstig contract, geen bestaande productiepublicatie. Geen download/custody/import, serveractie of nieuwe updater.
- GitHub-bron is niet dezelfde toestand als de fysiek verbonden Runner-MCP v0.1.88; #669, #341, Fabric #924/#942/#943 en ACK blijven onafhankelijk vereist.

## 0.1.137 — F30/#341 exacte Release-foutcategorieën (SOURCE ONLY)

- GitHub Release metadata blijft een read-only controle van het bestaande, exacte Fabric-pakket; nul download, installatie, activatie, nieuwe updater of rollback.
- Twee vaste GitHub 404-antwoorden -> `release_not_published`; één van beide ontbrekend -> `fabric_release_assets_unqualified`; HTTP/provider uitval -> `release_provider_unavailable`; asset-SHA metadata ongeldig -> `release_digest_invalid`. De bestaande Actions-updatebron en fail-closed autorisatie blijven ongewijzigd.
- Synthetische negatieve regressies dekken providerfouten, onvolledige metadata, vervalste HTTP 200 en geheime tekst. Deze **GitHub source** is niet de werkelijk geïnstalleerde Runner-MCP op originele hosts; A6, A7, #669 en oorspronkelijke-client ACK blijven noodzakelijke aparte controles.

## 0.1.85 (#341/#585 single original owner-private publisher sibling; SOURCE ONLY)

- On physical original `github-runner`/`gha-runner`, the separately held original machine credential already passed exact authenticated SQL issuer GET as `runner:control`, but its active Runner-MCP parent uses a different CLI-selected private config directory and reports `ISSUER_IN_PARENT_CONFIG=MISSING`. No copy or new issuer identity is appropriate.
- The existing optional Fabric qualification loader now admits exactly one original credential file from the default owner-private Runner-MCP directory OR the same owner's separately custodied Runner-Fabric sibling. Fail closed on dual issuers, symlinks, unsafe owner/directory/file permissions, non-machine issuer mode, invalid origin/secret; a custom config root never auto-selects the sibling. If no publisher file is present, the optional publisher remains disabled. Synthetic tests enforce no credential copy and negative cases.
- **Not deployed.** Active connected original MCP remains 0.1.38 with source/wheel provenance unverified and `self_update_ready=false`; previously installed Fabric issuer environment/tools absent; Fabric #1730 rollback reliability fix source-only. Do not infer completed SQL Black submit/claim/result/digest/ACK or Claude/Qwen dispatch from CI. No server mutation, rotation, second tunnel/relay/controller, login/MFA, or blanket restart.

## 0.1.84 (#341/#585 privately custodied original Control Center issuer forwarding; SOURCE ONLY)

- The existing Runner-MCP qualification Agent may now load the **already owner-custodied** `af585-control-issuer.env` private file and forward only its exact fixed machine issuer identity, HTTPS origin, and credential to the same pre-existing Fabric Agent process. Reject world-readable files, symlinks, other origins, role substitution, wrong key sets, or invalid credential values. A missing optional file retains previous behavior. Existing untrusted main configuration cannot promote a worker to a publisher.
- This is **source-only**; the physical `aifordable-lab` managed Fabric launcher is still exact revision `927c15392e1caae74463b1322296d367811e116c`, and the new `build_black_original_issuer_service` does not yet exist in its active slot. Current central Runner-MCP 0.1.38 also remains without qualified upgrade. Physical original one-shot Black SQL command/result/ACK is NOT claimed.

## 0.1.83 (#341 fixed Black post-ACK payload readback; SOURCE ONLY)

- The existing fixed Black original-client ACK verification now checks that the **actual terminal result payload** in the second durable SQL readback is identical to the pre-ACK result, not merely the reported digest, result code, version and worker generation. A mismatched payload retaining the old digest fails closed as an inconsistent original-client proof. This does not add another query, relay, endpoint, signer or permission: it strengthens the comparison of the two already fetched authenticated Fabric status records.
- Regression exercises a tampered terminal result payload with unchanged digest; all existing human MFA/machine-only `runner:control` contract tests remain. Live central still serves 0.1.38 and must not be blindly updated; physical original Black command/result/ACK remains unproven until the separately qualified issuer and actual serving Fabric/Runner-MCP release are available. No host or customer deployment from this source release.

## 0.1.82 (#341 fixed Black original machine requester evidence; SOURCE ONLY)

- The existing three first-party `control_center_black_submit/status/ack` tools can now validate the **owner-approved MACHINE issuer** as well as the historical human MFA original requester. Machine receipts are accepted only for exact fixed `qual:black:runtime:v1` → `runner:black` → `runtime_status` and requester identity exactly `runner:control`; values are read from the authenticated Fabric Agent result, never treated as authorizing themselves. Worker `runner:black`, `runner:primary` and wrong ID/target cannot become publishers by changing a field.
- Preserve the actual source-reported `requested_by_auth_strength=machine`, enforce unchanged requester and strength, positive worker claim/generation, fingerprint, terminal digest, version and SQL-persisted post-ACK status readback. Synthetic tests reject worker impersonation, relabelled MFA, swapped issuer, changed claim generation/digest and wrong request.
- **SOURCE ONLY.** AIfordable PR #636 machine endpoint is merged/staging-tested; PR #637 alternate original `/internal/control-relay/commands` interface and Fabric #1714 are open and must be reconciled into one canonical SQL issuer path (never run both as two production command authorities). Actual `runner:control` correct-host service credential, connected serving central still 0.1.38, real Black claim/result/durable ACK and six protected role update remain unproven.

## 0.1.81 (#341 Black worker generation and post-ACK lineage guard; SOURCE ONLY)

- Harden the existing fixed Black Control Center `runtime_status` source proxy: queued results require no claimed worker generation (zero); claimed/completed/failed require a positive existing worker claim generation. Never interpret a terminal result with generation zero as having reached the physical target.
- After an explicit ACK, require the second original-client status readback to preserve the same claim generation, original requester and canonical request fingerprint in addition to the exact result digest/version and acknowledged state. No automatic ACK from GET.
- Pure synthetic regressions reject unclaimed terminal, bad queued/claimed lineage and non-fixed Fabric operation delegation. One existing authenticated Fabric Agent MCP path only; no new relay, issuer, key, host/endpoint choice, updater or deployment. Central serving 0.1.38 and isolated Black 0.1.30 are unchanged. AIfordable #585 REST PR #632 has now SOURCE MERGED; physical original-client Black result+ACK and actual authorized deployment remain pending.

## 0.1.80 (#341 Black Control Center bounded Fabric bridge, SOURCE ONLY)

- Added three optional MCP tools for only `runner:black`/`runtime_status`: `control_center_black_submit`, `control_center_black_status`, and explicit `control_center_black_ack`. These delegate to the already-authenticated local Fabric Agent MCP; no second relay, listener, tunnel, general command, host/path/endpoint choice or central live update.
- Existing Fabric and AIfordable own command issuance, operator MFA/subject and durable ACK. Runner-MCP enforces exact target, operation, request ID, canonical fingerprint, original requester subject with MFA claim, queue version, terminal result digest, and separate post-ACK readback. Missing Fabric issuer tools, weak/mismatched identity, premature ACK and invalid result fail closed.
- This is SOURCE ONLY. Fabric Agent MCP issuer adapter to the original Fabric commandclient and AIfordable MFA operator endpoint is not deployed; AIfordable #585 PR #632 is upstream SOURCE CANDIDATE. Original client physical `runner:black` request/result/ACK is NOT PROVEN. Existing central six roles and live 0.1.38 are unchanged; #341 remains open.

## 0.1.79 (#669 receipt publication uncertainty; source-only)

- Repair a crash/durability edge in the existing offline original-wheel receipt writer: after verifying the exact wheel and installed Python modules, a failed parent-directory fsync is now classified as `WheelReceiptPublicationUncertain`. The already create-once 0600 receipt is preserved for independent reconciliation rather than silently unlinked and recreated. Early file fsync/byte-verification failure still cleans its own unvalidated receipt. Regression tests inject both errors and verify no false trusted identity or overwrite.
- This is an isolated source fix. The receipt is still offline candidate data, not a signed source/serving-process witness or authorization for production deployment. The active 0.1.38 generation remains unchanged; Runner-MCP #669 and Fabric physical A6/A7/original-client ACK gates remain open.

## 0.1.78 (#669 retained original wheel candidate receipt, isolated source only)

- Add `artifact_receipt_capture.capture_candidate_wheel_receipt` to be invoked by the already authorized initial wheel installer. It retains an immutable/owner-private candidate receipt binding supplied source-revision claim, SHA-256 of the exact original wheel and its Python package module bytes to the installed package, reusing the existing `offline_artifact_receipt_preflight` validator.
- Receipt is create-once 0600 in an existing private 0700 directory; refuses symlinks, unsafe wheel entries, missing/extra/tampered modules, invalid claimed revisions, overlarge manifests, missing or externally writable package data. No network, package install, new updater, service action, key or credential capture.
- Even a matching receipt is **offline original bytes only**, *NOT* independently trusted source revision, signed publisher, active in-memory code, systemd generation, previous working release, original-client ACK or self-update authorization. Existing `build_identity.source_revision`, `artifact_digest` and live `self_update_ready` remain fail-closed until Runner-MCP #669 independently qualifies the serving generation and current wheel. Source-only; protected 0.1.38 services unchanged.
- Tests cover valid new receipt, corruption after generation, tampered/incomplete wheel, duplicate publication, linked paths, invalid source, unsafe permissions and prior incomplete package. Next: wire this helper into the existing qualified installer, retain an independent previous-generation copy and bind its identity to a fresh server process receipt via Fabric's authenticated original-client route; do not turn its output into live promotion authority.

## 0.1.77 (#669 actual serving-instance epoch must survive manager status merges)

- Correct a false-attribution possibility introduced when existing status managers are merged into `runtime_status`: they could overwrite the local `serving_instance_epoch` or set `serving_instance_epoch_authenticated=true`. The existing central provenance finalizer now takes the current MCP server's in-memory epoch separately and always replaces any manager-supplied epoch or trust flag.
- Preserve backward-compatible unit call sites by emitting a null epoch when no local instance epoch was independently supplied. Reject malformed trusted-local epoch input. Synthetic tests cover swapped/stale/malformed manager values, explicit fake authentication, and unchanged imported-version/wheel fail-closed behavior.
- This remains a **local correlation hint only** (never verified host/route, six actual process roles, wheel SHA, source revision, original-client ACK or production authorization). No new MCP tool, relay, updater, installer, host process/service or credential work.

## 0.1.76 (#669 local serving-instance epoch, source only)

- Added one per-MCP-server **opaque serving instance epoch** to the existing `runtime_status` and `serving_process_observation_preflight` output, stable for one live server instance but different across process forks and restarts. The two reads can now be correlated without confusing an interactive PATH-selected `runner-mcp` executable with the actual serving MCP process. A second service using the same package version receives its own epoch.
- This identifier **does not authenticate host, service asset, route, source revision, wheel digest, original client, or result ACK**. Both fields explicitly mark `*authenticated=false`; central 0.1.38 remains live and unverified. The existing `active_build_provenance_verified=false`, `self_update_ready=false` fail-closed rules are unchanged.
- Local unit tests cover same-instance stability, distinct instances, forked process separation and accidental disclosure regressions. No new updater/relay/worker, no host state changes, no automatic 0.1.76 deployment.

## 0.1.75 (#669 reply-local identity scope; source only)

- `runtime_status` explicitly labels its evidence as **this connected serving process only**. Even if another host or an interactive CLI has the same package version, the reply does **not** claim independently verified host/route, loaded wheel/module bytes, or all six real role process identities. Version equality is reported only as a literal loaded-vs-installed string comparison, never as attestation.
- Override untrusted status-manager claims about reply origin or other roles with deterministic unverified fields; synthetic tests cover a stale CLI, an in-place upgrade, equality across distinct hosts, and managers claiming false cross-host trust. No host identifier, path, credential, new agent/updater, production installation, or service mutation.
- Current original connected production v0.1.38 remains unverified: wheel/source null, A6 0/11, `self_update_ready=false`. A source merge cannot attest an old live process; independent #669 old-wheel/real-role evidence and Fabric A6/A7/original-client ACK are still separate gates.

## 0.1.74 (F30 local Agent Bus worker preflight, source only)

- Added `runner-mcp agent-bus preflight` for safe **read-only** static local worker prerequisites on a configured rootless host. Reuses existing strict private configuration, relay/subject/credential, loopback endpoint and fixed Fabric launcher validators. Missing rootless launcher reports `wait/fabric_launcher_unavailable` rather than a false online claim; incomplete, unsafe or malformed local prerequisites fail closed.
- No relay HTTP, worker start, credential generation, network request, durable state creation, disk mutation, service update, original-client ACK or new remote-control path. Output is limited to `state`, fixed `reason_code` and explicit `original_client_ack_proven=false`. Tests cover configured/missing/partial/unsafe/invalid cases, no secret echo and no side effects.
- Physical first-host `black` Q7 33/33 custody and isolated physical Fabric install already verified separately under Fabric #1563; this **source-only** CLI change is not deployed to the older 0.1.30 Black stage and does not qualify a worker or authorize sending Claude/Qwen jobs.

## 0.1.73 (#739 Black Q7 one-time private lab login, SOURCE ONLY)

- Existing standalone Black Q7 source zipapp adds **explicit** `lab-login` after privately verifying the fixed prerelease/tag metadata, `lab-logout` (no token/network), and one-hour `lab-probe-release` / `lab-import` credential reuse. Login saves a 0600 owner-only scoped short-lived credential under the existing Linux `/run/user/UID` runtime tmpfs (0700 dir), never in home, source, git, process args, persistent env, Github issue or Actions artifact. Missing/expired session falls back to the existing hidden `getpass`; importer automatically drops the cached credential when all 33 original verified bytes have been privately custodied. No fresh token is needed for subsequent `lab-readback` in any case.
- Fixed Black host, no-root, pinned exact Q7 release/33 assets, original signed production path, SHA256/wheel verifier, no install/worker dispatch, and existing protected six central roles unchanged. Tests check noninteractive reuse, denial for symlink, wrong mode/runtime, expired/replayed credentials, logout without network and failure with no saved invalid auth.
- **Current physical facts remain unchanged** until source archive transfer + trial: Black root/private preflight PASS, original Runner-MCP v0.1.30 staged agent-bus `configured` but convergence `not_initialized`; 33-file private release import still WAIT authenticated read access, no real Agent Bus result/ACK and no Claude/Qwen model call. This patch does not recover credentials entered elsewhere or make the existing 0.1.72 ZIP magically support `lab-login`.

## 0.1.72 (#739 Q7 keyless lab offline readback, SOURCE ONLY)

- Extend the SAME fixed standalone Black first-host zipapp with `lab-readback`, an entirely offline/credential-free, read-only verifier for the existing isolated `lab-unsigned-bundle`. At `lab-import`, commit an owner-private immutable unsigned receipt with all 33 actual byte sizes/SHA256 hashes in the same fsynced staging directory before atomic no-replace promotion. `lab-readback` reopens the fixed 0700 lab leaf and 0600/one-link receipt/files through no-follow directory handles, bounds content/count, rehashes all 33 assets without a network call or mutation, and returns LOCAL_STORAGE_ONLY; a second Python process test proves persistence across process boundaries. Tampered/missing/extra/symlink/hardlink/wrong-permission cases fail closed without repair. The existing signed `bundle` path and custody schema are unchanged.
- Local receipt is mutable by its owner and **not** an independently signed publisher witness, physically off-target A6 journal test, offline target outage proof or authorization to install/dispatch. Actual Black host lab testing/worker/client ACK still WAIT.

## 0.1.71 (#739 isolate unsigned lab custody from signed production bundle)

- Preserve existing fixed Q7 import and keyed producer, but give keyless disposable-lab bytes a separate owner-private `lab-unsigned-bundle` final leaf and `.q7-lab-unsigned-inflight` stage, preventing untrusted test contents from being mistaken for or blocking `bundle` signed custody. Reuse all existing SHA-256, full-bundle, no-follow, no-overwrite, flock and fsync checks. No install or dispatch. Signed route unchanged, same fixed root, no arbitrary path/second updater.
- Tests verify parallel lab and normal destinations, no source overwrite, partial lab failure cannot erase signed custody and unsigned receipt cannot be promoted to verified publisher identity.

## 0.1.70 (SOURCE ONLY: opt-in disposable Q7 keyless lab route)

- Owner-requested temporary test route on the fixed Black lab only: new `lab-preflight`, `lab-probe-release`, `lab-import` in the existing standalone importer. No Ed25519 publisher key needed for this explicitly UNTRUSTED-PUBLISHER lab path; it still pins exact GitHub repository, Q7 commit/tag/release ID, validates the 33-asset roster, verifies SHA-256 of every downloaded byte, invokes the existing wheelhouse/bundle/private no-overwrite custody, and takes a hidden read-only GitHub token. It does NOT install or activate a worker, change any serving Runner-MCP role or attest original-client result/ACK.
- The signed path is unchanged and remains for later production security hardening. Never promote keyless lab metadata into independent publisher provenance, automated updater admission or protected six-role rollout. Real A6 storage and physical independent-host readback and A7 six-role rollback remain separate unresolved gates.

## 0.1.69 (source-only #739 explicit first-host signed Q7 metadata probe)

- Add `probe-release` to the existing owner-Black pinned standalone zipapp. The new interactive, secret-redacted step first verifies the preexisting owner's detached Ed25519 33-asset roster against a separately provided SHA-256 key fingerprint, then makes only two fixed private GitHub REST JSON metadata GET requests (Q7 exact tag and ref) and compares exact release ID/source/33 IDs/names/digests. It **does not fetch any asset bytes**, create a bundle, install software or claim original-client ACK. Reuse the existing signed-roster/API admission functions, no second downloader, updater, tunnel or relay. Negative synthetic wrong signer/tampered metadata tests and a CLI test asserting the asset importer cannot be called from `probe-release`.
- Key match does not establish independent publisher authorization: a preapproved owner trust anchor and real hardware/UID custody, real Black API credential scope and package transfer remain required before physical Q7 import. Original central 0.1.38/active digest NULL, A6 0/11 and independent A7/ACK remain unchanged.

## 0.1.68 (source-only #739 exact first-host Q7 private root)

- Add one narrowly scoped Black-only `prepare-root` action to the already-built fixed Q7 first-host zipapp, not a generic folder manager. Only after observing an existing owner-private 0700 `~/.local/state` anchor, it atomically creates exact private `runner-fabric/control-plane-update` descendants using nofollow open FDs, nonblocking owner-only flock, mkdir 0700, dir fsync, and verifies owner/mode. Both roots already safe are adopted idempotently; a partial/wrong-owner/symlink/broadly accessible path fails closed without chmod/chown/delete/auto-repair. No GitHub API/token, independent signer authority, Fabric install, active worker, A6/A7 or original-client ACK from this action. Synthetic create/idempotency/partial/race/symlink negative tests.

## 0.1.67 (source-only #739 standalone first-host Q7 importer zipapp)

- Deterministic fixed-source Python 3.12 zipapp builder assembles only the exact eight approved Q7 import/admission/wheel/custody Runner-MCP modules plus no-install first-host entrypoint; the archive does **not** require installing the current Runner-MCP server generation on Black. On the exact local Black host, the zipapp reads four preexisting owner-private mode-0600 signed-roster/key/trust files from the fixed original Runner-MCP config and checks the fixed preexisting 0700 Fabric update root; `preflight` performs no network or filesystem mutation. `import` uses a scoped operator-interactive hidden GitHub token, verifies fixed signed Q7 roster and 33/33 release bits, invokes owner-private single-use custody; never uses pip, installs Fabric, starts workers, mutates relay or claims an ACK. Negative syntax, missing trust/root, replay/unsafe build tests. **Publisher-key authorization and real physical Black admission remain WAIT**: a matching key/hash does NOT independently prove publishing authority.

## 0.1.66 (source-only #739 signed Q7 asset fetch orchestration)

- Compose a separately Ed25519-signed 33-asset independent Q7 roster, trusted operator-supplied public-key fingerprint, fixed release/source/tag admission, strict GitHub REST HTTPS no-proxy/no-redirect 2× bounded JSON reads, existing 33 individual content-hash-checked asset-byte fetcher, and the existing fixed owner-private one-time bundle custody library. Every asset must match independently signed ID/size/SHA; reject duplicate schema keys, incorrect signature, key, source, tag/ref, release ID, API-side changed digest, corrupted bytes or unsupported REST URL. Synthetic network injection tests; no real token, download or host action.
- **Still missing:** an independently authorized/held publisher signer key on Black, standalone qualified first-host entrypoint not requiring new installed Runner-MCP, physical original Release 33/33 download, operator-verified wheel ownership and 0700 root, BOOTSTRAP.py preflight, separate install, and original-client result ACK. Returning `operator_signer_authority_attested=false` explicitly refuses to treat a matching signature under caller-provided key as publisher authorization. Original central 0.1.38, six roles, A6/A7 and Black existing relay unchanged.

## 0.1.65 (source-only #739 fixed private Q7 33-asset custody)

- Add `stage_pinned_q7_bundle_once` for the known owner-private per-user Runner-Fabric control-plane update root. First run the exact 33-asset + 29-wheel content gate, then use existing fixed-root 0700 owner custody, descriptor-pinned O_NOFOLLOW stage, exclusive create 0600 binary files, per-file and directory fsync, a root inode-held lock and one-time promotion to `bundle`. A failed partial stage remains preserved and refuses retries; existing bundle is never overwritten. Synthetic failure, symlink, wrong ownership, nonprivate-root and replay regression tests added. No arbitrary path from caller, network, token, install or service mutation. Source separately authenticated publisher signer / release pin, actual live Black bytes, owner-root readiness, BOOTSTRAP.py preflight and original requester ACK remain WAIT. Code merged does not authorize activation.

## 0.1.64 (source-only #739 pinned Q7 wheel ZIP/METADATA/RECORD gate)

- Add `verify_pinned_q7_wheelhouse` after the existing 33/33 independent-pin bundle check. Validate 29 wheels in memory without writing, downloading or executing: bounded ZIP members/decompression, filename-versus-METADATA identities, WHEEL v1.0, SHA-256 and size of every non-RECORD member, complete RECORD coverage, duplicate/path traversal/symlink/encrypted/archive-bomb denial. Adversarial ZIP fixtures cover corrupt names, bad digest, missing metadata, extra entries, symlink/traversal and malformed wheel bytes. Return `wheel_metadata_record_only` and explicitly keep independent signer, local custody, host activation, mutation and original-client ACK false. This does not install on Black and does not qualify Fabric A6/A7 or central 0.1.38.

# Changelog

## 0.1.57 (source-only #739 Q7 in-memory 33-asset bundle consistency)

- Add offline `check_complete_q7_bundle` to verify 33 bounded asset bytes against separately authenticated immutable pins. Fail closed on mismatched content, duplicated/invalid JSON manifest fields, wrong exact commit, malformed SHA256SUMS, bad bootstrap digest and 29 wheel roster mismatch. This function never authorizes signer trust, wheel METADATA, real downloads, sealed host custody, install, mutation or original-client ACK; remaining Fabric A6/A7 and #669 live-generation gates are independent. Synthetic-only tests. (#748)

## 0.1.56 (source-only #739 independent Q7 33-asset release roster)

- Add in-memory `compare_exact_pinned_q7_roster` for exactly 33 Q7 metadata assets: exact source/tag/release ID, filenames, numeric asset IDs, byte sizes and SHA-256 comparison with independently held pins. Malformed/duplicate/bool/unsafe records fail closed, with synthetic tests. A match is not signer proof, download/custody, mutation, installation or original-client result ACK. Parent #739 and Fabric A6/A7 gates remain open. (#746)

## 0.1.55 (source-only #669 current-MCP-process observation)

- Add fixed zero-argument read-only `serving_process_observation_preflight` for the authenticated currently connected Runner-MCP process. Categorically observes three already-imported modules and any loaded-vs-installed distribution version mismatch, never reads a remote host, filesystem paths, system PIDs, tokens or private signers. Output never attests a wheel/source generation, recovery authority or the other five managed roles; source/digest remain null and update/dispatch false even for an observed local roster. Synthetic negative tests cover missing/forged modules, loaded-vs-disk mismatch and private-output denial. (#669)


## 0.1.53 (source-only standalone #669 receipt path canonicality)

- Make the standalone `offline_artifact_receipt_preflight` refuse lexical parent traversal, relative input and linked ancestor paths for each of the receipt, wheel and installed-package inputs. Leaf-only `lstat()` previously allowed a linked grandparent before `resolve()`; this remains an offline byte-consistency check, NOT trust in the running process. Nine negative regressions prevent path aliasing and retain unverified active source and digest. No host/service mutation. (#669)


## 0.1.52 (source-only #669 active-generation update readiness fails closed)

- Prevent `runtime_status` from inheriting `self_update_ready=true` from a self-update transaction manager when the current loaded wheel/source and serving process remain unverified. Historical commit, git checkout, installed package version and manager readiness are not current-generation authority. Explicitly set update readiness to false alongside null active provenance; tests cover stale true/false/malformed manager data and hot-installed dist-info without process restart. Source only: this does not create any updater, trusted signer, A6/A7 journal or operational installation. (#669)


## 0.1.51 (source-only #669 canonical offline evidence paths)

- Reject relative, `..`-redirected or symlink-ancestor manifest/receipt/wheel/installed-package/generation paths before offline evidence-chain comparisons. Prevent a lexical `is_relative_to()` success from masking a redirected generation candidate; negative tests preserve fail-closed state and never claim active build identity. No host scanner or production install authority. (#669)


## 0.1.50 (source-only #669 installed RECORD negative admission)

- Limit extra pip-installed RECORD entries to the two declared Runner-MCP CLI scripts and standard pip metadata. Refuse arbitrary out-of-tree paths, duplicate console entries, malformed external digests and unbounded entries that were previously silently ignored by the offline source-vs-install comparison. Preserve legitimate pip extras and deliberately keep the resulting classification OFFLINE ONLY, never live attestation or update authority. (#669)


## 0.1.49 (source-only fixed A6 value integrity; not installed)

- In `runtime_doctor`, require exact fixed A6 configuration values, canonical already-qualified owner-private roots, plausible private bearer format and matching canonical Fabric revisions before returning `ready_11_of_11`. Eleven nonempty keys with a stale revision, wrong storage root/domain, loopback endpoint, probe target or secret format are no longer a green status. Synthetic regressions for each of eleven fixed keys, absent evidence directory, and correctly generated fixed values. This does NOT grant off-target A6 journal, independent A7 rollback, current loaded wheel/process proof or original-client ACK. (#509/#669)


## 0.1.48 (source-only A6 ancestor symlink hardening; not installed)

- Refuse symlinked *ancestors*, not only the final A6 private state/configuration directory, before canonical resolution. Also reject relative/parent-traversal lexical roots. A redirected grandparent must never cause an A6 journal/configuration read or the fixed 11-key private repair to be accepted. Add negative tests for state-root and config-parent aliases, traversal and no private writes; unchanged fixed binding authority. (#509/#669/Fabric #1617)
- The original connected central v0.1.38 remains unverified and unchanged. This source-only hardening does not prove off-target A6 storage, independent A7 rollback, a trusted currently loaded wheel or original requester ACK.


## 0.1.47 (source-only A6 diagnostic safety; not installed)

- Prevent `runtime_doctor` from reporting A6 unconfigured (0/11, absent journal/evidence roots) as PASS. Preserve safe non-mutating absence detail with WARN, classify malformed/private-root configurations fail-closed, and retain PASS for structurally complete private bindings only. Separate Fabric #942/#1617 off-target journal, A7 independent rollback and original requester ACK remain required for live update authority. This source correction does not modify private configuration, restart processes or install a wheel. (#509/#669)

## 0.1.45 (source-only candidate; release guard not yet branch-required)

- Implement fail-closed read-only GitHub current-main / PR-head / version admission for the unique next patch, with deterministic READY PR priority and twice-sampled contender inventory against races (#662). Reject wrong source/version, invalid API data and inherited proxy/redirect. Source CI alone cannot enforce merge atomicity: administrator-required check and fresh branch/serialized merges are separate gates. No live host release.

## 0.1.44 (source-only candidate; not deployed)

- Add independently pinned Ed25519 signed serving-witness input validator (#669), with exact host, source, wheel, generation, nonce, role instances, expiry and signature checks. Even a valid signed statement is OFFLINE and cannot establish current loaded host/process provenance or trigger update. No signing issuer, credential, live host observation or rollback authority.

## 0.1.43 (source candidate; not installed)

- Add bounded inert fixed GitHub Release asset-ID byte verifier (#739/#745), with no inherited proxy, exact size and independently supplied SHA256; allow strict direct 200 or narrowly authorized 302 with credentials stripped. Source-only security tests; never a full 33/33 signed importer, immutable storage, service activation, private host permission or Agent Bus ACK.

## 0.1.42 (source candidate; not deployed)

- Add operator-interactive pinned, standalone read-only GitHub Release metadata probe for first-host Fabric access (#739). Restricts repo/tag, disables proxies/redirects, bounds response, checks expected metadata and secret-safe category outputs. Offline security regressions. Neither release asset integrity, local custody, host activation nor original requester ACK is proven; no host action.

## 0.1.40 (source candidate; not published)

- Contain missing/invalid active-revision provider metadata errors as unknown rather than a runtime diagnostic tool error; preserve failed self-update activation and historical baseline guards (#669 / PR #742).
- Fail closed on malformed/unclean source checkout baseline evidence instead of accepting a coercible pseudo-commit or leaking a provider error (RMCP-F-0046, #669).
- Record explicit read-only, independently trusted serving-generation provenance acceptance design. This is not yet live wheel/host attestation or a manual-baseline reconciliation and grants no update/rollback authority.

## 0.1.39 (source candidate; not published)

- Add an optional **already configured project ID** to existing known-project preflight/prepare so mixed staging roots can select a safe destination without exposing filesystem paths. Keep no-anchor refusal and refuse second exact clone on another parent (#740). This does not register/deploy EnerCue, start Claude/Qwen, or relax Agent Bus admission.

## 0.1.38 (source candidate; not published)

- First-host Agent Bus read-only status identifies genuinely absent private base setup as `base_config_not_initialized` without making credentials, opening ports or weakening partial/unsafe config refusals (#735).

## 0.1.37 (source candidate; not published)

- Prevent direct operator-local recovery CLI inspect/finalize from creating Python import bytecode in a pinned source checkout; add ordinary-Python subprocess regressions without automatic stage recovery or service activation (#732).

## 0.1.36 (source candidate; not published)

- Mask complete variable-length GitHub App installation/access token families in bounded logs, including opaque URL-safe separators that the previous alphanumeric-only regex left partially visible. Regression tests cover `ghs_`, other GitHub token prefixes, truncated input and benign short strings. No real provider secrets or log data used; installed runtime unchanged (#730).

## 0.1.35 (source candidate; not published)

- Add a read-only, fixed-repository GitHub Releases asset attestation for Fabric offline bundles. Require exact tag/SHA and tag ref, 5-160 distinct bounded asset IDs/names/sha256 digests and mandatory source manifests. All queries are metadata-only; no URL follows, binary download, local archive writes, runner privileges, service upgrades or Claude dispatch. Existing Actions-artifact update route remains unchanged; an separately authorized custody importer must follow before any release install.

## 0.1.34 (source candidate; not published)

- Recover owner-held nested 0775/0664 pip/setuptools files only when protected by an independently checked owner-only 0700 private ancestor. Refuse shared parent/stage boundary, foreign ownership, symlinks and generated hardlinks; never chmod or reinstall an existing failed stage (#723).

## 0.1.33 (source candidate; not published)

- Automatically verify the actual fresh isolated Python 3.12 venv and pip >=23.2 before first-host stage prefix creation; missing Ubuntu Python venv packages produce a bounded denial without an unusable partial installation (#726).

## 0.1.32 (source candidate; not published)

- Add operator-local, fail-closed, manifest/host/source-bound recovery for intact previously blocked stages. Verify installed Python against immutable Git archive, wheel RECORD and CLI integrity, require explicit recovery-digest confirmation; no installer retry, activation, relay enrollment or ACK (#723).

## 0.1.31 (source candidate; not published)

- Isolate first-host staged installer builds in a pinned private Git-archive copy so setuptools-generated `build/` and `*.egg-info` never dirty the trusted source checkout. Preserve strict second source/host/manifest gate, no activation, and no retry of failed physical stages (Runner-MCP #721).


All notable user-visible changes to Runner MCP will be documented here.

Runner MCP is under active development. New changes remain under **Unreleased** until an exact validated commit is explicitly tagged and released.

## Unreleased

- Source candidate 0.1.30 (unreleased, never installed): rootless first-host bootstrap `diagnose --manifest` reads only the original failed stage's filesystem metadata, refuses unsafe path/host custody, emits allowlisted status without executing partial venv code or inferring pip functionality/host activation. Tracked under RMCP-F-0030 / #716 / #718; it cannot repair, retry, enroll or deploy Black.

- Source candidate 0.1.29 (not tagged, published or installed): local, unprivileged, operator-confirmed, SHA-pinned first-host staging bootstrap in scripts/managed_host_bootstrap.py. Uses existing install.sh; does not enroll a runner, start services, change disks or grant Fabric remote management. See docs/LOCAL_HOST_BOOTSTRAP.md and #713.

- Source package and MCP manifest versions advance to 0.1.4; this is a **pending candidate**, not a published release or deployment.
- Release guard prevents any source, tools, installer, scripts or workflow changes without a strictly higher version and matching metadata.

### Added

- local first-party ChatGPT/Codex plugin package rendering for the existing Runner MCP MCP
  boundary, including registered-app and HTTP/self-hosted modes without embedding bearer-token values.

### Security

- generated plugin packages are private by default, reject unsafe connection metadata and refuse to
  overwrite directories not created by Runner MCP.

## 0.1.3 — 2026-10-02

Published from exact commit `0aa013c279128e22fbd53be32c35bced3ae26834` through the protected release workflow after the full release check passed.

### Added

- proportional AI fault-containment regression coverage and deterministic security-gate boundaries;
- optional coarse Runner Fabric work-unit transport plus bounded first-install Fabric bootstrap guards;
- durable asynchronous migration-job storage with explicit async start/status integration;
- cross-process release-operation locking and bounded local one-release retention pruning;
- local-only bounded service-journal reads behind explicit per-service opt-in;
- AIfordable Agent Bus private configuration, managed worker lifecycle, outbound relay core and one-shot qualification;
- local host-runtime integrity decision model, fixed Linux diagnostic adapter and sanitized hardware/runtime fault evidence;
- fresh fixed autostart runtime smoke plus shared fail-closed activation gating for systemd and managed cron;
- local read-only `runner-mcp autostart preflight` using the same activation decision as installation.

### Changed

- clean Ubuntu install proof now exercises the current installer/runtime integrity path;
- installer/runtime probes classify bounded timeout/native-crash outcomes instead of leaking raw process details;
- self-update wheel staging now preflights offline packaging capability before per-job artifact mutation;
- self-update baseline/bootstrap and distribution identity handling were hardened while preserving the no-dependency compatibility contract;
- Agent Bus is the preferred future runtime-control direction while GitHub mailbox remains a bounded fallback path.

### Security

- autostart cannot persist/enable managed startup unless emergency-stop, recovery, restart-pending, fresh runtime-smoke and host-integrity gates all clear;
- direct systemd/cron installer entry points independently reject missing activation permits;
- host diagnostics remain local-only and expose bounded categories rather than raw journal records;
- Runner Fabric live activation remains gated until its durable service/resume chain is integrated and privately proven.

## 0.1.2 — 2026-09-26

Canonical cross-registry recovery release.

### Distribution and discovery

- corrected the official MCP Registry identity to the case-sensitive `io.github.Blacksp1d3r/runner-mcp`;
- published `aifordable-runner-mcp==0.1.2` to PyPI;
- published matching `0.1.2` metadata to the official MCP Registry;
- created GitHub pre-release `v0.1.2` from exact commit `83175f439c60346f92b5759a90993c3b8f5352f8`;
- aligned public PyPI / MCP Registry / GitHub discovery links.

## 0.1.1 — 2026-09-26

First public PyPI package upload under `aifordable-runner-mcp` while preserving Runner MCP as the product name and `runner-mcp` as the primary CLI.

## 0.1.0 — 2026-09-24

First public alpha release, published as GitHub pre-release `v0.1.0`.

### Added

- security-first self-hosted MCP server foundation;
- allow-listed project registry and safe project file access;
- external operator emergency stop and retention safety policy;
- predefined asynchronous test profiles with bounded scrubbed logs;
- allow-listed staging service controls;
- PostgreSQL backup and migration controls;
- staging-only deployment and one-step code rollback;
- built-in project adapter foundation;
- short-lived local human approval gates for higher-risk staging actions;
- GitHub mailbox bridge protocol with a strict allow-list;
- bounded bridge result envelopes and replay protection;
- strict terminal task-completion events with deterministic notification IDs;
- optional private GitHub-issue completion delivery with bootstrap history cutoff, local delivery deduplication and remote deterministic-marker reconciliation;
- watcher heartbeat, replay lifecycle and fail-closed restart-recovery primitives;
- explicit local missing-result recovery that can publish a terminal safe failure for an already-claimed request without replaying the operational action or resetting watcher state;
- local-only abandonment for strictly valid unclaimed requests and bounded malformed-request quarantine with request-head race protection;
- transport-neutral bridge processor with explicit allow-listed executor and durable-result ordering;
- fixed-host GitHub mailbox transport with strict JSON/base64 validation and create-once results;
- incremental GitHub mailbox watcher with explicit bootstrap and restart-safe cursor reconciliation;
- loopback-only MCP bridge executor with strict JSON/SSE parsing and bounded test polling;
- private-config GitHub watcher runtime and CLI with explicit bootstrap and separate polling/heartbeat cadence;
- secure standard-input token ingestion for mailbox configuration without putting credentials in command-line arguments;
- bounded fair multi-project scheduling with persistent project queues, immediate test job IDs, safe capacity observability and explicit parallel-safe opt-in;
- scale-aware bounded MCP request capacity sized for concurrent mailbox workers and status polling;
- interactive setup, doctor, guide and configuration-management CLI;
- managed non-root autostart for the fixed Runner MCP server and explicitly bootstrapped watcher components, using systemd user services when available and a lock-protected managed cron fallback on headless accounts;
- public CI for this public repository;
- initial umbrella project identity;
- five-minute local demo, release checklist and launch-readiness documentation;
- clean Ubuntu 24.04 / Python 3.12 CI coverage for the documented five-minute demo;
- short per-job private test temporary directories that avoid Unix-domain socket path exhaustion while preserving restrictive permissions and cleanup;
- bounded operational GitHub mailbox actions for scrubbed test logs, configured service control, backups, migration/deployment/rollback planning and approval-bound high-risk execution;
- canonical main-only Runner MCP self-update jobs with fixed lint/unit gates, local no-dependency installation and internal component self-reexec;
- recoverable self-update activation markers that block overlapping updates and preserve pending restart intent when a fixed component re-exec fails;
- private staged self-update wheels with durable install transactions, verified baseline rollback for caught package failures and fail-closed pending-recovery state for unproven interruption;
- bounded local self-update install recovery requiring the emergency stop and restoring only the persisted private baseline wheel/source commit, unavailable through MCP/mailbox control;
- bounded local `status`/`doctor` visibility for self-update install recovery without exposing commits or private artifact paths;
- a fail-fast local release-check wrapper covering compile, Ruff, pytest, whitespace, built-artifact and clean-demo validation while keeping GitHub CI authoritative;
- category-only safe diagnostics for managed cron and completion-watcher failures without leaking private paths or raw exception text;
- terminal deployment/rollback completion delivery with source-scoped idempotency and no task replay;
- privacy-safe connectivity categories and current private-tunnel/reverse-proxy guidance without changing bind, TLS, DNS, firewall, proxy or tunnel state;
- local read-only PostgreSQL restore preflight that validates one private archive without reading the configured DSN, connecting to the database or adding restore execution authority.
- local read-only retention preview that strictly validates private release/backup state and reports protected or potentially eligible records without deletion authority.

### Fixed

- the loopback mailbox executor now accepts the MCP SDK's bounded multi-item text encoding for list-returning tools such as project and test-profile listings, while still rejecting multi-item content for scalar tools;
- the clean demo keeps its temporary project virtual environment outside the repository so local validation cannot delete a developer's `.venv`.

### Security

- arbitrary shell input is not part of the normal MCP or mailbox interfaces;
- unknown MCP arguments fail closed;
- bridge requests/results reject duplicate keys and non-standard JSON constants;
- bridge results are bounded and conservatively scrubbed;
- duplicate mailbox request IDs cannot be silently re-executed;
- notification delivery is separated from task execution so a delivery retry cannot rerun the task;
- ambiguous or missing-result watcher recovery states do not automatically re-execute operational actions;
- malformed historical requests can be quarantined only after all sibling backlog requests are verified durable and the request head is unchanged;
- mailbox operational actions remain fixed-schema: no arbitrary shell, argv, path, environment, systemd unit, MCP tool, approval grant, restore or production mutation is accepted;
- self-update cannot select an arbitrary repository, branch, package-manager command, executable, install path or restart command;
- self-update restart markers are create-once, batch-prepared for the fixed components, and restored after a failed re-exec instead of silently losing activation intent;
- self-update package mutation is preceded by private wheel staging and a strict transaction marker; caught failures roll back only when both package and source restoration are verified, while interrupted/unproven recovery blocks further updates;
- result persistence/finalization failures do not authorize bridge action replay;
- GitHub mailbox transport failures are classified and kept inside the persistence/recovery boundary;
- watcher restarts reuse cursor/replay state and never treat process restart as permission to replay actions;
- bridge execution cannot target a non-loopback MCP endpoint and never fetches test logs;
- GitHub mailbox secrets stay in the private 0600 runtime environment and are preserved across setup overwrite;
- production mutations remain disabled;
- database restore execution remains unimplemented; the local restore preflight is read-only and adds no restore authority.

### Known limitations

- privacy-safe private-tunnel/reverse-proxy guidance is available, but automatic tunnel/TLS/DNS/firewall/proxy provisioning remains operator-managed;
- untrusted public-fork code is not sandboxed for execution on a privileged persistent runner;
- PostgreSQL restore/PITR orchestration and automated retention pruning are not implemented;
- the optional built-in GitHub-issue notifier requires a private destination and GitHub credential; notification transport remains independent from mailbox execution.
- managed-cron removal disables future supervision but deliberately does not blindly terminate an already-running component; immediate local termination remains an operator action.

## Release format

Future releases should move relevant entries from **Unreleased** into a dated version section. Release notes should link to the exact validated tag/commit and call out security-boundary changes explicitly.
