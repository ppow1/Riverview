<!-- Version: 0.10.0 -->
# RIV-COMMS-0002 - Riverview Comms service runtime

Owner: Riverview Comms service owner (`riverview.mcp.http_server`).

## SYMPTOM

The service will not start, the loopback listener is absent, `/healthz` is
unavailable through the ingress, or MCP initialization/tool discovery fails.

## LIKELY BOUNDARY

Python environment, Riverview-owned service process, loopback port, or the
Streamable HTTP protocol—not PostgreSQL data and not ChatGPT registration.

## SAFE DIAGNOSTIC

From `A:\Riverview\repo`:

```powershell
.venv\Scripts\python.exe -m compileall -q src
.venv\Scripts\python.exe -m riverview.mcp.live_acceptance
Get-NetTCPConnection -LocalPort 11825 -State Listen -ErrorAction SilentlyContinue
```

For a local HTTP acceptance, run the service with
`.venv\Scripts\python.exe -m riverview.mcp.http_server`, then run
`.venv\Scripts\python.exe -m riverview.mcp.http_acceptance` in a second
process. Do not bind the service to a non-loopback address.

## EXPECTED HEALTHY RESULT

The stdio and Streamable HTTP acceptances report `status=healthy`, application
`Riverview Comms`, 15 tools, and no prohibited authority. The listener is on
the Riverview-owned loopback service port.

## KNOWN FAILURE RESULT

- `RIV-COMMS-0001`: invalid port or service startup configuration.
- `RIV-COMMS-0002`: attempted non-loopback bind without approved ingress.
- `RIV-COMMS-0005`/`0006`: missing or prohibited HTTP tool surface.
- `RIV-COMMS-0007`: bounded tool call or PostgreSQL projection failed.

The observed local warning about the dependency environment was a non-fatal
Pydantic settings warning; it did not invalidate acceptance.

## REPAIR

Use the repository `.venv`, verify `PYTHONPATH`/editable installation, restore
the fixed entrypoint, and restart only the positively identified Riverview
Comms process. If the port belongs to another process, stop and escalate
rather than terminating it. Repair PostgreSQL connectivity at the database
boundary; do not add file fallback state.

## VERIFY

Rerun both MCP acceptances and confirm the exact application identity, 15-tool
allowlist, six resource templates, bounded reads, and read-only authority.

## DO NOT

Do not expose the raw service publicly, change the bind to `0.0.0.0`, add
arbitrary SQL, or treat a running process without protocol/read evidence as
healthy.

## EVIDENCE

Protocol evidence is metadata-only. Operational data remains PostgreSQL;
source/version remains GitHub. Preserve service diagnostics under
`A:\Riverview\runtime\diagnostics\` without request bodies or secrets.
