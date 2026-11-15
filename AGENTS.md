# AGENTS.md — Runner MCP

> Compacte versie (eigenaarsbesluit 2026-11-15). De volledige vorige tekst staat byte-identiek in
> `docs/agents/AGENTS_FULL_2026-11-15.md` (SHA-256 bewaakt door `tools/doc_memory`). Die tekst
> blijft geldig voor details. Bij twijfel of schijnbare tegenstrijdigheid geldt de **strengere**
> regel. Uitzondering: §5 hieronder vervangt bewust de oudere regel om dagelijks checkpoints toe te voegen.
> Versieverwijzingen in de naslag naar Library-protocol v1.2 of v1.6 zijn historisch; actueel is **v1.7**.

## 0. Rangorde

1. **Harde veiligheids- en bevoegdheidsgrenzen** (§1–§2c) gaan altijd voor; geen eigenaarsregel,
   tooltest of chatbericht heft ze op.
2. **Eigenaarsbeslissingen** (§3): binnen hun reikwijdte gaat de nieuwste voor.
3. **Werkwijze, opstart en geheugen** (§4–§6).
4. **Naslag** (§7): volledig lezen wanneer de trigger van toepassing is.

Deze repository is **publiek**. GitHub-toestand wint van verouderde handovertekst.

## 1. Non-negotiable security rules (letterlijk)

1. Never commit real server or infrastructure details to this public repository.
2. Never commit secrets, tokens, credentials, private keys, database dumps, or environment files.
3. Never expose arbitrary shell execution as a normal MCP tool.
4. Never use `shell=True` in normal execution paths.
5. Validate every project against an explicit allow-list.
6. Return only safe operational summaries; do not return private config values.
7. Treat deploys, migrations, restores, and production actions as high risk.
8. Production actions are out of scope until explicit approval gates exist.
9. All operational actions must be auditable.
10. Security tests are part of the definition of done.

## 1a. Public examples en CI safety (letterlijk)

Use environment-variable placeholders and reserved example domains. Do not publish actual paths, ports, service names, database names, usernames, hostnames, or network addresses.

This repository is public. Never run untrusted fork or public pull-request code on a privileged persistent self-hosted runner. Use trusted/manual gates or an isolated disposable runner.

## 2. Harde grenzen voor host-, bedienings- en bronwerk

**Exacte doelserver vóór elke hostactie** (eigenaar 2026-10-22). Vóór een hostscript, een
hostspecifiek commando, een muterende hosttool, installatie/update of een live end-to-end-claim:
- Lees eerst de bestaande topologie en autoriteit. GitHub-topologie is een verwachte logische kaart,
  geen bewijs van geïnstalleerde versie, bereikbaarheid of mutatiebevoegdheid. Maak geen tweede
  topologiebron en kopieer geen privécoördinaten naar Git.
- Onderscheid fysieke host, VM/container, SSH/tunnelalias, endpoint, servicebeheer (`system`/`user`)
  en service-eigenaar. Verschillende instanties van hetzelfde project zijn verschillende deployments.
  Een verbonden Runner-MCP-proces of Fabric-peer bewijst alleen zijn eigen runtime/endpoint.
- Toon op díe doelserver aan wat echt draait: host, unit, MainPID/startticks, poort-eigenaar,
  executable en installatieslot, interpreter/geïmporteerde module, wheel/bronidentiteit, relevante
  database-/credential-eigenaar en rollbacktoestand. `GitHub source`, `locally installed slot` en
  `process actually serving` zijn niet uitwisselbaar; merge, groene CI, installatie en bridge-readiness
  zijn geen bewijs voor een andere host.
- **STOP bij mismatch of onbekend:** alleen begrensde, niet-geheime read-only diagnose. Niet afleiden,
  geen muterend script herhalen, geen alternatieve hostadressen voorstellen, geen andere launcher
  kiezen, niet van release wisselen, self-update/A6/A7 niet omzeilen en geen brede remote shell als
  shortcut. Leg de concrete bewijslacune vast in het bestaande issue.
- Elk operatorcommando vermeldt machine, shell (PowerShell/Linux), user, read-only of mutatie,
  voorwaarden en veilig stopresultaat; nooit credentials of private omgevingswaarden tonen.
