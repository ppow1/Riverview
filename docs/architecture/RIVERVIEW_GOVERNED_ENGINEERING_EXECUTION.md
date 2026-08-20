# Governed engineering execution

Riverview has two intentionally different surfaces: the MCP Relay and status
projections are read-only, while the Steward-approved engineering path is a
governed execution path.

`codex.engineering.v1` is the registered local Codex engineering capability and
action. Its typed formation contract selects the mode: `read_only` permits
inspection only, while `bounded_write` permits repository changes only within
the same approved contract. `bounded_write` is not a shell permission or a
wildcard. It is valid only after explicit Steward approval creates a durable
authority grant bound to the exact specification version/hash, seed, objective,
and stage.

The full path is `Comms5 store_specification -> Steward approval -> Grace
formation -> Engineering Intent -> Relay declared action -> named Codex
adapter -> independent reconciliation -> evidence/completion`.

Every formed intent is bound to repository identity/root, expected base SHA,
bounded instruction, allowed paths, acceptance criteria, evidence requirements,
capability/action identity, timeout, and write policy. Grace, Relay, and Codex
may consume these bounds but may not broaden them. A draft or stored
specification without explicit Steward approval is not executable. A stale base
SHA, invalid policy, missing evidence, out-of-scope path, failed acceptance, or
failed reconciliation is fail-closed. Publication remains a separate canonical
step and may claim a commit or remote SHA only after independent verification.

## Stale approved bases

`RIV-EXE-0008` is an execution checkpoint, not permission to silently rewrite
an Engineering Intent. Riverview may assess the Git ancestry and bounded diff
from the approved base to the current repository head. A descendant with no
change to the allowed paths or execution dependencies may be revalidated; a
change to governance/ingress code requires Pat's narrow confirmation of the
new base binding. Scope, capability, action, policy, instruction, criteria,
evidence requirements, repository identity, and authority lineage remain
immutable. Material scope or execution drift fails closed for a new
specification version or renewed approval.

An approved revalidation creates a successor work-order attempt and a fresh
execution envelope bound to the new verified base. The failed order and its
execution evidence remain immutable and visible. Revalidation never runs
Codex, bypasses Grace or Relay, or lets a client choose a base SHA.

The named adapter uses Codex CLI's `read-only` sandbox for inspection and
`workspace-write` sandbox for `bounded_write`; it never accepts shell text from
PostgreSQL or exposes a generic execution operation through MCP.

## One-shot Steward approval

For the external Comms5 path, the authenticated Steward-controlled connector
bearer is accepted by the Caddy ingress. Caddy then overwrites the upstream
`X-Riverview-Comms5` and `X-Riverview-Comms5-Principal: steward` attestation
headers. The Comms5 tool ignores `authenticated_principal` in the request body
for promotion authority and accepts `explicit_steward_confirmation` only when
that server-injected attestation is present. A local STDIO client or arbitrary
client string cannot self-declare Steward.

One successful promotion creates one durable authority grant bound to the
exact specification ID, version, content hash, formation contract, seed,
objective, stage, correlation, causation, and approval operation. Grace,
Engineering Intent, Relay, Codex, and reconciliation consume that grant; they
do not request another human approval for the same scope.
