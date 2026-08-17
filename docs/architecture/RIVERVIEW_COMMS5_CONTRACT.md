# Riverview Comms5 contract

Comms5 is the separate `riverview-comms-contract:5.0` MCP surface exposed by
`python -m riverview.mcp.comms5_server`. It is a bounded governed ingress and
read projection over the existing PostgreSQL/River, Steward seed, objective,
Grace/CME, Relay, execution, and diagnostics stores.

It does not replace Comms4 and does not own a workflow state machine. Client
identity is provenance only. `submit_steward_seed` creates a draft, and
`store_specification` creates a durable classified reference; neither promotes
work. Promotion requires explicit authenticated Steward authorization and uses
the canonical `StewardSeedStore.confirm_and_promote` path.

The machine-readable `comms5_help` response is the discovery authority. It
publishes operation schemas, bounds, classifications, authorization classes,
examples, stable errors, idempotency rules, and explicit do-not guidance.
`seed_status`, `seed_lineage`, `objective_status`, and `comms5_cme_status`
return bounded metadata only. Large specification content, credentials, and
protected payloads are never returned by these projections.

The repository includes a connector template at
`config/riverview-comms5.example.json`. External connector installation is a
deployment action and is not claimed merely because the source entrypoint
exists.