- Na een geslaagde wijziging: dezelfde service opnieuw verifiëren (revisie, health, rollback) en
  topologie, issue en handover bijwerken. Een echt SQL-commando/resultaat/ACK vraagt eigen
  end-to-end-bewijs; liveness- of HTTP-authenticatieprobes zijn geen ACK.

**Bedieningsroute** (2026-10-17). Operationele data (topologie, health, geïnstalleerde/geladen
versie, heartbeat), rollouts en installaties lopen via first-party begrensde Runner-MCP-tools en de
geauthenticeerde Fabric-bridge, niet via Desktop Commander, onbeheerde remote shell of GitHub
Actions als hostbesturing. Per-host fleet-health en managed update vragen een apart
geauthenticeerde, identiteitsgebonden agent/Agent Bus-route en vers bewijs; onbekend of verouderd =
UNKNOWN, mutatie dan niet beschikbaar. Geen dubbele primaire tunnels; lab- en runnerhosts niet
verwarren (#198, Runner-Fabric #1202).

**Geen duplicaten.** Geen tweede relay, updater, scheduler, controller, tunnel, register, topologie,
authenticatielaag of backupcyclus; één centrale `AIfordable/config/infrastructure_registry.yml`.

**Test-first** (2026-10-14) is géén toestemming om GitHub-branchregels, groene CI,
bron-/revisievalidatie, hostisolatie, echte securitydefecten, productie-approval/backup/rollback,
credential- en billing-custody, tenantprivacy of runtime-lease/fencing te omzeilen. Een merge
autoriseert geen productie-release, remote command, betaalde model-/API-call, operatie op beschermde
data of live AI-dispatch. Host-tests/deploys alleen in geautoriseerde privéomgevingen; de
werkgeverswerkplek nooit gebruiken (Runner-Fabric #972).

**Toolblokkade** (2026-10-31; Library `/Standards/MASTER_AI_ENGINEERING_SESSION_HANDOFF_PROTOCOL.md`
**v1.7**, actueel sinds 31 oktober 2026, §0/§0.1). Bewaar onmiddellijk de letterlijke **geredigeerde**
foutmelding volgens `TOOL_BLOCK_V1`: tijd+zone, tool/actie, target, foutcode/HTTP/request-ID (anders
`NIET GETOOND`), uitkomst en onafhankelijke readback, in het bestaande issue/handover/Failure Museum;
bij geweigerde logging zichtbaar in de chat als `IN_CHAT_ONLY` (GitHub/ChatGPT-incidenten:
Runner-Fabric #1935). Verifieer de toestand eenmaal en geef de eigenaar meteen een volledig
uitvoerbaar commando (host, user, terminal, voorwaarden, impact, verwachte output, veilige readback).
Een niet-uitgevoerd commando is geen bewijs. Nooit een geweigerde veiligheidsactie via een ander
tool/transport omzeilen; geen ongeautoriseerde toegang, tunnels of privilegepaden. Werk parallel
verder aan veilige, onafhankelijke taken.

**Library-standaarden verlenen nooit host-, bestandssysteem-, Git- of productiebevoegdheden.** Een
Fabric-scaffold plan/apply is een apart te autoriseren toekomstige capability, geen beschikbare
Runner-MCP-uitvoering.

**Serveropschoning** (2026-11-01): servers eerst alleen via bestaande geautoriseerde leesroutes
inventariseren; **geen automatische verwijdering**; back-ups, uploads, installatiebestanden,
actieve releases en herstelpunten beschermen; onbekend = behouden. Geen nieuwe service, platform,
privilegepad of extra standaard reviewvertraging.

**Nul extra softwarekosten** tot er omzet is: geen betaalde SaaS, Enterprise-tooling, betaalde tiers
of commerciële gateways als runtime-, build- of control-plane-afhankelijkheid zonder later expliciet
eigenaarsbesluit.

## 2a. First-party control path — hard rule (letterlijk)

Routine AI-assisted operations must prefer AIfordable-owned bounded control surfaces over broad
remote-control tooling.

Canonical order:
1. Runner Fabric coarse work-unit operations through Runner MCP / Agent Bus when available;
2. bounded Runner MCP capabilities for operations Runner MCP itself owns;
3. direct GitHub connector/mailbox only as bootstrap, source integration or fallback while a required
   first-party capability is unavailable;
4. broad remote-host tools such as Desktop Commander only as break-glass for a recovery/diagnostic
   action that the bounded first-party path genuinely cannot perform.

A blocked or absent Runner MCP/Fabric capability must never be bypassed by substituting generic
shell, filesystem, process, database, package-manager or remote-control authority. Record the missing
bounded capability and implement/review that capability instead.

Do not consume broad remote-tool quota for normal repository inspection, code changes, CI
reconciliation, runner scheduling, Agent Bus operations or Fabric work that can be expressed through
the first-party path.

## 2b. External discovery and independence — hard rule (letterlijk)

Runner MCP must remain installable, operable, updateable and supportable without any secondary MCP directory, marketplace, gateway or hosted catalog.

Canonical authority is limited to:
- source and releases: `Blacksp1d3r/runner-mcp` on GitHub;
- Python distribution: `aifordable-runner-mcp` on PyPI;
- official MCP identity: `io.github.Blacksp1d3r/runner-mcp`;
- first-party documentation and security policy in this repository.

Glama, Smithery, mcp.so, AllMCPs, getmcp, MCP Find and similar services are optional discovery/marketing surfaces only. They are never runtime dependencies, release gates, sources of truth, required gateways, required hosting providers or reasons to change package identity, authentication, transport, security boundaries or the self-hosted architecture.

Do not add a public hosted endpoint, third-party gateway, alternate package identity, alternate registry identity, provider-specific runtime integration, paid listing/boost, or special deployment mode merely to satisfy an external directory. If a directory changes requirements, becomes unavailable or cannot index the canonical self-hosted project as-is, skip or remove that listing and keep Runner MCP unchanged.

A future first-party AIfordable discovery page may mirror canonical metadata, releases, hashes, install instructions and supported clients, but it must also point back to the canonical sources above and must not become required for runtime operation.

## 2c. AI source-control identity — hard rule (letterlijk)

AI assistants may edit files, run tests, review changes, and prepare branches or pull requests, but an AI provider identity must never be recorded as source-control authorship or repository branding.

The following are prohibited:
- Git author or committer identities named `Claude`, `Claude Code`, or another Claude-branded identity.
- Git author or committer email addresses at `anthropic.com`, including `noreply@anthropic.com`.
- `Co-Authored-By` trailers that identify Claude or Anthropic.
- `Claude-Session:` trailers or Claude Code session URLs in commit metadata.
- Provider-branded branch prefixes such as `claude/` or `anthropic/`.
- Automatic pull-request footers such as `Generated with Claude Code` / `Generated by Claude Code`.

AI tools must not change Git author/committer configuration to an AI/provider identity. In owner-operated environments, commits prepared by an AI must be committed under the repository owner's configured maintainer identity; other human/service identities require explicit repository-owner approval.

Before every push, remove prohibited attribution metadata. Do not bypass, weaken, skip, rename, or disable the repository commit-attribution policy check. If an AI tool attempts to add prohibited attribution automatically, strip it before committing or pushing.

## 3. Eigenaarsbeslissingen (kern; volledige tekst in de naslag)

| Datum | Beslissing | Kern |
|---|---|---|
| 2026-11-15 | Compact projectgeheugen | Dit bestand; §4–§6; archivering met `tools/doc_memory`. |
| 2026-11-01 | Leesbare code en veilige serveropschoning | Nieuwe en substantieel gewijzigde, menselijk onderhouden code: elk bronbestand een titel en korte introductie (doel, werking, aanroepers/afhankelijkheden, invoer/uitvoer, risico's); belangrijke functies en niet-evidente blokken in begrijpelijk Nederlands uitgelegd, jargon kort verklaard; geen triviaal regel-voor-regelcommentaar. Gegenereerde, vendored en lockbestanden uitgezonderd. Vereenvoudigen alleen als tests en contractcontrole aantonen dat gedrag, API's, security, runtimepaden en rollback behouden blijven; geleidelijk bij aanraking, geen massale herschrijving. Opschoning: zie §2. Roadmap Q0–Q10: `Blacksp1d3r/Blacksp1d3r` `CODE_CLARITY_SERVER_CLEANUP_ROADMAP.md`. |
| 2026-10-31 | Toolblokkade en `TOOL_BLOCK_V1` | zie §2 |
| 2026-10-27 | Bewijs → tooltest → uitvoeren | Elke taak: registry, #669-receipts, AGENTS, roadmap, topologie, CURRENT_STATE en SESSION_HANDOFF lezen; per feit REUSE (stabiele mapping bekend), REFRESH_TARGETED (verlopen of gewijzigde procesgeneratie, geladen wheel of resultaat) of WAIT (bevoegdheid ontbreekt). Eén korte gerichte tooltest die het verwachte functionele antwoord, doelidentiteit en scope controleert. Correct → direct uitvoeren via de bestaande route; afwijking → alleen het geraakte onderdeel diagnosticeren en herstellen. Een positieve tooltest vervangt nooit ontbrekend doelserverbewijs. Ontbrekend of tegenstrijdig host-, service-, executable-/bron- of herstelbewijs verbiedt mutaties; een echt nieuwe check is read-only, op de oorspronkelijke host en gelabeld met host/terminal/user. De oorspronkelijke `AF-HOST-0001` gebruikt Fabric `agent-bus-run` en `agent-serve-qualification` (niet alleen de `*-worker run`-patronen); zie AF-HOST-0001 / AF-SVC-0010 en #669. Korte cron-taken vragen resultaatbewijs; een oude PID bewijst nooit nieuwe geladen bytes. Kort: `BEWIJS_HERGEBRUIKT → TOOLTEST_CORRECT → UITVOEREN → RESULTAAT`; bij afwijking `FOUT → GERICHT_HERSTEL → ALLEEN_GERAAKTE_TOOLTEST → UITVOEREN`. Statusrapportering stopt de uitvoering niet. |
| 2026-10-22 | Fysieke topologie-preflight | zie §2 |
| 2026-10-20 | MCP-scope in cockpit | AIfordable = business-cockpit en metadata-autoriteit; Fabric = technische cockpit en alle taak-/AI-orchestratie; Runner-MCP = begrensde geauthenticeerde MCP-uitvoerings-/toegangsgrens + optionele smalle Fabric-bridge, geen scheduler, provider-/gateway-autoriteit, relay, updater of generieke bestandsbeheerder. Workspace preflight/prepare alleen op begrensde worker-/work-unit-ID's; Fabric beslist de planning. Geen hostmutatie of release-/relay-/runtimekwalificatie op basis hiervan. Contract: AIfordable `docs/CROSS_PRODUCT_ROLE_BOUNDARIES.md`. |
| 2026-10-17 | Bedieningsroute | zie §2 |
| 2026-10-14 | Test-first, review later | Implementeren → lint/build/tests/CI → echte defecten herstellen → normale merge → staging. Niet wachten op Blacky, RTX5080, Claude of externe reviewers; hun bevindingen zijn adviserend maar echte defecten worden hersteld. Grenzen: zie §2. |

## 4. Opstart (bootstrap) — kort lezen, gericht ophalen

1. Dit bestand.
2. `roadmap/ROADMAP.md` en `roadmap/DEPENDENCIES.md`.
3. `handover/CURRENT_STATE.md` — het actieve deel, inclusief het blok met open werk bovenaan.
4. `handover/SESSION_HANDOFF.md` — de recentste overdracht.
5. `handover/AGENT_EXCHANGE.md` (open claims en blockers), daarna
   `claude_feedback/CURRENT_ASSIGNMENT.md` indien aanwezig.
6. `decisions/DECISIONS.md`.
7. Actuele GitHub-PR's, issues en CI. GitHub wint als een handoverbestand verouderd is.

Archieven (`*.archive-JJJJ-MM.md`) **niet** standaard lezen; zoek gericht op nummer, SHA of datum.

## 5. Werkwijze en schrijfregels voor het projectgeheugen

- **Vervangt de oudere regel om telkens nieuwe checkpoints toe te voegen:** `CURRENT_STATE.md` =
  wat nu waar is (de sectie van de lane bijwerken, geen dagboek). `SESSION_HANDOFF.md` = alleen de
  recentste overdracht. `ROADMAP.md` = open en lopend werk.
- Vóór het sluiten van een chat waarin de toestand materieel veranderde: `SESSION_HANDOFF.md`,
  `CURRENT_STATE.md` en, bij gewijzigde coördinatie, `AGENT_EXCHANGE.md` bijwerken.
- Dezelfde tekst niet in meerdere bestanden; verwijs met issue-/PR-nummer of SHA.
- Historisch bewijs nooit verwijderen; archiveren met `tools/doc_memory/doc_memory.py split` +
  `verify-split`. Gearchiveerde secties zijn alleen-aanvullen (pytest controleert dit). Archieven
  mogen geen vertrouwelijke infrastructuurgegevens bevatten.
- Kleine branches en PR's; kerncode projectagnostisch, projectspecifiek gedrag in adapters/config.
  Feature-/codewerk via branch → PR → tests; handover-/coördinatiebestanden mogen op het afgesproken
  coördinatievlak zonder aparte feature-PR per bericht.
- **Agents en claims**: projectbrede reviews, blockers, toewijzingen en overdrachten in
  `handover/AGENT_EXCHANGE.md` (nieuwste eerst, geen secrets, klantdata of volledige testlogs);
  codereview op de PR. Wie een taak start, registreert claim + branch/PR. Vóór overname branches,
  PR's en CI reconciliëren; nooit een actieve conflicterende branch/PR dupliceren; een hervatte agent
  slaat geclaimde of afgeronde taken over. Beschikbaarheid van een agent is versnelling, geen
  afhankelijkheid; overname verzwakt geen branch-, PR-, review- of testvereisten.
- **Epics** vóór substantiële implementatie opsplitsen in begrensde child-issues; nieuwe children
  gebruiken `TASK.md` + `STATE.md`; bestaande `roadmap/children` niet massaal hernoemen (zie
  `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md`). Een umbrella is pas klaar op child-bewijs.
- **Troubleshooting**: eerst `docs/diagnostics/README.md` en `component_registry.yml`; diagnose naar
  de vroegst bewezen divergentie, niet de downstreamstatus patchen. Diagnosedocumenten blijven
  public-safe; `.github/ISSUE_TEMPLATE/failure-record.md` en `docs/SAFE_DIAGNOSTICS.md` blijven canoniek.
- Een AI-opdracht is pas klaar als tests/bewijs terminaal en groen zijn of de blocker expliciet is,
  met een duidelijke handover. "Agent zegt klaar" is geen acceptatie.

## 6. Geldigheid van informatie

| Type | Voorbeeld | Geldigheid | Vóór risicovolle wijziging |
|---|---|---|---|
| Stabiel | rol→launcher, aliassen, beslissing | tot gewijzigde beslissing | hergebruiken |
| Semi-stabiel | geïnstalleerde revisie/wheel, cron/systemd-beheer | tot deploy/herstart/update | gericht herverifiëren |
| Dynamisch | PID/startticks, poort-eigenaar, online-status | momentopname | altijd actueel op exacte doelserver |
| Bewijs | CI-run, ACK, receipt | gebonden aan exacte SHA/run-ID | nooit voor andere revisie |

Publieke repository: **geen** echte hostnamen, IP's, poorten, paden, users, servicenamen, device-ID's
of credentials; verwijs met register-ID uit de private AIfordable/Runner-Fabric-autoriteit, bv.
`<AF-VM-0004-tester-home>`.

## 7. Naslag — `docs/agents/AGENTS_FULL_2026-11-15.md`

| Onderwerp | Lees volledig wanneer |
|---|---|
| Missie en canonieke cross-project standards | scope of repositorystructuur wijzigt |
| Epic-decompositie en bounded children | een epic start |
| Diagnostische topologie (public-safe) | niet-triviale troubleshooting |
| Multi-agent beschikbaarheid en overname | een taak van een andere agent wordt overgenomen |
| Externe discovery en onafhankelijkheid | een directory- of registry-listing wijzigt |
| Volledige eigenaarsbeslissingen (§3) | een beslissing in detail moet worden toegepast |
