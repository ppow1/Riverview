# Riverview machine connections and Comms5 recovery — 2026-10-17

**File Revision:** 1.0.1
**Updated:** 2026-10-17 — record Windows alias acceptance and the Camrui-hosted Codex execution environment.
**Predecessor SHA-256:** `33233bf090374ca694eec00bb3becc3fd1b0658f35d97a7b07697fcbcea834d9`

**Start here for machine access, Ionoge, Camrui, Comms5 SSH reverse tunnel, and related troubleshooting.** Evidence status is explicit: **VERIFIED** means observed in operator-provided output on 2026-10-17; **DOCUMENTED** means inherited from an existing repository runbook; **CHECK LIVE** means not independently reverified in this commissioning session.

## Machine and access inventory

| Machine / function | Address or name | Access / alias | Evidence and notes |
|---|---|---|---|
| Windows development workstation | `DESKTOP-JA3RPNQ` | Windows PowerShell; SSH client | DOCUMENTED in project history. The operator's working shell is `A:\Riverview`. SSH config and keys are local, not stored in Git. |
| Camrui Ubuntu — resident Grace / Riverview core / Comms5 backend | `192.168.1.155` | From Windows: `ssh camrui`; Linux account `admin1` | VERIFIED 2026-10-17: headless Windows alias command returned hostname `admin1-Default-string`, account `admin1`, `/home/admin1`, exit code 0. Repository checkout: `/home/admin1/projects/Riverview-New-Core`. |
| Ionoge DigitalOcean VPS — public ingress | `64.227.21.54`; `ionoge-control-01` | From Windows: `ssh root@64.227.21.54` | VERIFIED SSH and Comms5 reverse-tunnel endpoint. Public DNS name: `riverview-comms.ionoge.com`. |
| OctoMiner inference host, referred to as OCTOMINER1 in WOL runbook | `192.168.1.160` | `ssh root@192.168.1.160`; Windows alias `octo1` in recent operations | DOCUMENTED in `docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md` and `CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md`. **Naming warning:** the model guide calls its target “OCTOMINER2 / SSH alias octo1”; confirm hostname and GPU identity live, not from labels alone. |
| Other OctoMiner | Address not established by this document | Windows alias `octo2` appears in OctoMiner runbook | CHECK LIVE: run `ssh octo2 hostname; ip -br addr` before recording a fixed address or changing service settings. |

## Verified SSH path and Codex execution environment — 2026-10-17

The Steward verified unattended access from Windows PowerShell using the existing alias and existing Windows-managed SSH identity:

```powershell
ssh.exe -o BatchMode=yes camrui "hostname; whoami; pwd"
```

Observed Windows output:

```text
admin1-Default-string
admin1
/home/admin1
ExitCode: 0
```

The alias is configured on the Windows development workstation, documented as `C:\Users\wille\.ssh\config`. The private key remains on that workstation and was neither read nor copied by the Codex Linux process. The verified output did not include the exact `IdentityFile` setting; inspect it only on Windows with `ssh.exe -G camrui` if the filename is operationally needed. Treat the Windows configuration as the source of truth.

The Codex execution environment for this session is not a separate Windows client: it is a Linux shell on Camrui itself. Independent local observations on 2026-10-17 showed hostname `admin1-Default-string`, user `admin1`, `/home/admin1`, `eno1` configured with `192.168.1.155/24`, and systemd running. Therefore engineering commands in this session use Camrui's local shell and checkout; they do not depend on importing or reusing the Windows SSH identity.

### Earlier alias failure and diagnosis

An earlier attempt to run `ssh -o BatchMode=yes camrui ...` inside a Linux execution context returned `Could not resolve hostname camrui: Temporary failure in name resolution`. That is a client-side name-resolution/configuration failure before SSH authentication; it is not evidence that Camrui's SSH daemon is down or that the Windows key was rejected. In that Linux context, `ssh -G camrui` showed no matching `~/.ssh/config` stanza and left the hostname as the literal alias `camrui`.

Distinguish the failure classes:

- `Could not resolve hostname`: the current client's alias/DNS mapping did not resolve; inspect that client's effective configuration and name resolution.
- `Connection timed out` or `Connection refused`: the name/address resolved, but network reachability or the target listener failed.
- `Permission denied (publickey)`: the SSH connection reached an SSH server, but the offered identity was not accepted. Inspect the client's effective identity selection and server authorization only after verifying the target host.
- Windows `ssh.exe -o BatchMode=yes camrui ...` returning the observed host/account/path with exit code 0: unattended Windows alias access is verified.

Do not repair Camrui SSH based on a missing alias in a separate Linux client, and do not copy the Windows private key into that client. Preserve both access paths: the Windows alias for remote operator access and the Camrui-local shell for this host's Codex execution.

