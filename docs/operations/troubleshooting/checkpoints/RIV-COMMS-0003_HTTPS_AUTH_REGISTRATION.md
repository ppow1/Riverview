<!-- Version: 0.10.0 -->
# RIV-COMMS-0003 - HTTPS ingress, authentication, and ChatGPT registration

Owner: Riverview ingress and application-registration owner.

## SYMPTOM

DNS does not resolve, TLS fails, Caddy rejects its configuration, `/healthz`
times out, `/mcp` returns 404/502/401 unexpectedly, or ChatGPT cannot discover
`Riverview Comms`.

## LIKELY BOUNDARY

DNS/TLS/Caddy, bearer authentication, or ChatGPT workspace registration. A
local MCP success does not prove this boundary.

## SAFE DIAGNOSTIC

```powershell
Resolve-DnsName riverview-comms.ionoge.com
Invoke-WebRequest https://riverview-comms.ionoge.com/healthz -TimeoutSec 10
```

For an approved host, validate Caddy before reload and probe `/healthz`, then
probe `/mcp` with a secret supplied by the service environment. The probe must
report status only; never print the Authorization header or response body.

Expected classifications:

- missing bearer: `401`;
- wrong bearer: `401`;
- correct bearer with unavailable backend: `502` or equivalent backend failure;
- correct bearer with healthy backend: MCP initialize and tools/list succeed.

## EXPECTED HEALTHY RESULT

DNS and certificate resolve for the approved Riverview hostname; `/healthz`
responds without revealing credentials; unauthenticated MCP is rejected;
authenticated MCP returns `Riverview Comms`, 15 tools, six templates, and
PostgreSQL-backed reads.

## KNOWN FAILURE RESULT

- `RIV-COMMS-0010`: DNS or hostname unavailable.
- `RIV-COMMS-0011`: certificate/TLS failure.
- `RIV-COMMS-0012`: Caddy validation/reload failure.
- `RIV-COMMS-0013`: route or loopback backend unavailable.
- `RIV-COMMS-0014`: missing or incorrect bearer.
- `RIV-COMMS-0015`: request exceeds the 256 KiB ingress bound.
- `RIV-COMMS-0016`: ChatGPT registration/discovery failure.

During this tranche, `riverview-comms.ionoge.com` resolved but HTTPS probes
timed out, and no local Caddy or authorized remote deployment control existed.
This was classified as an external ingress boundary failure, not as MCP health.

Later VPS deployment evidence established that the approved Caddy route on
`64.227.21.54` is active and HTTP requests redirect correctly to HTTPS, but
public DNS still resolves the hostname to `185.146.167.203`. A direct TLS probe
to the approved VPS therefore returned a TLS internal error because the
hostname certificate could not be completed for that destination. This is
`RIV-COMMS-0010`/`RIV-COMMS-0011`, not a backend or MCP failure.

On 2026-08-14, authorized inspection of `ionoge-control-01` confirmed Caddy
configuration validation and the loopback listener, while Caddy's live ACME
attempts failed at the external DNS boundary. HTTP-01 was answered by
`185.146.167.203` with `404`, and TLS-ALPN-01 could not negotiate
`acme-tls/1` through the same stale destination. The approved host therefore
remains healthy but cannot complete certificate issuance until the A/AAAA
records converge. This is verified `RIV-COMMS-0010`/`RIV-COMMS-0011` evidence.

## REPAIR

Provision only an approved Riverview-owned HTTPS host. Install the Caddy route
from `config/riverview-comms-ingress.Caddyfile.example`, keep the bearer in the
service environment, validate configuration, and perform a controlled reload.
Rotate credentials by replacing the service-held secret and the approved
registration binding together; preserve neither value in GitHub, PostgreSQL,
logs, diagnostics, or chat.

When DNS is managed outside the authorized VPS, update only the
`riverview-comms.ionoge.com` A/AAAA destination to the approved Caddy host,
then allow Caddy ACME issuance to complete. Do not change unrelated records.

For ChatGPT, register the exact name `Riverview Comms` and exact approved
`/mcp` endpoint. Do not reuse an Estate or IONOGE application or endpoint.

## VERIFY

Repeat DNS/TLS, unauthenticated, incorrect-bearer, correct-bearer, MCP
initialize, tools/list, resource-template, PostgreSQL read, and authority
checks. Then verify the designated conversation visibly has the exact
`Riverview Comms` application and can retrieve current position and mailbox
projections.

## DO NOT

Do not paste secrets into chat, print them in diagnostics, expose the Python
listener directly, reload shared Caddy without backup/validation, or call a
successful health response proof of ChatGPT registration.

## EVIDENCE

Record hostname, service/application version, status codes, tool/template
counts, and correlation metadata only. Keep ingress logs under the approved
Riverview runtime owner and omit bodies, cookies, and tokens.
