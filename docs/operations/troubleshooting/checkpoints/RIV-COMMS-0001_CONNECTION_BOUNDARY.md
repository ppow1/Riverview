<!-- Version: 0.10.0 -->
# RIV-COMMS-0001 - Riverview Comms connection boundary

Owner: Riverview Comms transport owner.

Input: a named `Riverview Comms` Streamable HTTP registration pointing at the
versioned `/mcp` endpoint.

Output: the designated ChatGPT conversation can list the fixed read-only tools
and retrieve bounded PostgreSQL-backed projections.

Authoritative state: PostgreSQL for operational data; GitHub for source and
application version; the Comms registration for connection state.

Failure classes: service unavailable, registration absent, unauthenticated or
unapproved ingress, protocol/version mismatch, PostgreSQL unavailable,
projection failure, or prohibited tool exposure.

Distinguishing probes: run `python -m riverview.mcp.live_acceptance` for the
stdio model; run the Streamable HTTP protocol acceptance against the configured
loopback endpoint; then inspect only the designated ChatGPT conversation for
the exact `Riverview Comms` identity and bounded position/mailbox retrieval.

Smallest safe repair: restore the fixed transport or approved registration
metadata. Do not add arbitrary SQL, generic writes, browser control, secrets,
or a file-state fallback.

Recovery verification: enumerate the exact allowlist, call current position and
mailbox projections, verify PostgreSQL failure classification, and capture
versioned metadata-only evidence.

Provenance: Estate Comms8 Blue was the primary reference for the exact ingress
shape (HTTPS, `/mcp`, `/healthz`, bearer from service environment, loopback
upstream, bounded request body, and candidate acceptance). IONOGE Comms9 and
other Comms8 surfaces were secondary comparison material. Riverview tools and
authority are its own implementation.

Applicable version: 0.10.0.

Escalation boundary: stop for missing approved HTTPS hosting, external
ChatGPT workspace/admin registration permission, authentication, or any
request to widen authority.
