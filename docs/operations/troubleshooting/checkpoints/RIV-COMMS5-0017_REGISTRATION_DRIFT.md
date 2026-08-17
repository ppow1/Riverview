# RIV-COMMS5-0017 — Callable manifest and registry drift

## Symptom

Comms5 `help` or `capabilities` advertises an operation, but the external
callable manifest omits it, or a mutation is published with a stale opaque
`request` schema.

## Distinguishing probe

Compare three bounded projections from the same revision:

1. `Comms5Service.capabilities()` operation names;
2. `mcp._tool_manager.list_tools()` names and input schemas;
3. `tools.riverview_comms5_manifest.TOOLS` and `TOOL_SCHEMAS`.

The sets and mutation property/required-field projections must agree. Then
repeat `initialize`, `notifications/initialized`, and `tools/list` over the
approved public endpoint.

## Known failure

A hand-maintained connector manifest omitted newly added lifecycle tools and
could not prove the published mutation schemas matched the callable registry.

## Smallest repair

Derive the packaging manifest from the authoritative FastMCP registry. Do not
add a second operation table, alter Comms5 lifecycle semantics, or weaken
Steward authorization.

## Verification

Run the Comms5 registry/schema tests and confirm the public endpoint exposes all
15 tools, including `comms5_cancel_draft` and `comms5_supersede_seed`, with flat
top-level mutation fields.

## Do not

Do not promote, cancel, or supersede a seed to test registration. Do not edit
PostgreSQL, credentials, Caddy, Comms4, or protected payloads to compensate for
manifest drift.
