# Comms5 OAuth connectivity

Status: implemented in source; production deployment and ChatGPT acceptance are
not yet verified.

## Purpose and authority mapping

This increment makes the existing `https://riverview-comms.ionoge.com/comms5/mcp`
Streamable HTTP endpoint usable by ChatGPT's OAuth connector without replacing
Comms5, its tools, or its authorization rules. Comms4 remains on `/mcp`.

The authorization page asks the Steward to prove possession of the existing
Steward-controlled Comms5 connector credential. The OAuth service compares it
in constant time and does not persist or log it. Caddy authenticates its
loopback authorization hop with a separate proxy key; the service rejects
authorization pages reached without that key, even from another local process.
The resulting access token represents the existing `steward` transport
principal. Caddy validates each token and injects the same trusted Comms5
principal marker already consumed by `comms5_server.py`. The bearer is not
accepted as authority by itself: existing Comms5 tool contracts, explicit
confirmation fields, authoritative database checks, and idempotency continue to
decide each action.

The OAuth service reads the existing Comms5 client credential and the new
random proxy-hop key from `/etc/riverview/comms5-oauth.env`. The same file must
be loaded by the Caddy systemd service so its Caddyfile can inject the proxy
key. It must be root-owned and mode 0600; no values belong in the repository.

This is a migration-compatible path: the existing static-bearer Caddy branch
continues to work while OAuth is commissioned. OAuth does not create a new
resident, grant, work-order authority, or tool restriction.

## OAuth contract

- Issuer: `https://riverview-comms.ionoge.com`
- MCP resource: `https://riverview-comms.ionoge.com/comms5/mcp`
- Protected-resource metadata: `/.well-known/oauth-protected-resource`
- Authorization-server metadata: `/.well-known/oauth-authorization-server`
- Authorization: `/oauth/authorize`
- Token: `/oauth/token`
- Dynamic client registration: `/oauth/register`
- Revocation: `/oauth/revoke`
- Internal Caddy token check: `/oauth/verify` (loopback only; not publicly routed)
- Scope: `comms5`
- Flow: public client, authorization code, PKCE S256, exact `resource`
- ChatGPT redirect: `https://chatgpt.com/connector_platform_oauth_redirect`
- Compatibility callback accepted at registration:
  `https://chatgpt.com/connector/oauth/{callback_id}`

Every Comms5 tool advertises ChatGPT's OAuth `securitySchemes` metadata for the
`comms5` scope. The issuer advertises RFC 9207 issuer identification and returns `iss` in
successful authorization responses. Tokens are opaque, random bearer values;
only SHA-256 token digests are stored. Access tokens last one hour. Where the
registered client requests refresh tokens, refresh tokens last 30 days and
rotate on use. Authorization codes expire after three minutes and are consumed
once within a database transaction. The exact resource and `comms5` scope are
required at authorization, exchange, refresh, and token verification.

OAuth protocol state is stored in a dedicated SQLite file under the OAuth
service's systemd `StateDirectory`. This is limited to OAuth DCR clients,
authorization forms/codes, and revocable token digests. Riverview objectives,
authority, and Comms5 operational data remain in the existing PostgreSQL
authority stores. The service binds only to `127.0.0.1:11827` on Ionoge.

## Intended request path

```text
ChatGPT
  -> HTTPS Caddy on Ionoge
  -> /oauth/* and OAuth metadata -> loopback OAuth service :11827
  -> /comms5/mcp -> Caddy forward_auth -> loopback OAuth service /oauth/verify
  -> existing reverse tunnel :11826 -> Camrui Comms5 /mcp
```

The legacy static Comms5 bearer branch stays available during migration. The
OAuth MCP branch reaches the existing Camrui backend only after `forward_auth`
returns success. Caddy then replaces the public bearer with the existing
upstream service credential and injects the trusted `steward` principal. The
public Caddy matchers do not expose `/oauth/verify`.

The code and configuration template do not establish that the current Ionoge
reverse tunnel still reaches Camrui. The live `:11826` upstream must be checked
from Ionoge before the Caddy change is activated.

