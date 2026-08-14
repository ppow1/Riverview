# Riverview Comms

Version: 0.10.0
Checkpoint date: 2026-08-14
Status: deployment checkpoint; external ChatGPT acceptance remains pending.

## Purpose and authority

Riverview Comms is the Riverview-owned, bounded application surface for the
designated reasoning conversation. It exposes PostgreSQL-backed operational
projections through the accepted Riverview MCP implementation. PostgreSQL is
authoritative operational state; GitHub is authoritative source and history.

The application is read-oriented. Conversation text, the MCP transport, and the
browser doorbell do not create execution authority.

## Ownership

Riverview owns all Riverview operational source, runtime, configuration, and
diagnostics.

- Source: `A:\Riverview\repo\...`
- Mutable local runtime: `A:\Riverview\runtime\...`

Operational configuration and runtime state must not be placed under
`A:\theestate` or `A:\theestate-data`. Estate Comms8 Blue was used as a proven
reference and provenance implementation only. Riverview has no operational
dependency on Estate runtime, credentials, tools, browser state, or data.

## Designated reasoning boundary

- ChatGPT project: `Riverview_001`
- Designated conversation ID: `6a7f910b-1308-83ea-91a3-654e4a7aa4e7`
- Fixed doorbell wake text: `Riverview doorbell v1: inspect the Riverview MCP mailbox.`

The browser doorbell targets exactly this configured conversation. Playwright
wakes only. Riverview Comms/MCP carries typed operational data. The doorbell
does not scrape or interpret the reasoning response.

## Riverview-owned browser runtime

- Persistent profile: `A:\Riverview\runtime\browser\profile`
- Doorbell configuration: `A:\Riverview\runtime\doorbell\config\doorbell.json`
- CDP: localhost-only port `9225`
- Chrome executable currently used: `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

Canonical preflight commands, run from the repository, are:

```powershell
node tools/riverview_browser_runtime.cjs --preflight
node tools/riverview_doorbell_bridge.cjs --preflight
```

A healthy preflight reports all of the following as true:

```text
browser_runtime=true
cdp_available=true
authenticated_session=true
designated_target_configured=true
exact_target_resolvable=true
fixed_action_available=true
ready=true
```

## Riverview Comms application contract

Application identity: `Riverview Comms`.

The accepted surface contains:

- 15 bounded tools;
- 6 resource templates;
- PostgreSQL-backed reads;
- read-only authority;
- local stdio MCP transport;
- Streamable HTTP MCP transport.

The accepted ingress paths are `/healthz` and `/mcp`.

Riverview Comms explicitly does not expose arbitrary SQL, filesystem access,
shell or process authority, secrets, unrestricted write authority, Undercurrent,
or general browser control.

## Runtime and deployment topology

The local HTTP implementation can be started with the repository's accepted
Python service entry point:

```powershell
python -m riverview.mcp.http_server
```

The manifest and local acceptance tooling are:

```powershell
.venv\Scripts\python.exe tools\riverview_comms_manifest.py
.venv\Scripts\python.exe -m riverview.mcp.live_acceptance
.venv\Scripts\python.exe -m riverview.mcp.http_acceptance
```

The approved external ingress is:

- Hostname: `riverview-comms.ionoge.com`
- Caddy VPS: `64.227.21.54`
- Host identity: `ionoge-control-01`
- Caddy configuration: `/etc/caddy/Caddyfile`
- Riverview loopback backend/tunnel: `127.0.0.1:11825`

Caddy is installed and active. The Riverview route has been added, Caddy
validation passed, and controlled restart passed. The backend and tunnel are
loopback-only. Bearer authentication is service-held; its secret is not stored
in GitHub or ordinary diagnostics. PostgreSQL authority remains the local
Riverview PostgreSQL instance. No server-side replica or file fallback authority
was created.

Deployment recovery backup:

`/etc/caddy/Caddyfile.backup-riverview-comms-20260814T225407Z`

## Current DNS and TLS checkpoint

At the dated deployment checkpoint represented by this document,
`riverview-comms.ionoge.com` resolves publicly to:

- A: `185.146.167.203`
- AAAA: `2a07:7800:1::203`

The approved Riverview Caddy destination is `64.227.21.54`; DNS therefore does
not yet point to the approved deployment host. HTTP currently redirects toward
HTTPS, but TLS certificate completion on `64.227.21.54` is blocked until DNS is
corrected. This is a DNS/TLS boundary issue, not an MCP or backend authority
failure.

Detailed symptom, diagnostic, repair, and verification procedures remain in
[`RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md`](troubleshooting/checkpoints/RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md).

The next external action is to update only the DNS records for
`riverview-comms.ionoge.com` so the approved public destination is
`64.227.21.54`. Handle AAAA deliberately: verify whether an approved IPv6
address exists for `ionoge-control-01`, or remove the stale/incorrect AAAA
record. Do not invent an IPv6 value.

## Recovery and troubleshooting

This document records durable architecture and the current deployment snapshot;
it does not replace the operational troubleshooting checkpoints.

- [Troubleshooting index](troubleshooting/README.md)
- [Comms service runtime](troubleshooting/checkpoints/RIV-COMMS-0002_SERVICE_RUNTIME.md)
- [HTTPS, authentication, and registration](troubleshooting/checkpoints/RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md)
- [Browser doorbell and end-to-end acceptance](troubleshooting/checkpoints/RIV-PLY-0002_BROWSER_DOORBELL_END_TO_END.md)
- [Promotion evidence](troubleshooting/checkpoints/RIV-RDM-0007_PROMOTION_EVIDENCE.md)

## Next bounded continuation

After DNS convergence:

1. Allow and verify Caddy ACME certificate issuance.
2. Run external HTTPS `/healthz` acceptance.
3. Run unauthenticated and incorrect-bearer rejection tests.
4. Run authenticated external `/mcp` acceptance.
5. Register Riverview Comms in ChatGPT using the accepted Comms8 Blue application pattern.
6. Verify Riverview Comms is visible and usable in the designated `Riverview_001` conversation.
7. Reconfirm browser and doorbell preflight.
8. Create one real correlated RV-008.3 mailbox request.
9. Ring the already-authorized fixed doorbell once.
10. Verify typed mailbox/MCP/River evidence.
11. Promote RV-008.3 only after genuine end-to-end success.
12. Evaluate RV-004.5 dependency readiness without starting RV-004.5.

## Roadmap checkpoint snapshot

Authoritative operational state at this deployment checkpoint:

- RV-005.2: completed
- RV-008.1: completed
- RV-008.2: completed
- RV-008.3: pending
- RV-004.5: pending

This is a dated recovery snapshot, not a replacement for PostgreSQL authority.
PostgreSQL remains the authoritative operational state and must be queried for
current status and any roadmap transition.

## Provenance

The external deployment pattern was informed by the working Estate Comms8 Blue
implementation. That system is reference material only; Riverview's source,
runtime, configuration, service, browser state, credentials, and operational
data remain Riverview-owned.
