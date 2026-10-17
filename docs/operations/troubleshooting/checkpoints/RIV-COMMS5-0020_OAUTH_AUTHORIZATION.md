# RIV-COMMS5-0020 — ChatGPT OAuth authorization and Comms5 principal

## Trigger

ChatGPT cannot discover OAuth metadata, the browser authorization flow fails,
the token endpoint rejects a code, Caddy denies a valid token, or Comms5 receives
no trusted Steward principal after the OAuth rollout.

## Owning components

- OAuth protocol state and endpoints:
  `src/riverview/mcp/comms5_oauth.py` and
  `src/riverview/mcp/comms5_oauth_server.py`.
- Ionoge loopback OAuth service:
  `deploy/systemd/riverview-comms5-oauth.service` on `127.0.0.1:11827`.
- Public discovery, authentication, and routing:
  `config/riverview-comms5-ingress.Caddyfile.example`.
- Existing governed tools and principal checks:
  `src/riverview/mcp/comms5_server.py` and `src/riverview/mcp/comms5.py`.

## Safe distinguishing checks

1. Confirm DNS resolves the approved Comms hostname and HTTPS terminates at
   Ionoge.
2. From Ionoge, check Caddy service state, OAuth service state, listener
   ownership on `:11827`, Comms5 reverse-tunnel listener on `:11826`, and
   upstream HTTP status without printing environment values or request bodies.
3. Check the protected-resource metadata has the exact resource URI and issuer.
4. Check authorization-server metadata advertises PKCE `S256`, the exact
   issuer, a registration endpoint, and the registered public-client method.
5. Confirm `/oauth/verify` is not externally routed. A valid OAuth bearer should
   pass Caddy forward-auth; missing, expired, wrong-resource, or revoked tokens
   must receive 401 with a protected-resource challenge.
6. Confirm the OAuth flow returns `iss` and that the token exchange echoes the
   exact resource and consumes the code once.
7. Run Comms5 initialize, `tools/list`, and `comms5_help` through the public
   endpoint. Verify a governed write only with an already-authorized operation
   and its existing explicit confirmation contract.

8. If Chrome blocks the Steward form with a `form-action 'self'` violation,
   inspect the generated form action, the final document URL/origin, and all
   response CSP headers. A `self` source is evaluated against the document's
   effective origin (which may be opaque in an embedded authorization view),
   not the server that generated the HTML. The form must post to the absolute
   configured issuer endpoint and the CSP must allow only that issuer origin.
   For cross-origin authorization POSTs, the short-lived transaction cookie
   must retain `Secure` and `HttpOnly` and use `SameSite=None`; the server must
   continue requiring both the transaction cookie and CSRF form token. Do not
   disable CSP or remove the CSRF comparison.

Never print bearer tokens, OAuth codes, cookie values, client secrets, submitted
MCP bodies, or private tool results to logs or evidence.

## Smallest repair

Repair only the failed OAuth metadata, issuer path, loopback service, Caddy
forward-auth mapping, or existing Comms5 tunnel route after preserving the
current Caddyfile and service state. Validate the Caddyfile before reload.
Keep the static Comms5 bearer branch and Comms4 `/mcp` route intact during
recovery.

## Rollback verification

Restore the preserved Caddyfile, validate it, and reload Caddy. Stop only
`riverview-comms5-oauth.service`; retain its release and SQLite state. Verify
the predecessor static-bearer Comms5 route and Comms4 route separately. A
rollback must not alter Comms5/PostgreSQL state or the Comms5 backend process.

## Current evidence status

Source tests exercise metadata, DCR callback restriction, PKCE, one-time code
use, refresh rotation, revocation, invalid-resource rejection, HTTP challenge,
and Caddy mapping. The public endpoint previously returned HTTP 401 while the
protected-resource metadata path returned Caddy HTTP 404. SSH host identity was
not present in the available Linux known-host files; live configuration and
upstream state were therefore not inspected or changed. Current production
status must be rechecked from a trusted operator connection before activation.
