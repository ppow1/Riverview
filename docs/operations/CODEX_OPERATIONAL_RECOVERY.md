# Codex Operational Recovery — Riverview

Status: persistent recovery index. Updated 2026-10-17. This file is an index of verified solutions, not a substitute for authoritative runbooks.

## Required recovery sequence
1. Read this file at session start, after context compaction, and whenever the execution environment changes.
2. Identify the current execution environment, target host, and exact failure signature.
3. Consult the matching known-good procedure and linked runbook **before** attempting new diagnostics.
4. Distinguish VERIFIED live evidence, DOCUMENTED historical state, and UNVERIFIED assumptions.
5. Verify prerequisites and use the existing authorized path. Never repeat previously disproven fixes without new evidence.
6. If blocked, report the specific missing capability or changed precondition, not a generalized server failure.
7. After resolving an incident, update this index and the owning runbook together with date, commands, evidence, and any remaining unknowns.
8. Never commit or print private keys, passwords, bearer tokens, OAuth secrets, or other credentials.

## Camrui SSH — VERIFIED from Windows PowerShell, 2026-10-17
- Alias: `camrui`; host `192.168.1.155`; user `admin1`.
- Windows SSH IdentityFile reference: `C:/Users/wille/.ssh/octominer1_nopass`; `IdentitiesOnly yes`.
- Successful unattended `ssh.exe -o BatchMode=yes camrui` returned hostname `admin1-Default-string`, account `admin1`, working directory `/home/admin1`, exit code 0.
- The isolated Linux Codex environment does **not** automatically inherit the Windows SSH alias, client configuration, or identity. `Could not resolve hostname camrui` from Linux is not a Camrui SSH-server failure.
- Linux Codex-to-Camrui unattended access remains UNVERIFIED. Before assuming it cannot work, inspect available **non-secret** client configuration and identity file presence and test only an authorized path with strict host-key verification. Never print a private key.
- Do not replace credentials, disable host-key checking, or change server SSH settings to fix a client-environment mismatch.

### Verified PowerShell clipboard diagnostic convention
```powershell
Clear-Host
$Command = 'hostname; whoami; pwd'
$Result = & ssh.exe -o BatchMode=yes camrui $Command 2>&1
$Report = ($Result | Out-String) + "`nExitCode: $LASTEXITCODE"
$Report | Set-Clipboard
Write-Host $Report
```
Use variables, capture exit status, copy complete **non-secret** output to clipboard, and display it. Prefer simple linear PowerShell diagnostics over unnecessary `else`/`throw` branches.

Source: [Machine connections and Comms5 recovery](RIVERVIEW_MACHINE_CONNECTIONS_AND_COMMS5_RECOVERY_2026-10-17.md); [SSH standard](network/RIVERVIEW_SSH_STANDARD.md).

## Other managed device access — DOCUMENTED, verify live
| Device | Alias / address | User | Notes |
|---|---|---|---|
| Camrui | `camrui` / `192.168.1.155` | `admin1` | Windows path VERIFIED |
| OctoMiner host 1 | `octo1` / `192.168.1.160` | `root` | Windows SSH standard |
| OctoMiner host 2 | `octo2` / `192.168.1.162` | `root` | Windows SSH standard |
| Ionoge | `64.227.21.54` | tunnel uses `root` | Dedicated restricted key, not general login |
| PiKVM / PiCam | Not established | CHECK LIVE | Do not invent address/identity |
| Windows development workstation (inbound SSH) | Not established | CHECK LIVE | Do not infer an SSH server |

Historical OctoMiner naming is inconsistent. Confirm hostname, NIC/IP, GPUs and services before changes. Source: [SSH standard](network/RIVERVIEW_SSH_STANDARD.md).

## TCP/IP, Comms5 tunnel, and public routing — VERIFIED historical incident, 2026-10-17
- Camrui `riverview-comms5-tunnel.service` establishes restricted reverse SSH forwarding from Ionoge `127.0.0.1:11826` to Camrui `127.0.0.1:11826`. Loopback `/healthz` returned HTTP 200.
- This tunnel is **not** a general-purpose Codex-to-Camrui interactive SSH connection.
- Prior host-key failure: unprivileged `admin1` could not read root-only known-hosts file. Solved using systemd `LoadCredential` and `UserKnownHostsFile=%d/ionoge-known-hosts`; do not disable strict host-key checking.
- Prior public-key refusal: `permitopen="none"` in Ionoge restricted authorized-key options blocked the tunnel. Removing only that option restored authentication; do not reintroduce it. Preserve all other restricted-key safeguards.
- Prior `hostname contains invalid characters`: caused by PowerShell/Linux command construction or CRLF; normalize line endings, not server authentication.
- Diagnostic sequence: Camrui backend → tunnel service → Ionoge loopback listener → `/healthz` → Caddy route → OAuth → authenticated MCP. Health alone does not prove MCP functionality.
- Preserve existing Comms4 `/mcp` route and separate `11825` loopback boundary.

Source: [Machine connections and Comms5 recovery](RIVERVIEW_MACHINE_CONNECTIONS_AND_COMMS5_RECOVERY_2026-10-17.md).

## Grace and Comms5 — last reported, CHECK LIVE before claiming progress
- Five discovery operations worked; 16 operational operations returned `NOT_IMPLEMENTED`.
- Historical Comms5 handlers are not automatically compatible with the newer Camrui runtime/schema/authority model.
- PR #20 source changes fixed transport-attested Steward identity checks and linked worktree validation; 65 focused tests passed. Last reported open and undeployed. Verify current PR/runtime status.
- Acceptance requires real authenticated intake, authorization, queueing, execution, reconciliation and status; tests or advertised tool names alone are insufficient.

Sources: [Comms5 contract](../architecture/RIVERVIEW_COMMS5_CONTRACT.md), [deployment guide](RIVERVIEW_COMMS5_DEPLOYMENT.md).

## GitHub and worktrees
Read `AI_HINTS.md` and `tools/hermes/skills/riverview-clean-state/SKILL.md`. Check checkout root, branch, HEAD, upstream, registered worktrees, dirty state, and source provenance. Do not confuse an isolated Linux Codex workspace with the Windows development machine or live Camrui checkout. A missing local remote-tracking ref does not prove the remote branch is missing: check `git ls-remote origin refs/heads/<branch>`. Preserve unrelated changes.

## Maintenance template
Record **symptom**, **failure signature**, **date**, **environment**, **target**, **VERIFIED/DOCUMENTED/UNVERIFIED**, **established cause**, **last-known-working method**, **nonsecret command**, **actual verification**, **disproven attempts**, **source runbook**, and **remaining unknowns**. Keep the index concise and link to the owning procedure rather than duplicating large sections.
