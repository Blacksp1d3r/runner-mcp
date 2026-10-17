## Diagnose a blocked physical stage without rerunning it (RMCP-F-0030)

A real operator-local stage returned `existing_installer_failed` on the new
Black in October 2026. Its partially created venv lacked a usable pip command;
the root cause and exact Ubuntu packaging state remain **unconfirmed**. Preserve
the failed stage; **never** re-run `stage`, `install.sh`, `pip install`,
`sudo`, or remove/overwrite the old prefix as a shortcut. Do not enroll
Agent Bus or claim original-client ACK.

An independently verified **new source checkout** with the added diagnosis
command may examine the already-failed, original manifest-pinned stage on the
**same** physically controlled host. It does **not** need to match the old
manifest source commit because it cannot stage, run, repair or activate it.
Do not edit the original private 0600 manifest or old source checkout:

~~~bash
python3 scripts/managed_host_bootstrap.py diagnose \\
  --manifest /PRIVATE/original-host-bootstrap.json
~~~

This checks owner custody of the private manifest and stage, exact local
machine identity match, and `lstat`-only file/dir types in the fixed original
stage location. It executes **no staged Python, pip, installer or shell**, makes
no filesystem writes, and prints **no machine fingerprint, stage path,
credential, command stdout, or installed package list**. A pip `__init__.py`
presence is *only* a file observation, not evidence `pip` can run. Likewise,
a `stage-result.json` presence is **not** trusted release/activation proof.
All admission flags remain false and installer root cause remains undetermined.

Separately, a physically attended operator may run limited **read-only** OS
package inventory for `python3.12-venv`, `python3-venv` and Python wheel
packages. System `python3 -m ensurepip --version` failing on Ubuntu does not
on its own prove that `python3.12-venv` is missing. A package fix or fresh
stage generation requires separate owner-approved bounded recovery; the
source merge and diagnosis command never grant that approval. See Runner-MCP
#716/#718 and Runner-Fabric #1562/#1563.

---

# Local host bootstrap — first staged Runner-MCP instance

Tracking: Runner-MCP #713; AIfordable #428/#584/#585; Runner-Fabric #1554/#1556/#924.

This is the **one-time physically attended, local** prerequisite to later
Runner-MCP → Fabric management of a new host. No Desktop Commander, SSH,
remote installation command, generic host agent, cloud installer or GitHub
Actions host-control task is created here. The script stages but **never
activates** the host.

## Safety contract

- Run only on the intended privately owned Ubuntu/Linux machine, as its
  intended *unprivileged* service user. It **refuses root**.
- Python >=3.12, /usr/bin/git, /usr/bin/bash and venv/pip must be
  available **before** staging. The installer performs **no apt/sudo**.
- The local source checkout must be clean, on a full immutable commit, with
  the canonical runner-mcp GitHub origin. The preapproved SHA-256 of its
  **existing** install.sh must match.
- Private operator manifest: regular 0600 file, owned by the invoking user,
  without symlinks. Record the asset ID from the existing AIfordable
  Infrastructure Authority; use a dedicated new runner subject. The
  machine_id_sha256 is a locally observed, operator-confirmed fingerprint
  and **not independent remote attestation**.
- plan is read-only. stage requires exactly the full plan SHA-256.
  It creates only a new private isolated *non-serving* installation under
  that user's home, reusing the normal upstream install.sh.
- Existing live Runner-MCP, launchers, crontab, systemd, Agent Bus relay,
  AIfordable website, control tunnels, SSD/HDD partitions, filesystems,
  network ports, credentials and service accounts remain untouched.
- Partial failure leaves the stage in place and refuses automatic replay
  or cleanup. Never bypass with a different host alias.
- Successful stage records service_activation=false,
  relay_enrollment=false and original_client_ack=false.
  **Do not** interpret stage success or CI as host enrollment.

## Locally inspect and prepare the private manifest

Use a **clean immutable checkout** obtained by the physical operator from the
existing canonical GitHub repository. Verify the intended approved source
commit through the repository release/issue and an **independent trusted
channel** before using it. The script does not fetch a floating branch.

On that host, obtain the **local** machine digest (do not paste it into public
GitHub issues or ChatGPT):

~~~bash
python3 scripts/managed_host_bootstrap.py identity
git rev-parse --verify HEAD
sha256sum install.sh
~~~

Create an operator-private file OUTSIDE the repository, mode 0600, with
exactly these keys (example IDs and placeholder digests only):

~~~json
{
  "schema_version": "runner-mcp/local-host-bootstrap/v1",
  "asset_id": "AF-HOST-0000",
  "runner_subject": "runner:example-host",
  "machine_id_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_commit": "1111111111111111111111111111111111111111",
  "installer_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
~~~

This private manifest contains no relay token, bearer, password, network
destination, port, installer command or arbitrary executable path. Its
presence is operator intent, **not** proof that AIfordable authorized that
host, or that the relay credential belongs to it.

Run from the exact checked-out repository directory (replace the
illustrative private path with the local private file):

~~~bash
python3 scripts/managed_host_bootstrap.py plan \
  --manifest /PRIVATE/host-bootstrap.json --source "$PWD"
~~~

Read the local, secret-free plan. Check exact asset/runner identity and
approved source digest. Only then, locally and intentionally:

~~~bash
python3 scripts/managed_host_bootstrap.py stage \
  --manifest /PRIVATE/host-bootstrap.json --source "$PWD" \
  --accept-plan THE_FULL_PLAN_SHA256
~~~

The stage uses the existing installer in a fresh isolated install root
and a fresh isolated launcher directory, without changing ~/.local/bin.
It checks installed pip check and runner-mcp --help. A failed stage
must be diagnosed, not retried automatically. Never use a sudo invocation.

## Separate admission before turning on a service

**Not implemented or authorized by this child.** Next, via the existing
first-party and owner-controlled surfaces only:

1. Bind the exact physical host, user and process to its stable
   AIfordable asset ID; attest the installed wheel/source and original
   first-party listener. Validate the already-mounted storage without
   formatting it.
2. Have the owner configure the *existing* Runner-MCP setup and existing
   agent-bus configure private secret custodian; never copy another
   runner's subject, credential, listener or control token.
3. Qualify the managed Agent Bus worker and protected Fabric release
   using existing product steps with authenticated issuer, lease/fence,
   generation, outbox, original-client command→result→ACK and verified
   error/recovery paths.
4. Only after separate protected activation/rollback admission enable
   bounded local services, the AIfordable public web release, isolated
   synthetic demos and the authenticated Fabric Cockpit.

The current central bridge has been observed handshaking while
mutation_enabled=false and Agent Bus relay health unavailable.
This cannot authorize a Black install or Claude dispatch.

## Failure Museum seed — first-host identity confusion

Avoid replay of Runner-Fabric #1202 wrong-host control-path incident: a
reasonable-looking version/heartbeat from a connected **different host**
is not evidence that this target is online, enrolled or authorized.
Also avoid reformatting an already-mounted disk because an earlier
bootstrap issue described a now-obsolete destructive provisioning step.