**Security boundary:** these are operational identifiers, not credentials. Never commit private keys, OAuth client secrets, bearer tokens, access tokens, passwords, or the contents of `/etc/riverview/comms5/ionoge-tunnel`.

## Comms5 working topology (VERIFIED 2026-10-17)

```text
ChatGPT / external MCP client
    |
    | HTTPS (PUBLIC ROUTE / OAUTH: NOT YET REVERIFIED IN THIS SESSION)
    v
riverview-comms.ionoge.com (Ionoge VPS, 64.227.21.54)
    |
    | Caddy: /comms5/mcp -> /mcp (check live configuration)
    v
127.0.0.1:11826 on Ionoge (reverse-SSH listener)
    |
    | SSH -R 127.0.0.1:11826:127.0.0.1:11826
    | Camrui -> root@64.227.21.54
    v
127.0.0.1:11826 on Camrui (Comms5 HTTP backend)
    |
    +-- GET /healthz => HTTP 200
        {"status":"ok","service":"riverview-comms5-camrui"}
```

**Verified:** `riverview-comms5-tunnel.service` is `active (running)` and `enabled` on Camrui; Ionoge `ss -ltnp` showed `sshd` listening at `127.0.0.1:11826`; Ionoge `curl -i http://127.0.0.1:11826/healthz` returned HTTP 200 and the JSON above.

**Not proven by these checks:** current public Caddy routing, OAuth discovery, ChatGPT connector registration, MCP initialize, authenticated tool calls, or end-to-end public accessibility. Older documentation reports past public acceptance, but do not treat it as a current live test.

**Comms4 preservation:** existing public `https://riverview-comms.ionoge.com/mcp` uses a separate `127.0.0.1:11825` loopback boundary. Do not replace it while commissioning Comms5.

## Camrui systemd tunnel: authoritative live configuration

- Unit: `/etc/systemd/system/riverview-comms5-tunnel.service`
- Drop-in: `/etc/systemd/system/riverview-comms5-tunnel.service.d/hostkey.conf`
- Service account: `admin1`
- Private key source: `/etc/riverview/comms5/ionoge-tunnel` (root-owned, mode 0600; **never print or commit contents**)
- Pinned host keys source: `/etc/riverview/comms5/known_hosts`
- Systemd credential names: `ionoge-tunnel`, `ionoge-known-hosts`
- Runtime credential directory: `/run/credentials/riverview-comms5-tunnel.service/`
- SSH target: `root@64.227.21.54`
- Reverse bind: `-R 127.0.0.1:11826:127.0.0.1:11826`
- SSH flags verified in running process: `-NT -i /run/credentials/riverview-comms5-tunnel.service/ionoge-tunnel -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/run/credentials/riverview-comms5-tunnel.service/ionoge-known-hosts -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o TCPKeepAlive=yes`
- Service restarts are managed by systemd; **inspect** `systemctl cat` for the current exact restart policy before edits.

The host-key credential drop-in fixes a previous failure in which the unprivileged `admin1` process could not read a root-only `known_hosts` path. Systemd now loads the pinned host key as a service credential. The associated Codex source change was prepared on `codex/comms5-hostkey-credential-20261017`, commit `5d1f2d3213e74fbdf01057a3d922d30208907e34`; **verify its merge/deployment state** before claiming source/runtime parity.

## Ionoge authorized key: precise restriction and repair

The dedicated tunnel key's **public** fingerprint is:

`SHA256:pW1d46JXrxuInWRoX8cV31tXSfM4xW9kMx0OEmQEYfE`

The pinned Ionoge SSH server ED25519 host-key fingerprint observed was:

`SHA256:z93NerVUXIJ/5p3yDX7srC4dJBYwfq/xtDYE1QdjjTE`

The authorized key is in `/root/.ssh/authorized_keys`, with restrictive options. The verified working **options prefix** is:

```text
restrict,port-forwarding,permitlisten="127.0.0.1:11826",no-agent-forwarding,no-X11-forwarding,no-pty,command="/bin/false"
```

The old entry additionally contained `permitopen="none"`. In a controlled test, **removing only that option** caused the server to accept the previously rejected key and authenticate successfully. The change was then applied permanently, and the tunnel started successfully. Do not reintroduce `permitopen="none"` to this key. The original file was backed up at:

`/root/.ssh/authorized_keys.comms5-20261017-112404.bak`

This is a restricted reverse-tunnel key, **not** a general-purpose interactive root login key. `command="/bin/false"` remains in the working entry; SSH `-N` requires no remote shell.

## Read-only connection and recovery checks

From **Windows PowerShell** (the operator prefers a single copy/paste block with `Clear-Host` first, complete output in `$Report`, `$Report | Set-Clipboard`, then `Write-Host $Report`):