## Files and local verification

- `src/riverview/mcp/comms5_oauth.py` — PKCE, DCR, token persistence, expiry,
  refresh rotation, exact audience/scope checks, and Steward credential proof.
- `src/riverview/mcp/comms5_oauth_server.py` — loopback HTTP endpoints and
  sanitized logging.
- `deploy/systemd/riverview-comms5-oauth.service` — isolated loopback service.
- `config/riverview-comms5-ingress.Caddyfile.example` — OAuth discovery,
  forward-auth, and the preserved Comms5 route.
- `tests/test_comms5_oauth.py` and
  `tests/test_comms5_oauth_ingress_contract.py` — protocol and ingress tests.

Run:

```sh
PYTHONPATH=src python3 -m pytest -q tests/test_comms5_oauth.py tests/test_comms5_oauth_ingress_contract.py
systemd-analyze verify deploy/systemd/riverview-comms5-oauth.service
```

The package's dependency-backed Comms5 regression suite also requires the
declared `mcp` dependency. A missing local package is an environment failure,
not evidence that those tests passed.

## Controlled commissioning sequence

1. From an already trusted operator SSH configuration, inspect the current
   Ionoge Caddy service, routes, listener `:11826`, and reverse tunnel. Never
   accept an unverified SSH host key.
2. Preserve the live Caddyfile, unit state, and service release pointer. Verify
   that the current static Comms5 route and Camrui tunnel both pass an
   authenticated MCP initialize/tools-list probe.
3. Stage the OAuth source under
   `/opt/riverview-comms5-oauth/releases/<commit>` and preserve `current`.
4. Create the root-owned mode-0600 `/etc/riverview/comms5-oauth.env` with the
   already-approved Comms5 login credential and a newly generated random
   `RIVERVIEW_COMMS5_OAUTH_PROXY_KEY`. Do not show either value in command
   output. Add this file as an `EnvironmentFile` to both the OAuth service and
   the existing Caddy systemd service, then run `systemd-analyze verify` on
   both units before activation. Do not change the upstream Comms5 credential.
5. Install the service unit and start the OAuth listener on loopback. Verify
   both metadata documents, `/healthz`, invalid-token rejection, and DCR using
   only a test client in a disposable SQLite database.
6. Apply the Caddy fragment beside the unchanged Comms4 block. Validate Caddy
   configuration before reload. Confirm the `:11826` upstream remains the
   Camrui Comms5 service.
7. Verify public unauthenticated `/comms5/mcp` returns a bearer challenge with
   the protected-resource URL, OAuth discovery returns the exact issuer and
   resource, and the legacy static credential still initializes Comms5.
8. In the ChatGPT connector UI, set Server URL to the public Comms5 endpoint,
   select OAuth, use DCR if the UI offers the choice, complete the Steward
   credential login, discover the existing tool set, and invoke
   `comms5_help`. Separately exercise one already-authorized operation only
   after the read-only connectivity acceptance succeeds.

No ChatGPT-side acceptance, current upstream health, or production deployment
is claimed by source tests.

## Rollback

Restore the exact preserved Caddyfile, run `caddy validate`, then reload Caddy
using the host's established service procedure. Stop and disable only
`riverview-comms5-oauth.service`, restore its predecessor active pointer if
one existed, and verify that the original static-bearer Comms5 route and
unchanged Comms4 route still work. Keep the OAuth SQLite state and release
directory for diagnosis; do not delete them during rollback.

## Current evidence boundary

On 2026-10-16, the public Comms5 MCP URL returned HTTP 401 and the public
protected-resource discovery path returned Caddy HTTP 404. DNS resolved the
hostname to `64.227.21.54`. The available Linux SSH alias
`ionoge-control-01` resolves to that host with `StrictHostKeyChecking ask`, but
no trusted known-host entry was present in the inspected SSH trust files. No
SSH authentication was attempted and no host key was accepted. Therefore the
live Caddy configuration, tunnel, and upstream-to-Camrui route remain
unverified and unchanged.
