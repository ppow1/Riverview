# RIV-UI-0009 — Riverview-owned Open WebUI service boundary

## SYMPTOM

Riverview operator requests reach an unowned service, lack authentication, exceed the bounded schema, or lose reasoning correlation.

## BOUNDARY

RV-010.1 isolated Riverview Open WebUI adapter.

## SAFE DIAGNOSTIC

Probe only loopback `/health`, authenticated `/api/models`, and bounded `/api/chat`; inspect service identity, port, data-path reference, and typed response correlation.

## EXPECTED HEALTHY RESULT

Riverview-owned service identity, isolated runtime/data path, bearer authentication, approved provider-neutral response, and preserved request/correlation IDs.

## REPAIR / VERIFY

First prove that the installed `Riverview Runtime Supervisor` owns the
Operator registration. Its registry identifies
`riverview.operator.live_service`, the working repository, the protected
credential handoff, and the single `127.0.0.1:18082` listener. Use
`Install-RiverviewRuntimeSupervisor.ps1` for migration and the installed
`Riverview Runtime Supervisor` task for restart; do not launch the Python
module directly. Verify the status projection, one launcher/child topology,
health, authenticated model discovery, served source revision, and one bounded
typed request with preserved correlation.

On Windows, `\\Estate Operations Runtime Host` remains a separate Estate
boundary and is not sufficient evidence of Operator ownership. Its action runs
`estate.cli.main operations-runtime host run-foreground`. The Riverview Runtime
Supervisor is the only Riverview top-level owner; CME's internal supervisor is
subordinate and the transport remains a separate managed service identity.
If the unified owner is missing or cannot reconcile a required port, stop and
escalate to the Steward; do not create an unmanaged replacement or invent a
credential.

## DO NOT

Do not reuse Estate Open WebUI state, expose credentials, add shell/SQL
authority, accept browser prose as operational state, treat the broad Estate
host as an Operator supervisor without a launch/ownership probe, or create a
new scheduler/startup path when the approved owner is missing.

## EVIDENCE

Source: `src/riverview/operator/openwebui.py`; test: `tests/test_openwebui_riverview.py`.
