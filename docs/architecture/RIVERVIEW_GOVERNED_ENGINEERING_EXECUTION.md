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

The named adapter uses Codex CLI's `read-only` sandbox for inspection and
`workspace-write` sandbox for `bounded_write`; it never accepts shell text from
PostgreSQL or exposes a generic execution operation through MCP.
