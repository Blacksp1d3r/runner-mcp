# Managed autostart

Runner MCP can install its own fixed non-root autostart without exposing a general service-control interface.

The preferred backend is a systemd user manager. When a host has no usable user systemd bus, `--backend auto` falls back to a managed user crontab block that supervises the same fixed Runner MCP components once per minute.

This packaging is for a host where Runner MCP is already installed and its private configuration is valid.

## Geïntegreerde zesrollen- en echte peerproef (source 0.1.169)

De op [PR #990](https://github.com/Blacksp1d3r/runner-mcp/pull/990) gemergede bestaande disposable CI-test combineert nu in één echte Linux `systemd --user`/crontab-proef de zes onschuldige cron-fixturerollen met de **daadwerkelijk gegenereerde** statische `runner-mcp-github-watcher.service` en de werkelijk gedeelde `run_cron_component`-flock. Met oude lock bezet geeft `systemctl start` **geen nieuwe taak**. Pas na het exact uitsluiten van één cronrol, draineren van de oude worker en aantoonbaar vrijgeven van de lock start een nieuwe `MainPID`. De terugweg stopt deze nieuwe generatie, verwijdert het test-owned unitbestand en herlaadt de user-manager voordat de oorspronkelijke zes cronregels plus vreemde cronregel exact worden teruggezet. Marker: `M2_DISPOSABLE_SIX_ROLE_RENDERED_PEER_EXCLUSIVE_SWITCH_AND_ROLLBACK=PASS`.

Dit is **uitsluitend** geïsoleerd testbewijs. De fysieke `github-runner` is niet omgeschakeld; M3 vereist juiste geïmporteerde wheel/source, owner UID, originele cron/proces/lock/children, functioneel resultaat+duurzame ACK, originele A7-/boot-/offline-herstelproef en externe monitorcompatibiliteit. Niet een managed unit zelfs disabled stagen op het origineel zolang cron reconcilet. De automatische updates worden door dit testwerk niet gewijzigd.

## Beperkte één-rol systemd-preview (v0.1.165, GEEN CLI of activering)

De reeds bestaande `plan_single_role_cron_exclusion` en `render_inactive_cron_server_peer_unit` zijn nu samen in `plan_single_peer_systemd_migration` te gebruiken. De functie vereist een exact `AutostartMigrationPlan` met toestand `PLAN_ONLY`, behoudt de volledige oorspronkelijke crontab en SHA256 voor toekomstige rollback en berekent één statische nevenunit zonder `Requires=runner-mcp.service` of `[Install]`. Zij voert **geen** crontab-/systemd-/procesactie uit; haar resultaat `cutover_authorized=False` is onveranderlijk. Dit is een Python bron-API voor begrensde testvoorstellen, geen nieuw `autostart install` of live migratiecommando.

Ook een inactieve unit met de managed marker onder `~/.config/systemd/user` kan `has_managed_user_units()` laten omslaan en de nog actieve cron-reconciler verstoren. Daarom de gegenereerde unit uitsluitend in geheugen of geïsoleerd testbed beoordelen; **nooit** naar de originele managed unitmap schrijven of bestaande auto-install/reconcile gebruiken bij gedeeltelijke migratie. De exclusieve rol-voor-rol-switch, daadwerkelijke rollback en host-/reboot-/A7-acceptatie zijn nog niet geïmplementeerd of live bewezen. Zie [#866](https://github.com/Blacksp1d3r/runner-mcp/issues/866) en de canonieke roadmap. Dit traject vormt geen extra blokkade voor de afzonderlijke automatische updates.

## Eén-rol migratiepreview deelt de cron-vergrendeling (source 0.1.166)

Voor de [systemd-migratie #866](https://github.com/Blacksp1d3r/runner-mcp/issues/866) voert de pure, inactieve `render_inactive_cron_server_peer_unit` nu de **bestaande `autostart cron-run <role>`** uit in plaats van de directe `<role> run`-opdracht. Daardoor neemt zowel de oorspronkelijke cronworker als deze niet-geïnstalleerde systemd-kandidaat dezelfde per-rol-`flock`, erfbaar over `execv`. De gecombineerde `plan_single_peer_systemd_migration` weigert een kandidaat zonder deze gedeelde lockroute en blijft `cutover_authorized=False`. De gewone volledige systemd-installatie en originele crontab worden hiermee niet aangepast.

**Geen live cutoverbewijs:** een bezette lock laat `cron-run` zonder dubbele uitvoering terugkeren; de statische service kan dan `inactive` zijn zonder automatische retry. Controleer vóór elke toekomstige fysieke switch de echte oude proces- en childgeneratie, cron-uitsluiting, dezelfde lock, de werkelijk uitgevoerde nieuwe functie en het exacte herstel. Ook een **inactief** managed-marker unitbestand in de bestaande `~/.config/systemd/user`-map kan cron-reconcile blokkeren: genereer uitsluitend in geheugen of op een disposable Linux testhost. Een echte rolgebonden switch en reboot-rollback zijn niet geïmplementeerd of op `github-runner` uitgevoerd; onafhankelijke automatische updates gaan voor en zijn niet gewijzigd.

## Test met één systemd-rol naast vijf cronrollen (disposable CI, v0.1.167)

De reeds bestaande GitHub-hosted Linux-`scripts/qualify_systemd_user_lifecycle_ci.sh` verifieert nu naast de algemene cron/systemd-terugval ook een echte **zesrollen-crontab** van onschuldige `/usr/bin/true`-commando's, één externe cronregel, uitsluitend verwijdering van de gesimuleerde `github-watcher`-regel, behoud van de overige vijf, start van de bestaande test-owned (niet-enabled) systemd-user-`sleep`-unit met werkelijke PID-readback en **volledig exact herstel van alle zes oorspronkelijke cronregels nadat die unit is gestopt**. De test draait alleen op een non-root disposable GitHub-hosted Ubuntu met systemd PID1 en een vooraf lege gebruikerscrontab. CI marker: `M2_DISPOSABLE_ONE_OF_SIX_CRON_TO_SYSTEMD_AND_FULL_ROLLBACK=PASS`. Dit bewijst scheduler/rollback-gedrag, **niet** de operationele originele rollen of hun client-ACK.

De aparte pure bronrenderer van v0.1.166 blijft de bestaande `autostart cron-run <role>` lock delen, zonder te installeren of activeren. Een originele fysieke rol-voor-rol overdracht, juiste actieve source/UID/PID, externe monitorconsumenten, echte functionele verwerking en A7/offline reboot-/ACK-herstel zijn nog niet gekwalificeerd; er is **geen** productie-cutoverbevoegdheid en de automatische updates blijven onafhankelijk. Zie [#866](https://github.com/Blacksp1d3r/runner-mcp/issues/866).

## Werkelijke kandidaat-unit met bestaande lock getest (v0.1.168)

De bestaande disposable GitHub-hosted Linux-test draait nu ook de **letterlijke systemd-unit uit `render_inactive_cron_server_peer_unit`**, niet alleen een algemene test-`sleep`-unit. Een tijdelijke, onschadelijke fake CLI roept de **werkelijke** `runner_mcp.cron_autostart.run_cron_component`-bron aan, neemt dezelfde private per-rol-`flock` en erft die via `execv` over. De proef bewijst dat de kandidaat bij een nog bezette cronlock geen tweede rol start, na gecontroleerd einde van de oude worker exact één nieuwe systemd-`MainPID` kan starten, en na stop de lock teruggeeft. De unit blijft static, met geen tweede server-`Requires` of `[Install]`; er zijn geen productiehostacties uitgevoerd. Jobmarker: `M2_DISPOSABLE_REAL_RENDERED_PEER_AND_SHARED_CRON_LOCK=PASS`.

**Belangrijke grens:** een startpoging bij lockconflict kan `systemctl start` succesvol beantwoorden maar de unit `inactive` laten. De operator mag dit nooit als functionele rol-ACK beschouwen. De oorspronkelijke host, zes echte cronrollen, geladen executable en owner/UID, echte functie/nieuwe task ACK, A7 herstel en reboot-rollback blijven ongekwalificeerd. Uitsluitend source/read-only voorbereiding voor fysieke #866; niet de originele user-units plaatsen of cron omzetten, automatische updates onafhankelijk laten functioneren.

## What gets installed

The command:

```bash
runner-mcp autostart install
```

selects the backend automatically:

- systemd user services when the user's systemd manager is available;
- otherwise a managed crontab block, when `crontab` is available.

You can force the choice locally with `--backend systemd` or `--backend cron`.

Both backends always supervise the loopback-only Runner MCP server. They also supervise the fixed GitHub mailbox watcher when the mailbox is configured and explicitly bootstrapped, and the fixed completion watcher when completion delivery is configured and explicitly bootstrapped.

Generated unit files or crontab entries live only in local user state. They may contain local executable/configuration paths, so that generated state must not be copied into the public repository.

No bearer token, GitHub token, database credential or project command is placed in the generated autostart configuration.

## Safety boundaries

Autostart does not create a generic systemd control surface.

It:

- manages only the fixed server, GitHub-watcher and completion-watcher components;
- binds the MCP server to `127.0.0.1`;
- uses fixed `systemctl --user` argument arrays on the systemd backend;
- uses a marked crontab block plus a local lock-protected `cron-run` helper on the cron backend;
- the cron helper executes only fixed Runner MCP argv arrays and does not accept a shell command;
- refuses to overwrite/delete foreign systemd units or silently absorb unmanaged Runner MCP cron entries;
- requires watcher bootstrap before enabling either watcher;
- keeps bootstrap/replay state unchanged;
- never enables sudo or system-level services;
- is available only through the local CLI, not through the GitHub mailbox.

Changing the local server port is an explicit local installation choice:

```bash
runner-mcp autostart install --port 8000
```

## Dedicated service-user hosts

When Runner MCP is installed under a dedicated service account, qualify the runtime as that account. Do not inspect or execute the service account's private virtual environment directly from a different operator account, and do not relax private home/configuration permissions merely to make that possible.

From an authorized local operator account, prefer the existing delegated operator launcher installed by `install-operator.sh`. For direct local diagnosis where that launcher is not yet available, use the host's normal account-switching policy and run the public CLI as the service user, for example:

```bash
sudo -iu SERVICE_USER runner-mcp status
sudo -iu SERVICE_USER runner-mcp doctor
sudo -iu SERVICE_USER runner-mcp autostart preflight
```

Use the literal local service-account name in place of `SERVICE_USER`; never copy credentials or private configuration into the operator account.

Apply a capability/version fence before activation:

1. `runner-mcp status` must identify the intended installed runtime and must not report `development` for a packaged persistent install.
2. `runner-mcp --help` / `runner-mcp autostart --help` must expose the expected command surface. If `autostart preflight` is absent, treat the runtime as stale and update/bootstrap it before continuing.
3. `runner-mcp doctor` must complete against the same service-user runtime.
4. Only then run `runner-mcp autostart preflight`.
5. A blocked preflight remains a hard activation gate; do not bypass it by installing autostart manually.

For repository diagnostic scripts, invoke them explicitly with `bash scripts/diagnostics/...` when appropriate instead of relying on executable-bit state after checkout. Run any private-runtime probe in the service-user context it is intended to qualify.

## Before installing

Run:

```bash
runner-mcp doctor
runner-mcp autostart preflight
```

`autostart preflight` is read-only. It executes the same fresh activation checks used immediately before installation and returns only a bounded readiness category. A blocked result does not create unit files, call the managed backend installer, or alter crontab state.

If you use the GitHub mailbox, configure and bootstrap it first:

```bash
runner-mcp github-mailbox status
runner-mcp github-watcher bootstrap
```

Bootstrap is intentionally explicit. Autostart will not move or create the watcher cursor on your behalf.

If you use completion notifications:

```bash
runner-mcp completion-notifier status
runner-mcp completion-watcher bootstrap
```

Again, autostart will not reinterpret historical completions.

## Install and inspect

Confirm the activation gate first:

```bash
runner-mcp autostart preflight
```

Only a clear result is eligible for installation. Then install and start the applicable managed services:

```bash
runner-mcp autostart install
```

Check only safe component state:

```bash
runner-mcp autostart status
```

Status reports only the selected backend and whether the server, GitHub watcher and completion watcher are installed, enabled and active. It does not print unit-file paths, crontab contents, private configuration paths or credentials.

## Remove

To remove only autostart state managed by Runner MCP:

```bash
runner-mcp autostart remove
```

The CLI requires the explicit local confirmation phrase shown on screen. Foreign unit files and unrelated crontab entries are never removed.

On the systemd backend, removal disables and stops the managed units. On the cron backend, removal deletes the managed schedule so no future restart occurs; it deliberately does not send a blind process-kill signal to a currently running component. Stop or reboot that local account explicitly when immediate termination is required. This conservative behavior avoids killing a process whose identity cannot be proven from cron state alone.

## Original-host cron to systemd-user migration (#866)

This section documents the **migration boundary**, not an activation procedure. The original physical `github-runner` has six historically cron-supervised Runner MCP/Fabric roles. Blacky has a separate hourly F35 reviewer task and is **not** a substitute for Black or `github-runner`. Their existing schedulers must continue operating until the individual original-host gates in [#866](https://github.com/Blacksp1d3r/runner-mcp/issues/866) are satisfied.

**Do not use the general `autostart remove`, `autostart install` or `autostart reconcile` commands as a per-role live migration tool.** The current implementations manage the entire Runner MCP-owned autostart block or configured unit set; they do not atomically transfer a single cron role while preserving five other active cron rows. The direct installers deliberately refuse cross-backend coexistence. Removing the complete managed cron block first would interrupt supervision and could affect the existing control/update path. No code merge, successful dry-run, inactive unit file or connected MCP response authorizes that interruption.

The source-level `autostart plan` command (where present in the **actually installed** CLI) is read-only and deliberately returns `PLAN_ONLY` or `WAIT`, never live authorization. An older deployed CLI must not be assumed to support it merely because `main` does. Match the **original physical host and service UID**, exact managed role/cron command, actual running PID/start generation, listener/port, active executable and imported wheel provenance, systemd-user manager/linger, existing dependencies/monitor consumers, and a verified restorable prior supervisor state using the existing AIfordable infrastructure registry and handover. Retained backup bytes are not, by themselves, proof that a per-role rollback has been rehearsed.

The next **code/test** deliverable before any real canary is an owner-bound, **single-role** switch-and-restore path within the existing cron and systemd-user backends. It must preserve all unaffected cron entries and existing update/Agent Bus/relay processes, prevent simultaneous supervisors for the selected role, accept only inactive/disabled prevalidated candidate units, fail closed on version/host/owner/port/source/lock conflicts, and restore the exact previous cron entry after a failed functional verification. Qualify it on the existing disposable Linux test path first, including reboot/linger, misconfiguration, failure injection and real loaded-manager rollback. The original role's functional result/ACK and external health/monitor expectations remain separate acceptance criteria. Blacky's hourly reviewer needs a **oneshot + timer**, not a permanent service; Windows continues using Task Scheduler.

Migration planning and source tests **do not block unrelated automatic updates or existing services**. Equally, an ongoing update is not permission to switch supervisors: coordinate its safe window through the existing Fabric fleet authority, and defer only the affected original-host role if active update/rollback state or fresh execution evidence is unknown. Keep cron as the active owner throughout source development, and record the eventual one-role canary and rollback under the existing #866 / CURRENT_STATE / SESSION_HANDOFF authorities. Never create another updater, scheduler, relay, inventory or control plane.

### Read-only, non-installable per-role candidates (source 0.1.159–0.1.160)

Source-only `plan_single_role_cron_exclusion` calculates the exact original managed cron block minus one fixed scheduled role and retains all original bytes. `render_inactive_cron_server_peer_unit` calculates one **static** unit for a configured peer, omitting both `Requires=runner-mcp.service` and `[Install]`/`WantedBy`. Neither helper writes, enables, starts or attests anything.

**A disabled managed unit file is NOT harmless live staging:** `has_managed_user_units()` treats its marked file as installed and the current cron side will reject it during reconciliation. Keep candidate bytes strictly outside the original live user-unit directory. The regular install/remove/reconcile CLI still acts on the full managed role set and is not a one-role cutover. Exact exclusive cutover, original source/PID/lock attestation, functional ACK, boot/reboot, external monitor and rollback proof remain #866 M3–M6. Continue unrelated automatic updates independently.

## Headless hosts

Some Linux installations do not expose a usable systemd user manager to the Runner MCP account. In `auto` mode Runner MCP now falls back to a managed user crontab instead of requiring a system-level policy change.

The cron backend starts each fixed component through a per-component private lock. A new cron tick exits immediately while the component already owns its lock; after a crash, the next minute can start it again.

If an existing unmanaged Runner MCP cron setup is detected, installation fails closed instead of creating duplicate supervisors. The operator must remove or migrate those old entries explicitly before the managed cron backend is installed.

Runner MCP deliberately does not change login/session, system-level services or host privilege policy automatically.
