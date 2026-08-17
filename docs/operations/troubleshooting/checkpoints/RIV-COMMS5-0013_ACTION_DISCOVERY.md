# RIV-COMMS5-0013 — ChatGPT action-discovery compatibility boundary

## Symptom

The authenticated public Comms5 endpoint initializes and `tools/list` returns
successfully, but the connected ChatGPT app displays no actions.

## Distinguishing probe

Compare the public `tools/list` result with a working Riverview MCP app. For
every tool verify a valid name, non-empty description, object `inputSchema`,
declared properties for required inputs, supported JSON Schema constructs, and
a bounded MCP response. Do not treat HTTP 200 or tool count alone as action
discovery acceptance.

## Known failure

A tool may be technically enumerable while exposing an opaque arbitrary
`request` object such as `{"additionalProperties": true}`. This is valid JSON
Schema but is not a usable action contract for all MCP action scanners and may
cause the entire action surface to be rejected.

## Repair

Keep the authoritative Comms5 service request dictionaries and normalize only
the MCP wrapper signatures into explicit bounded fields. Do not create a second
workflow, weaken authorization, or modify Comms4.

## Verification

Validate local generated schemas and then repeat `initialize`,
`notifications/initialized`, and `tools/list` through the public endpoint.
Refresh the existing ChatGPT app's actions and invoke the read-only
`comms5_help` action. A connected app with no visible actions is not accepted.

## Do not

Do not infer ChatGPT action support from a Python MCP client alone, do not
return secrets or protected payloads while debugging, and do not create a new
app merely to conceal a stale action scan.