```powershell
Clear-Host

$Report = & {
    Write-Output "=== CAMRUI TUNNEL ==="
    ssh -T camrui 'systemctl is-active riverview-comms5-tunnel.service; systemctl is-enabled riverview-comms5-tunnel.service; systemctl --no-pager --full status riverview-comms5-tunnel.service | head -22'
    Write-Output "=== IONOGE LOOPBACK AND HEALTH ==="
    ssh -T root@64.227.21.54 'ss -ltnp | grep 11826; curl -sS -m 8 -i http://127.0.0.1:11826/healthz'
    Write-Output "=== CAMRUI SERVICE DEFINITION ==="
    ssh -T camrui 'sudo systemctl cat riverview-comms5-tunnel.service'
    Write-Output "=== IONOGE CADDY CONFIGURATION ==="
    ssh -T root@64.227.21.54 'sudo caddy validate --config /etc/caddy/Caddyfile'
} *>&1 | Out-String

$Report | Set-Clipboard
Write-Host $Report
```

From Camrui, to restart **only when authorized and needed**:

```bash
sudo systemctl reset-failed riverview-comms5-tunnel.service
sudo systemctl restart riverview-comms5-tunnel.service
systemctl is-active riverview-comms5-tunnel.service
journalctl -u riverview-comms5-tunnel.service -n 80 --no-pager
```

On Ionoge:

```bash
ss -ltnp | grep 11826
curl -sS -m 8 -i http://127.0.0.1:11826/healthz
sudo caddy validate --config /etc/caddy/Caddyfile
```

## Troubleshooting decision tree (observed incidents)

1. **`No ED25519 host key is known for 64.227.21.54`:** first inspect whether the service can read its pinned known-hosts file. The working fix uses `LoadCredential=ionoge-known-hosts:...` and `UserKnownHostsFile=%d/ionoge-known-hosts`. Do not disable strict host-key checking.
2. **`Permission denied (publickey)` after `Offering public key`:** inspect the exact dedicated key entry on Ionoge. On 2026-10-17 the key fingerprint, file ownership, modes, and `sshd -T` settings were correct, but `permitopen="none"` in the authorized-key options caused the key to be refused. Controlled removal led to `Server accepts key` and `Authenticated to ... using "publickey"`.
3. **`hostname contains invalid characters` in diagnostics:** this arose from PowerShell-to-Linux command construction/line endings; it was **not** an SSH server authentication result. Avoid multiline command arguments sent directly as a hostname. If piping scripts to `ssh -T ... "bash -s"`, normalize CRLF to LF and remove trailing CRs.
4. **Tunnel service active but no Ionoge listener:** inspect `journalctl`, `ExitOnForwardFailure`, and remote `ss -ltnp`; verify the requested bind is `127.0.0.1:11826`.
5. **Listener present but `/healthz` fails:** verify Camrui backend service and loopback `127.0.0.1:11826`; distinguish backend outage from SSH tunnel outage.
6. **Loopback health works but public Comms5 fails:** inspect Caddy route, rewrite `/comms5/mcp` to `/mcp`, TLS, OAuth discovery, bearer authentication, and MCP protocol independently. Do not modify Comms4 `/mcp` route as a workaround.
7. **Misidentified OctoMiner:** `octo1`, `octo2`, `OCTOMINER1`, and `OCTOMINER2` have historically been used inconsistently. Confirm hostname, LAN IP, NIC MAC, GPUs and services live before changes.

## Other machine/service references

- [Comms5 deployment guide](RIVERVIEW_COMMS5_DEPLOYMENT.md) — Comms5 ingress design and historical acceptance claims; the old Windows tunnel instructions are superseded by this verified Camrui runbook.
- [Comms/Comms4 guide](RIVERVIEW_COMMS.md) — `/mcp`, Ionoge Caddy, `127.0.0.1:11825`, historical Windows runtime.
- [OctoMiner WOL and remote power](octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md) — `192.168.1.160`, NIC MAC, power recovery, WOL.
- [Current AI model startup](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md) — 80B and Grace vision service names, `8080` and `18080`, GPU UUIDs, verified October 13 configuration.
- [Comms5 contract](../architecture/RIVERVIEW_COMMS5_CONTRACT.md) — application semantics and authority boundaries.

## Documentation maintenance rule

For each future host, tunnel, OAuth, Caddy, inference or SSH change, record **date, machine, hostname, IP, alias, unit, effective config path, port, exact nonsecret command, observed result, rollback/backup path, and source commit/PR**. Mark **VERIFIED / DOCUMENTED / CHECK LIVE** explicitly. Keep the central inventory updated and link to the detailed component runbook. Never publish secret material.
