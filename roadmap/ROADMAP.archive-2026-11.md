## 2026-11-07 — #341 hersteltransactie kan andere updater niet meer overschrijven: v0.1.155 SOURCE/CI MERGED

- **ACTUELE HOOFDBRANCH SOURCE**: [PR #964](https://github.com/Blacksp1d3r/runner-mcp/pull/964) exact PR-head `3aac20c8b8425c5fbde2e51fe57335ed2a92b8f3`, guarded squash MERGED `ecb5a52d3b6517c0787cbf2eafa924ca6ffcc2df`; zelfde SHA + versie `0.1.155` en gewijzigde `SelfUpdatePackageInstaller.begin_transaction` op originele GitHub `main` onafhankelijk herlezen. [Validatie 42358658671](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42358658671) all 5 applicable jobs SUCCESS: Ruff/full pytest, echte disposable systemd, releaseversie-reservering, volledige vijfminutendemo, pas daarna immutable PR kandidaat-artifact ID 13568961752; [clean Ubuntu 42358658676](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42358658676) SUCCESS, [commit-attributie 42358658624](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42358658624) SUCCESS. 7/7 CI-controles SUCCESS. Main push validatie [42358919769](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/42358919769) **IN PROGRESS** op laatst gecontroleerd moment; geen terminal claim.
- **OORZAAK/OPLOSSING**: bestaande `begin_transaction` controleerde vooraf op afwezigheid maar gebruikte vervolgens `os.replace`; een tweede updater die tussen die twee stappen zijn herstelinformatie publiceerde, kon overschreven worden. De bestaandezelfde-map-transactie wordt nu atomair met `os.link(..., follow_symlinks=False)` gepubliceerd. `os.link` conflict/ongeschiktheid = FAIL CLOSED zonder `os.replace` fallback. Alleen de eigen .tmp wordt verwijderd; bestaande bestands-`fsync` en oudermap-`fsync` en 0600 blijven behouden. Twee nieuwe negatieve regressies: volledig geldig concurrerend record blijft byte-identiek en een niet-ondersteunde atomic-link faalt zonder nieuwe transactie. Geen tweede updater of scheduler.
- **FYSIEK NIET GEACTIVEERD**: actuele originele host `AF-HOST-0001` Runner-MCP is volgens laatste onafhankelijk fysieke meting 0.1.88, dus nieuwe source-versie 0.1.155 is niet daarop geïnstalleerd. #669 originele ingeladen wheel/source/herkomst, #341 onafhankelijke rollback, Fabric A6 #942, fysiek autonome Black A7 zesrollen-herstel #943/#1650 en echte campagnegebonden oorspronkelijke-client terminal result + durable ACK blijven open. Black bestaande gast UUID, `ephemeral=false`, RUNNING is read-only PASS; dat bewijst géén zesrollenactivering. Claude/Qwen/SQL/producerende diensten en hostprocessen niet gewijzigd. Ed25519 blijft uitgesteld. Issuebewijs [#341](https://github.com/Blacksp1d3r/runner-mcp/issues/341#issuecomment-6704952029).

## 2026-11-07 — #662 0.1.154 automatische artifactpublicatie na demo/isolated systemd (SOURCE KANDIDAAT)

- V0.1.152 uploadde kandidaatartifact `13565557686` terwijl main validation `42351052147` later eindigde CANCELLED in de einddemo. V0.1.153 #962 beschermt lopende main-runs tegen volgende docs-commits (na echte v0.1.153 main-run `42351865566` SUCCESS bewezen). Resterend rechtstreeks bronprobleem: `release-artifact` had in bestaande `validation.yml` alleen `needs: validate`, zodat artifact eerder kon verschijnen dan de volledige demo en systemd-test groen waren.
- Beperkte volgende fix: **dezelfde** release-artifactjob gebruikt `needs: [validate, demo-smoke, disposable-systemd-user]`. Geen extra pipeline, compiler, publicatiesysteem, security-issuer of controller. Eén workflow-test beschermt deze afhankelijkheid. Exacte-head CI/merge nog vereist. On-site #669/#341/A6 #942/A7 #943 en oorspronkelijke client ACK nog WAIT.

## 2026-11-07 — #662 0.1.153 behouden actieve main-release CI (MERGED / live-uitrol WAIT)

- GitHub run `42351052147` v0.1.152 CANCELLED door volgende docs main-commit ondanks bestaande candidate ID `13565557686`; volledige CI-bronrun dus NIET GREEN. [PR #962](https://github.com/Blacksp1d3r/runner-mcp/pull/962) verandert alleen de twee bestaande CI cancellation-instellingen; exact-head **7/7 PASS, 4708 pytest**, MERGED `f79f07e27b5af1d97c7019f298e42c5275af85f9`. Actieve main-validaties worden niet meer door docs-pushes afgebroken; PR-checks mogen nog latest-only. Het aparte geval van superseded **wachtende** GitHub-main-runs is niet hiermee bewezen/uitgesloten.
- **Fysieke uitrol NO:** originele serving-wheel/host #669, startbare rollback #341, owner-source/CI-hostpolicy, A6 #942, onafhankelijke offline A7 #943 en oorspronkelijke-client result+ACK. Geen nieuw releasecontroller/updater of ED key; andere sporen ongemoeid.

## 2026-11-07 — #662 bescherming van autonome main-release CI (0.1.153 BRONKANDIDAAT)

- **Concreet reproducerende blokkade:** Runner-MCP 0.1.152 shipping commit `4155e7f7219139603a167dbaa72abb84694c749b` produceerde artifact id `13565557686` (volgens GitHub officieel), maar main workflow `42351052147` werd CANCELLED terwijl einddemo liep na volgende documentatiepush `5220b3e7097b1ebb480a6d0c7e31461944df874d`. Dit verliest de volledige main-release-CI-acceptatie, ondanks bewezen exact-head PR-tests.
- Bestaande CI-groepen blijven bestaan; alleen `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` in validatie en commit-attributie. Hiermee kunnen PR-verversingen oude runs annuleren, main/source-pushes nooit. Bestaand release-artifact en 30-dagen candidate custody behouden; geen parallelle publisher/daemon, geen productiesleutel. Testcontrole voor beide werkstromen. **PR-head CI/merge nog af te wachten.**
- Fysieke uitrol blijft WAIT: originele host/wheel #669, owner/CI/host-policy, vorige startbare baseline #341, Fabric A6 #942, no-NIC A7 #943, oorspronkelijke-client ACK. ED key pas na werkende auto-updates/Qwen/Claude.

## 2026-11-07 — F30 #341 source 0.1.152 definitief getest en gemerged; fysieke uitrol nog WAIT

- [PR #961](https://github.com/Blacksp1d3r/runner-mcp/pull/961) 7/7 CI groen op head `ef54623fb6062f18b000345eb0ea68750cb4f10e`, **4707 tests PASS**, MERGED `4155e7f7219139603a167dbaa72abb84694c749b`. Hergebruik bestaande ZIP/METADATA/RECORD-controle bij alle lokale stage-statuspaden; een ZIP met mee herberekende SHA256SUMS krijgt niet langer `bundleReady=True`; geen nieuwe updater.
- **Volgende werkelijke blokkades:** onafhankelijke originele `AF-HOST-0001` actieve wheel/zesrollen-generatie #669, owner/CI/source/hostpolicy, behouden startbare rollback #341, Fabric A6 #942 off-target journal en A7 #943 zelfstandige boot/no-NIC herstel, authentieke client result+ACK. Geen fysieke update of nieuwe ED-sleutel vóór bruikbaar automatisch updaten, Qwen en Claude.

## 2026-11-07 — F30 #341 bronkandidaat 0.1.152: stage en readiness hetzelfde lokale wheel-contract

- **Bevestigde broninconsistentie:** v0.1.151 `local_readiness` hercontroleert reeds ZIP/METADATA/RECORD, maar `stage_local_bundle` kon `bundleReady=true` teruggeven over dezelfde op schijf herpinde corrupte wheel doordat de idempotente route en de nieuwe builder beide alleen `SHA256SUMS` herlazen.
- **Beperkte bestaande-functiecorrectie** in `fabric_update.py`: drie `_validated_bootstrap(..., verify_wheel_records=True)` bij opnieuw aangeboden `local-bundles/<commit>`, vóór promotie van een vers gebouwde bundle en na de bestaande atomische NOREPLACE-promotie. Hergebruik bestaande wheelhouse-parser zonder aparte updater, daemon, issuer of controller. Synthetische correctheidstests bestaande+nieuwe stage; exacte PR-head CI vereist. Source versie 0.1.152.
- **Fysieke gates ongewijzigd:** original-host `AF-HOST-0001` 0.1.88 niet independently verified voor geladen wheel #669; host/CI/source-pins, A6 #942, A7 #943 zelfstandige boot/no-network rollback, vorige startbare baseline #341 en oorspronkelijk client result+ACK ontbreken. Qwen, Claude, SQL en servers ongemoeid; ED key later.

## 2026-11-07 — F30/#341 0.1.151 lokale ZIP/RECORD-hercontrole SOURCE VOLTOOID, HOST WAIT

- [Runner-MCP PR #960](https://github.com/Blacksp1d3r/runner-mcp/pull/960) **MERGED** als `22624dbf42c63f6b57d2161eaf88f6050128a6bd`, exacte head `920dcf884b0d00c8149464371f867ca5d19a122e`, CI **7/7 SUCCESS** (4705 pytest, Ruff, version/reservation, schone Ubuntu, gebouwd artifact, geïsoleerde systemd, einddemo, attribution). Bestaande `_wheel_record_check` opnieuw gebruikt bij bestaande lokale readiness/stage/preflight. Negatieve test: valide 5-asset import, daarna wheel EN SHA256SUMS samen aangepast; SHA-only accepteert de bijpassende hash, ZIP/RECORD weigert het pakket.
- Vijf oudere positieve tests gebruikten geen volwaardige wheels; hun testfixtures hebben nu correcte ZIP/METADATA/WHEEL/RECORD. Eerdere gefaalde heads wegens ontbrekende `glama.json`-versie, Ruff importvolgorde en ongeldige fixtures zijn historisch behouden en beschreven in Failure Museum.
- Alleen **bron en geïsoleerde CI VOLTOOID**. Oorspronkelijke `AF-HOST-0001`/gha-runner/:8000 serving wheel/source/generatie #669, onafhankelijke owner/CI/source-policy, behouden startbare rollback #341, Fabric #942 off-target A6, #943 offline no-NIC zesrollen-A7 en echte originele-client result/ACK blijven **GEBLOKKEERD/NIET GETEST**. Geen productie-aanpassing en geen ED-productiesleutel tot auto-updates/Qwen/Claude bruikbaar zijn.

## 2026-11-06 — F30 #341 bronketen tot en met local_readiness geverifieerd

- Source-only automatische Fabric Release-publicatie werkt; Runner-MCP v0.1.149/0.1.150 verifieert keyless exact Release/asset/ZIP/SHA en bewaart in bestaande eigenaar-private flat local-bundles NOREPLACE. #958 heeft definitieve map/mode test, #959 heeft echte bestaande local_readiness + corruptie-fail-closed op synthetische 5/33/160 assets. [#959](https://github.com/Blacksp1d3r/runner-mcp/pull/959) 7/7 exact-head CI SUCCESS (4704 pytest), MERGED `d49940b8e7116b89d1b139b010c5ed72cb50a8e8`; versie 0.1.150 blijft. Local `artifact_ready` is enkel bestandscontrole, NOOIT owner-/install-/rollbackautoriteit.
- **Volgende FYSIEKE afhankelijkheid:** echt geattesteerde originele AF-SVC-0001 serving wheel/process generatie #669; onafhankelijke eigenaar-goedgekeurde source/CI/host-pins; behouden startbare oude release #341; off-target A6 #942, zelfstandige offline A7 #943, oorspronkelijke client terminal result/ACK. Alleen dan gecontroleerde first-node en eventueel automatisch uitrollen via de bestaande Fabric Update Plane #924. Geen parallel infra, geen ongeteste `start_local/apply`.
- ED productsleutel uitgesteld tot werkende automatische updates én bruikbaar Qwen en Claude; bronwerk op gescheiden werksporen blijft toegestaan.

## 2026-11-06 — F30 #341 volgende veilige schakel: GitHub-inactieve custody → bestaande local_readiness

- Runner-MCP [PR #958](https://github.com/Blacksp1d3r/runner-mcp/pull/958) is **gemerged** `c9162aedab64a92c291c9847a9ccce5677505944`, met exact-head 7/7 CI groen en post-merge Validation/Attribution SUCCESS. Finale `local-bundles/<SHA>/<asset>` is VLAK door bestaande atomaire `source/bundle`-promotie; voorheen foutieve nested-eindmaphypothese expliciet gecorrigeerd.
- NIEUWE TEST-KANDIDAAT: bestaande private `_stage_github_release_inactive_once` (fictieve 5/33/160 SHA/assetrelease) en gewone `FabricUpdateManager.local_readiness` worden in dezelfde `pytest-tmp_path` getest. Het eerste codepad mag alleen bewaring claimen; het tweede mag alleen lokaal gevalideerde bytes lezen, zonder `preflight/apply/start_local`. Na opslag gewijzigde BOOTSTRAP/wheel/manifest moet expliciet falen. Test/docs only: versie blijft 0.1.150, CI nog af te wachten.
- Deze ketentest is GEEN productieinstallatie. Vereist blijven oorspronkelijke host/process/installed wheel #669, eigenaar-/CI-bronbeleid, A6 #942 off-target journaal, onafhankelijk A7 #943 / #341 lokale herstelproef en echte originele-client-result+ACK. ED owner signer pas na auto-updates, bruikbaar Qwen en Claude.

## 2026-11-06 — F30 #341 tijdelijk genest / definitief vlak bewaarpad verduidelijkt

- Bij GitHub-release-inactieve custody gebruikt de bestaande manager `.incoming-<uuid>/source/bundle/<asset>` als PRIVATE tijdelijke werkboom; de al bestaande `_promote_inactive_bundle_noreplace` promoveert precies `source/bundle` atomair als vlakke `local-bundles/<commit>/<asset>`-bestemming. De tests controleren finale bytes, 0700/0600, NOREPLACE en geen dubbele assetkopie in de bewaarde tijdelijke boom.
- Een structureel leesbare inactieve bundel is slechts opslaggereed, GEEN installatiebevoegdheid. De ontbrekende originele host/proces/wheel #669, rollout/herstel #341, Fabric off-target A6 #942, onafhankelijk offline A7 #943 en werkelijke original-client result/ACK blijven noodzakelijke gates. ED key pas na automatische updates/Qwen/Claude.
- Eerste PR #958 head testte ten onrechte geneste FINALE structuur en faalde 4/4698 tests. Herstelde head nog via officiële exacte-head CI valideren; geen wijziging aan live servers of updater.

## 2026-11-06 — F30/#341 0.1.150 GitHub Release → bestaande inactieve custody, ED pas later

- Releasepublicatie Fabric #924 operationeel met 33 assets; Runner-MCP 0.1.149 verifieert vaste GitHub Release/tag+assetbytes zonder ED key. Deze kandidaat 0.1.150 hergebruikt dezelfde transport en de AL BESTAANDE signed-custody NOREPLACE opslag voor de keyless CI-bundel, alleen inactief. Geen kopie/parallel downloader/daemon/installer.
- Volgende echte operationele koppeling: owner-goedgekeurde repository/commit/CI-source-acceptance en originele host/wheel-attest #669, + bestaande A7 offline watchdog met duurzaam gewapende autonome rollback #341/#943 en off-target A6 #942; vervolgens werkelijke end-to-end original client resultaat en ACK vóór commit. Geen apply/start/hostupdate op basis van een onbetrouwbare GitHub hash alleen.
- Binding volgorde: volledige automatische updates; Qwen gebruiken; Claude gebruiken; pas daarna optioneel ED25519 keybeleid. Onderlinge onafhankelijke bronwerkstromen hoeven niet stil te staan.

## 2026-11-06 — F30/#341 S3 GitHub provider-integrity source WITHOUT Ed25519 owner key

- Real Fabric automatic CI-release pipeline already published 33 assets for exact main 2b62cd5c1305433b04f0c5eaca16c86a20ec18e0, GitHub release ID 436869142. 0.1.149 source-only private Runner-MCP route reuses existing fixed-repository tag/Release admission, asset-ID HTTPS transport and complete SHA256/BUNDLE/ZIP/RECORD verifier for non-Ed CI releases.
- NO fresh signer, new publisher, service, or install authority. Next is to qualify this byte path with owner-approved fixed source/release CI policy and original host #669, only then reuse existing owner-private INACTIVE local-bundles stage. Actual apply requires retained baseline + independently installed A7 offline rollback, A6 off-target journal and same original-client result plus ACK.
- Binding priority: automatic updates operational FIRST, Qwen usable SECOND, Claude usable THIRD, independent ED25519 key/rotation optional FOURTH. No signing hard block while these three workstreams progress.

## 2026-11-06 — F30 #937 v0.1.148 private signed Release end-to-end source closure

- Exacte onafhankelijke owner-pins → onbetrouwbare GitHub Release/body + tagref → bestaande Ed25519/assetbytes/manifest/wheel-verifier → owner-private create-once INACTIEVE NOREPLACE custody is als **private code**, met synthetische tests, doorverbonden; geen publieke tool, install, restart of rollback.
- S3 fysieke uitrol moet blijven wachten op echte onafhankelijke signer/trust, automatische ondertekende publicatie in Fabric #924, originele Runner-MCP #669 + #341 herstelsupervisor, Fabric fysieke A6 #942/A7 #943 en originele geauthenticeerde result/ACK. Nooit een geteste codeketen verwarren met een uitrol op de werkelijke machine.

## 2026-11-06 — F30 #937 source-only gesloten signed Release-body → bestaande manager-verificatie

- Interne manager-route gebruikt één vaste Release/tag-snapshot plus signed description, valideert onafhankelijke key-/commit-/releasepin en hergebruikt volledige bestaande pinned assetbytes-verificatie in geheugen. Geen aparte downloader, updateservice of publieke tool.
- Productie nog niet vrijgegeven: eigenaarssigner/rotatie en onafhankelijke trustdistributie plus daadwerkelijk ondertekende releasepublicatie via Fabric #924 ontbreken, evenals originele runtime #669, herstelsupervisor #341, A6/A7 fysieke bewijsstukken en authentieke result/ACK. Nooit een groene CI als bewijs voor productie-activering beschouwen.

## 2026-11-06 — F30 #937 signed description consumer 0.1.146, source-only

- De generieke Ed25519 signed roster kan als strikt eindblok worden afgenomen uit de bestaande releasebeschrijving zonder de vaste GitHub assetlijst te vergroten. Alleen synthetisch en onbereikbaar vanuit publieke MCP-tools; sleutel, commit en release-ID komen van buiten GitHub/aanroeper.
- Nog nodig: daadwerkelijke owner-managed Fabric signing/rotatie, onafhankelijke public key-trust, publicatie/durable distributie door bestaande Fabric workflow buiten de 5..160 assets, oorspronkelijke doelhost/wheel #669, fysieke recovery A6/A7, resultaat/ACK. Niet activeren bij onzekerheid.

## 2026-11-06 — F30 #937 S2e bronkandidaat 0.1.145: offline signed inactive storage

- Hergebruik 0.1.144 in-memory signed verifiers, Q7 private root-FD en bestaande atomic NOREPLACE onder lokale private update-root. Voeg uitsluitend source-only private offline stage toe met 5/33 synthetische wheel-tests, race en crashfailures.
- Publicatie-, owner- en fysieke hostbevoegdheid ontbreken, dus GEEN echte releaseimport of live update. Fabric #924 signing authority, #669/#341 en A6 #942/A7 #943 + ACK blijven harde gates. Geen invloed op Claude/Qwen.

## 2026-11-06 — F30 #937 S2 bronketen 0.1.144 compleet in tests, S2d signer WAIT

- 0.1.144 [Runner-MCP PR #946](https://github.com/Blacksp1d3r/runner-mcp/pull/946) MERGED `86e63ad461e687c7d9f9176bd4cb10c96eef0fc3`, exact CI Validation `42240506433`, Clean Ubuntu `42240506547`, Attribution `42240506486` SUCCESS. Bestaande interne manager `_read_exact_release_admission` en bestaande signed `fetch_exact_signed_fabric_bundle_bytes` zijn met extra vroege signed-rostercheck in één niet-geëxporteerd codepad getest. Full manifest/SHA/ZIP/RECORD en falsificatietests PASS; geen nieuwe controller, updater, API-route of echte mutatie.
- **Volgende voorwaarde buiten Runner-MCP:** Fabric #924/eigenaar levert waarlijk onafhankelijke generieke releaseondertekening en trusted key/source/release-ID, daarna origineel host- en eigenaargebonden inactieve safe custody, vervolgens #669/#341/A6 #942/A7 #943 + client result/ACK. Tot die tijd geen `start_local/apply` en geen nieuwe officiële host-acties. Claude en Qwen V3 parallel onaangeraakt.

## 2026-11-06 — F30 #937 0.1.144 bronkandidaat: bestaande manager full chain slechts intern koppelen

- Bestaande `FabricUpdateManager._read_exact_release_admission` en vaste assetbyte-batch 0.1.142 nu uitsluitend intern in `_read_verified_signed_release_bytes` gekoppeld, met vroege Ed25519/commit/release-ID preflight. Geen tweede API, geen nieuwe publisher/signing key, geen stage/apply, geen nieuwe tool, cron/daemon of beïnvloeding van Claude/Qwen. Synthetische object-standalone manager-tests op 2 exacte metadata endpoints, volledige 5/33 wheel ZIP/RECORD-validatie, verboden extra API, fail-closed vóór download.
- Volgende stap na volledige CI: Fabric #924 moet **werkelijke** onafhankelijke eigenaarssigner/pins en releasebron leveren. Daarna echte assettransport op exact bekende originele host/owner + owner-private inactieve create-once local-bundles; pas voor automatische activatie de fysieke #669/#341, A6 #942/A7 #943 en oorspronkelijke client-result/ACK verifiëren.

## 2026-11-06 — F30 #937 0.1.142 + 0.1.143 SOURCE GREEN; upstream signer/physical owner WAIT

- Runner-MCP [#944](https://github.com/Blacksp1d3r/runner-mcp/pull/944) source 0.1.142 en [#945](https://github.com/Blacksp1d3r/runner-mcp/pull/945) source 0.1.143 beide MERGED met exact-head full CI PASS. De huidige vaste assetbyte-downloader + signed/full/ZIP-verifiers vormen een pure in-memory 5..160 asset-verificatieketen; de bestaande vaste Release/tag-metadatalezer biedt exact hetzelfde getypeerde `ReleaseAdmission` intern aan, zonder tweede API/tokenroute. Geen verandering aan servers of bestaande Q7-contracten.
- **Blokkerende externe prerequisite:** onafhankelijke eigenaar/Fabric-gekwalificeerde generieke Ed25519 uitgeverssleutel/owner key pin en getekend `runner-fabric/signed-release-roster/v1`; pas na eigen key/source/release-ID beleid en echte releasebytes kandidaat voor INACTIEVE eigenaar-private NOREPLACE custody op de werkelijk bewezen oorspronkelijke host. `start_local/apply` is geen pre-stage. Fysieke #669/#341 en Fabric #924/A6 #942/A7 #943 + originele issuer terminal result/ACK blijven te kwalificeren.

## 2026-11-06 — F30 #937 exact ReleaseAdmission hergebruiken, zonder dubbele API-implementatie

- Na bron-merge 0.1.142 generieke in-memory assetbatch: 0.1.143 kandidaat verplaatst enkel de bestaande `release_assets_readiness` interne exacte API-parser naar `_read_exact_release_admission`. De bestaande status gebruikt dezelfde getypeerde parser; geen nieuwe endpoint of auth, geen download/stage/apply, oorspronkelijke Q7 en Release foutcodes blijven intact. CI-regressies op identiteit, aantal metadata-GETs, public_dict, verboden mutatie.
- Volgende veilige blokkade blijft onder Fab #924: onafhankelijke eigenaarssigner + release-ID/source/key-policy daadwerkelijk leveren en generiek signed roster publiceren, daarna pas exact bytes over bestaande batch naar eigenaar-private INACTIEVE custody op fysiek aangetoonde doelserver. Originele #669/#341/A6/A7/ACK moeten voor live update klaar zijn.

## 2026-11-06 — F30 #937 S2e: signed assetbytes op bestaand transport (0.1.142 kandidaat)

- Voeg binnen de al bestaande `fabric_release_asset_bytes.py` een begrensde full-batch-ingang toe: eerst onafhankelijk *aangeleverde* exacte signer/bron/release-ID + gematchte Release/tag metadata, dan per file de huidige pinned downloader, na iedere GET onafhankelijke grootte/digest, en op het einde bestaande full manifest + ZIP/RECORD-verifier. Geen nieuw transport, tokenroute, storage/installer en Q7 ongewijzigd. CI synthetisch met gemockte reader, 5/33/160 items, negatieve ondertekening en verkeerde bytes.
- **Gaat NIET naar productie:** bronvoorbereiding kwalificeert nog niet de origineel door eigenaar/Fabric beheerde signer of signature-uitgever; echte published roster ontbreekt. Na onafhankelijke signerbron de eerste echte download en uitsluitend lokale INACTIEVE create-once custody onder de bewezen originele eigenaar, dan fysiek #669/#341/A6/A7/ACK. `start_local/apply` blijft verboden als pre-stage.

## 2026-11-06 — F30 #937 S2e bestaande inactieve local-bundles stage: racefix MERGED 0.1.141

- [Runner-MCP PR #942](https://github.com/Blacksp1d3r/runner-mcp/pull/942) `ebe687b75c1ed7a2979966a43e0fb7e3a97c032f`, source 0.1.141, exact-head full CI `42221040779` / clean Ubuntu `42221041071` / attribution `42221041052` SUCCESS. Hergebruik van bestaande Q7 `renameat2(RENAME_NOREPLACE)` voor de al bestaande `stage_local_bundle`; geen gelijktijdige overschrijving van inactieve `local-bundles/<commit>` meer. Geen tweede updater, geen actie op Qwen/Claude. Failure Museum in bestaande folder.
- **Nog OPEN:** onafhankelijke generieke issuer-key/owner-pin en werkelijk ondertekend `runner-fabric/signed-release-roster/v1` vanuit Fabric #924; echte exact gepinde byte-download koppelen aan inactieve custody zonder nieuwe admin-/authroute; geen `start_local/apply` voordat #669/#341 + A6 #942/A7 #943 plus originele client-result/ACK fysiek bewezen zijn. Een lokale bronbuildstage is niet dezelfde authority als een gesigneerde GitHub Release-installatie.

## 2026-11-06 — F30 S2 #937: drie bronmijlpalen MERGED, inactieve custody blijft OPEN

- **SOURCE/CI VOLTOOID:** 0.1.138 [#939](https://github.com/Blacksp1d3r/runner-mcp/pull/939) onafhankelijke ondertekening+SHA-pins; 0.1.139 [#940](https://github.com/Blacksp1d3r/runner-mcp/pull/940) gedeelde Q7/generic volledige asset- en manifestintegriteit; 0.1.140 [#941](https://github.com/Blacksp1d3r/runner-mcp/pull/941) gedeelde ZIP/METADATA/RECORD wheel-inhoud. Exacte-head Validation, Ubuntu en Attributie voor alle drie SUCCESS. Bestaande Q7 contracten behouden.
- **S2d/e GEBLOKKEERD/OPEN:** eerst onafhankelijke generieke Fabric-signer/owner key en bron/release-ID/hostbevoegdheid bewijzen; dan echte releasebyte-download in bestaande verifier en create-once opslag uitsluitend onder bestaande inactieve `local-bundles/<commit>`, geen overschrijven van `bundle/` en geen `start_local/apply`.
- **S3 FYSIEK OPEN:** #669 actuele serving process/wheel, #341 echte lokale recovery, Fabric #924 compat/lease, onafhankelijke A6 #942, offline A7 #943 en originele actor result+ACK vóór productieactivatie. Bron 0.1.140 ≠ verbonden productie 0.1.88.

## 2026-11-06 — #937 S2c generieke Python-wheels verifiëren vóór inactieve opslag

- Bron 0.1.140 kandidaat: dezelfde ZIP/Metadata/RECORD-parser gebruikt voor vaste Q7 en toekomstige exact ondertekende generieke Fabric-bundels; eerst signed roster + volledige manifest/SHA, daarna wheelinhoud. Synthetische 5/33/160 asset- en fouttests plus volledige CI verplicht.
- Resterend: werkelijk onafhankelijk geautoriseerde signer/rooster gepubliceerd door Fabric #924, daarna vaste byteimport en inactieve `local-bundles/<commit>`-custody, echte host/provenance en A6/A7/original-client ACK vóór activatie. Geen nieuwe updater of tweede wheel-parser.

## 2026-11-06 — #937 S2b: Q7 en generieke bundle-inhoud via één codepad

- **SOURCE kandidaat 0.1.139:** na gemergde 0.1.138 signed-pins wordt `fabric_release_full_bundle` gedeeld voor 5..160 bestanden, exacte SHA256SUMS/BUNDLE/COMMIT, met oude Q7-interface vastgehouden op 33/33. Volledige CI en negatieve tests vereist vóór merge.
- **VOLGENDE S2 stappen:** bestaande ZIP/RECORD wheelhouse-verificatie uitbreiden zonder aparte uploader, vervolgens eerst onafhankelijke echte issuer/signer-pins en real-host custody respecteren voor exact `local-bundles/<sha>` create-once. `start_local` is een echte update/apply, geen stage. Rollout blijft Fabric #924/#942/#943 en #669/#341 fysieke herstel-/ACK-gates.

## 2026-11-06 — F30 S2a #937: generiek ondertekende Release-inventaris (bron kandidaat)

- Nieuwe source 0.1.138 module: pure Ed25519- en exacte Fabric SHA/release-ID/publisher-schemacontrole, hergebruikt bestaande `inspect_exact_release`; vergelijking met aparte GitHub metadata blijft niet-autoriserend. Historische Q7-import niet aangepast.
- S2a acceptatie = volledige exacte-head CI en geen I/O of servermutatie. S2b blijft afhankelijk van een **echt onafhankelijk door Fabric/eigenaar gekwalificeerd signer- en bronpincontract**; daarna bestaande assetbyteverificatie en bestaande owner-private inactieve custody hergebruiken. Geen extra updater/scheduler en geen install/rollback totdat #669, #341, Fabric #924/#942/#943 en originele actor-ACK fysiek bewezen zijn.

## 2026-11-06 — F30 releasecontrolemijlpaal: #934 en #936 SOURCE MERGED; #937 volgende stage

- [#934](https://github.com/Blacksp1d3r/runner-mcp/pull/934) v0.1.136 reuse bestaande exacte GitHub Release-readiness wanneer Actions `actions_run_unavailable` meldt, zonder het oorspronkelijke blocked/install-authority-resultaat te wijzigen. [#935](https://github.com/Blacksp1d3r/runner-mcp/pull/935) handover gemerged.
- [#936](https://github.com/Blacksp1d3r/runner-mcp/pull/936) v0.1.137 bron MERGED: `release_not_published` na twee vaste 404's; `release_provider_unavailable` bij providerstoring; `release_digest_invalid` bij ongeldige SHA-256-assetmetadata; incomplete release/tag blijft unqualified. Finale CI 42206013659/42206013610/42206013606 all SUCCESS. Alleen read-only diagnose, geen serverdownload/install/rollback.
- Nieuwe kleine kindtaak [#937](https://github.com/Blacksp1d3r/runner-mcp/issues/937): bestaande #739 Q7-asset-byte-verifier/signer/private custody alleen veilig hergebruiken voor toekomstige volledige release-set als onafhankelijke generieke signer/roster/host-pin bewezen is. Eerst inactieve exacte bestaande local-custody, dan afzonderlijk #341/ Fabric #924/A6 #942/A7 #943 operationeel kwalificeren. Als signer of fysieke hostprovenance onbekend: WAIT, niet stilzwijgend activeren.

