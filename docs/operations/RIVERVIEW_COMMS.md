# Riverview Comms

Version: 0.18.0
Checkpoint date: 2026-08-15
Status: external MCP accepted; RV-004.5 and RV-008.4 are complete; the bounded
autonomous control-plane foundation is implemented locally; RV-008.5 and RV-008.6
are complete with durable acceptance evidence.

## Purpose and authority

Riverview Comms is the Riverview-owned, bounded application surface for the
designated reasoning conversation. It exposes PostgreSQL-backed operational
projections through the accepted Riverview MCP implementation. PostgreSQL is
authoritative operational state; GitHub is authoritative source and history.

The application is read-oriented. Conversation text, the MCP transport, and the
browser doorbell do not create execution authority.

## Ownership

Riverview owns all Riverview operational source, runtime, configuration, and
diagnostics.

- Source: `A:\Riverview\repo\...`
- Mutable local runtime: `A:\Riverview\runtime\...`

Operational configuration and runtime state must not be placed under
`A:\theestate` or `A:\theestate-data`. Estate Comms8 Blue was used as a proven
reference and provenance implementation only. Riverview has no operational
dependency on Estate runtime, credentials, tools, browser state, or data.

## Designated reasoning boundary

- ChatGPT project: `Riverview_001`
- Designated conversation ID: `6a804df2-a580-83ea-addc-753a6dc93f75`
- Fixed doorbell wake text: `Riverview doorbell v1: inspect the Riverview MCP mailbox.`

The browser doorbell targets exactly this configured conversation. Playwright
wakes only. Riverview Comms/MCP carries typed operational data. The doorbell
does not scrape or interpret the reasoning response.

## Riverview-owned browser runtime

- Persistent profile: `A:\Riverview\runtime\browser\profile`
- Doorbell configuration: `A:\Riverview\runtime\doorbell\config\doorbell.json`
- CDP: localhost-only port `9225`
- Chrome executable currently used: `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

Canonical preflight commands, run from the repository, are:

```powershell
node tools/riverview_browser_runtime.cjs --preflight
node tools/riverview_doorbell_bridge.cjs --preflight
```

A healthy preflight reports all of the following as true:

```text
browser_runtime=true
cdp_available=true
authenticated_session=true
designated_target_configured=true
exact_target_resolvable=true
fixed_action_available=true
ready=true
```

## Riverview Comms application contract

Application identity: `Riverview Comms`.

The accepted surface contains:

- 19 bounded tools, including the classification-filtered `mailbox_requests` read
  and fixed reasoning-consumer writes: `mailbox_acknowledge`, `mailbox_claim`,
  and `mailbox_submit_advisory_response`;
- 6 resource templates;
- PostgreSQL-backed reads;
- read-only projections plus bounded typed mailbox-write authority;
- local stdio MCP transport;
- Streamable HTTP MCP transport.

The accepted ingress paths are `/healthz` and `/mcp`.

The bounded reasoning write contract is:

- `mailbox_acknowledge(request_id, correlation_id)`;
- `mailbox_claim(request_id, correlation_id, lease_seconds)`;
- `mailbox_submit_advisory_response(request_id, correlation_id, summary,
  evidence_refs)`.

These operations are fixed to the designated `chatgpt:riverview_001` consumer,
accept only River-classified requests, preserve correlation, enforce leases and
payload bounds, and never provide a generic state setter. The advisory response
operation fixes its category to `advice` and escalation to `false`; it accepts
only an existing active reasoning claim. A response completes the request
transactionally. Timeout expiry and exactly-once Steward escalation
are performed by the bounded mailbox service, not by arbitrary ChatGPT input.

## Grace response-consumption contract

RV-008.4 consumes durable responses through
`riverview.grace.responses.GraceResponseConsumer`. Migration `0013` stores one
consumption per `response_id`, preserving request/correlation identity,
consumer/version, objective context, evaluation outcome, and timestamp.

Grace accepts only completed River-classified responses from the designated
reasoning producer with the `rv-008.4-response-v1` envelope and required
evidence. Supported categories are `advice`, `escalation`, and `seed_result`;
only bounded non-escalating advice produces the declared `advisory_accepted`
objective outcome. Consumption retries reconcile to the original consumption
row and do not duplicate objective progression or River events.

This contract does not submit Steward seeds, create work, dispatch providers,
run momentum evaluation, mutate the roadmap, or grant conversation text
execution authority. A Steward seed remains a later RV-008.5 input, not a work
order.

The currently deployed external schema lists 19 tools. The local source now adds
the bounded `submit_steward_seed` draft operation (20 local tools); deployment and
conversation schema refresh are required before that operation is externally
available. A real RV-004.5
request was created and its fixed doorbell wake succeeded, but the designated
conversation did not acknowledge or claim it during the bounded observation
window. No second wake was sent and no response was fabricated.

That request is now outside its expiry deadline because schema refresh completed
after mailbox expiry. It remains historical evidence only and must not be
revived; a fresh bounded request is required for a subsequent live acceptance.

The fresh recovery request was visible and its one fixed wake succeeded. The
designated conversation subsequently acknowledged and claimed it, proving that
the refreshed application can use the bounded write path. Its response write
was then blocked twice by the ChatGPT platform safety layer before Riverview
accepted the call. The repair is the narrower
`mailbox_submit_advisory_response` contract; the request remains historical and
must not be revived after expiry.

The current schema-binding diagnostic is separate: ChatGPT Apps administration
shows the repaired advisory tool, while existing conversations may continue to
receive the prior tool snapshot. Riverview's public endpoint advertises only
the repaired tool; conversation-level invalidation is a ChatGPT platform
boundary unless an explicit refresh control is provided.

Riverview Comms explicitly does not expose arbitrary SQL, filesystem access,
shell or process authority, secrets, arbitrary writes, roadmap mutation,
work-order creation, Undercurrent, or general browser control. The three
mailbox writes are fixed typed operations for the designated
`chatgpt:riverview_001` reasoning consumer and preserve request/correlation,
classification, payload, lease, and lifecycle bounds.

## Grace and local Codex control plane

The autonomous engineering path is Riverview-owned and PostgreSQL-backed:

`Grace evaluation -> measured capability -> bounded execution envelope -> named
adapter -> typed result -> independent reconciliation -> Grace evidence`.

Migration `0014` stores measured capabilities and capacity, replay-safe execution
envelopes, typed execution results, Grace transition evaluations, and explicit
checkpoints. The registered local capability is `codex.engineering.v1`, provided by
`codex-cli-local`; its current measured slot is one, with no OpenAI API route.
The adapter launches the installed local Codex CLI through the fixed `codex.cmd`
entry point, binds execution to the Riverview Git repository, enforces the expected
base SHA, relative allowed paths, bounded instruction, and hard timeout, and never
claims publication without independent verification.

The first real local acceptance envelope used the same persisted correlation after
an initial Windows executable-resolution failure, created only
`tests/fixtures/autonomy/README.md`, completed the bounded tests, and was
independently reconciled to the allowed path. Its durable evidence is in
`execution_envelopes`/`execution_results`; it did not commit or push.

Grace momentum records readiness, stale lease checkpoints, bounded retry decisions,
and Steward routing without silently changing objective intent. A retry-safe failure
is limited to one retry; otherwise a durable checkpoint is required. The named
Codex adapter is not exposed through MCP as a generic execution operation.

A second real continuation objective completed through the same path with
objective `autonomous-loop.continuation.e0ec4851-6385-479a-b6a9-4156a22e78c4`,
correlation `36009669-1d48-47dc-bd22-d8d2b6a712c6`, execution
`5a6f7154-e9e4-43d6-8c23-6f6623e91d0f`, and typed result
`c1a7919e-46ec-4cca-a323-ce3998a31f1f`. Grace completed declared plan, execute,
and reconcile stages; Codex changed only `tests/fixtures/autonomy/CONTINUATION.md`.
Publication of that fixture remains separately verified before the result is treated
as a published source claim.

Migration `0015` adds the bounded Steward seed draft boundary. The MCP
`submit_steward_seed` operation creates exactly one idempotent draft for the fixed
consumer `chatgpt:riverview_001`; only an explicit `steward` confirmer can promote
that draft through Grace into an objective. Seed
`c68f4a7e-a442-40db-ae7f-229978911b2f` was explicitly confirmed and promoted into
objective `24c5081b-b82c-4a88-b1cb-8c3f9ab952d4` under correlation
`696dc369-a86e-4264-b5de-d94762d8483f`. A seed is never a work order.

Migration `0016` adds the optional declared action binding to objective stages.
Grace may enqueue only that stage's already-registered approved action, with a
stable objective/stage idempotency key; no generic state setter or database command
is accepted. A real momentum acceptance evaluated and enqueued `relay.noop`, the
restricted runner completed it, and Grace finalized the objective. Its durable
work-order evidence is `f5250284-584d-4448-8890-5035af378d59` with correlation
`05080b5e-92cc-425d-8477-f49626d05700`.

Migration `0017` adds exclusive relative-path lanes and typed reconciliation
records. An overlapping lane was rejected and safely reacquired after release; the
same continuation correlation also produced one durable conflicting-result decision
(`db4676fb-8fe4-47e6-a204-1489e5fb6619`) without executing the conflict. Capacity
exhaustion paused dispatch and resumed after fresh telemetry.

Migration `0018` adds the bounded `bridge_recovery_attempts` state machine for
RV-008.6. It preserves request/correlation identity across retry, records River
failure and recovery events, and creates at most one Steward escalation when a
bounded retry budget is exhausted. It does not add browser authority or create
mailbox requests.

## Runtime and deployment topology

The local HTTP implementation can be started with the repository's accepted
Python service entry point:

```powershell
python -m riverview.mcp.http_server
```

The manifest and local acceptance tooling are:

```powershell
.venv\Scripts\python.exe tools\riverview_comms_manifest.py
.venv\Scripts\python.exe -m riverview.mcp.live_acceptance
.venv\Scripts\python.exe -m riverview.mcp.http_acceptance
```

The approved external ingress is:

- Hostname: `riverview-comms.ionoge.com`
- Caddy VPS: `64.227.21.54`
- Host identity: `ionoge-control-01`
- Caddy configuration: `/etc/caddy/Caddyfile`
- Riverview loopback backend/tunnel: `127.0.0.1:11825`

Caddy is installed and active. The Riverview route has been added, Caddy
validation passed, and controlled restart passed. The backend and tunnel are
loopback-only. Bearer authentication is service-held; its secret is not stored
in GitHub or ordinary diagnostics. PostgreSQL authority remains the local
Riverview PostgreSQL instance. No server-side replica or file fallback authority
was created.

The reverse proxy normalizes the upstream `Host` header to
`127.0.0.1:11825`. This is required by the loopback MCP service and does not
change the public Riverview hostname or external TLS identity.

Deployment recovery backup:

`/etc/caddy/Caddyfile.backup-riverview-comms-20260814T225407Z`

## ChatGPT Comms acceptance checkpoint

The application `Riverview Comms` is connected at
`https://riverview-comms.ionoge.com/mcp` for the designated `Riverview_001`
conversation. Through the real ChatGPT/MCP boundary, `current_position` and
`roadmap_revision` returned PostgreSQL-backed state; the observed revision was
`RV-MASTER-2026-08-14`, and RV-008.3 was observed as pending with its Steward
checkpoint. PostgreSQL, not GitHub conversation context, remains operational
authority.

The single authorized doorbell attempt succeeded at the browser boundary with
attempt identity `ad57b894-5960-420d-be76-1ea33bd62212`. A bounded typed-state
observation found no acknowledgement, claim, response, or completion event.
That downstream behavior is not an RV-008.3 acceptance requirement: reasoning
response return belongs to RV-008.4, and the full correlated mailbox loop
belongs to RV-004.5. The request remains durable evidence of the wake boundary.

## Current DNS and TLS checkpoint

At the 2026-08-14 deployment checkpoint represented by this document,
`riverview-comms.ionoge.com` resolves authoritatively and through the checked
public resolvers to:

- A: `64.227.21.54`
- AAAA: no answer

The domain-wide wildcard IPv6 record is not inherited by this explicit hostname,
so clients do not receive the unrelated IPv6 destination for Riverview Comms.
Caddy obtained a valid certificate for the hostname after DNS convergence.
Public `/healthz` returns `200`; missing and incorrect bearer credentials are
rejected with `401`; authenticated external MCP initialization, tool/resource
discovery, and bounded PostgreSQL-backed reads pass.

Detailed symptom, diagnostic, repair, and verification procedures remain in
[`RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md`](troubleshooting/checkpoints/RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md).

The next bounded action is the RV-008.4 reasoning-response-return waypoint.
Do not ring a second time for this request or add write authority to the
read-only Comms surface. DNS records and the domain-wide wildcard/root records
must not be changed.

## Recovery and troubleshooting

This document records durable architecture and the current deployment snapshot;
it does not replace the operational troubleshooting checkpoints.

- [Troubleshooting index](troubleshooting/README.md)
- [Comms service runtime](troubleshooting/checkpoints/RIV-COMMS-0002_SERVICE_RUNTIME.md)
- [HTTPS, authentication, and registration](troubleshooting/checkpoints/RIV-COMMS-0003_HTTPS_AUTH_REGISTRATION.md)
- [Browser doorbell and end-to-end acceptance](troubleshooting/checkpoints/RIV-PLY-0002_BROWSER_DOORBELL_END_TO_END.md)
- [Promotion evidence](troubleshooting/checkpoints/RIV-RDM-0007_PROMOTION_EVIDENCE.md)
- [Full-loop mailbox](troubleshooting/checkpoints/RIV-MCP-0009_FULL_LOOP_MAILBOX.md)
- [Grace reasoning-response consumption](troubleshooting/checkpoints/RIV-GRC-0003_REASONING_RESPONSE_CONSUMPTION.md)
- [Autonomous control-plane and Codex adapter](troubleshooting/checkpoints/RIV-EXE-0001_AUTONOMOUS_CONTROL_PLANE.md)
- [Grace momentum and checkpoint routing](troubleshooting/checkpoints/RIV-GRC-0004_MOMENTUM_CONTROL.md)
- [Capability registry and dispatch](troubleshooting/checkpoints/RIV-CAP-0001_CAPABILITY_DISPATCH.md)
- [Lane ownership and result reconciliation](troubleshooting/checkpoints/RIV-CAP-0002_LANE_RECONCILIATION.md)
- [Steward seed and schema boundary](troubleshooting/checkpoints/RIV-MCP-0010_STEWARD_SEED_SCHEMA.md)
- [Bridge replay and recovery](troubleshooting/checkpoints/RIV-MCP-0011_BRIDGE_REPLAY_RECOVERY.md)

## Next bounded continuation

RV-008.5 seed promotion and RV-008.6 bridge replay/recovery are complete. The
recovery path is intentionally bounded: retry the same recovery identity while it
is retryable, preserve correlation, and route exhausted recovery to its durable
Steward checkpoint. Do not create replacement requests to mask a bridge failure.
The next waypoint must be recomputed from authoritative PostgreSQL state.

## Roadmap checkpoint snapshot

Authoritative operational state at this deployment checkpoint:

- RV-005.2: completed
- RV-008.1: completed
- RV-008.2: completed
- RV-008.3: completed
- RV-004.5: completed
- RV-008.4: completed
- RV-008.5: completed by explicit Steward-confirmed seed promotion
- RV-008.6: completed by induced retry/recovery and exactly-once escalation acceptance
- RV-005.3: completed
- RV-005.4: completed
- RV-005.5: completed at its authorized checkpoint
- RV-005.6: completed at its authorized checkpoint
- RV-006.1: completed
- RV-006.2: completed
- RV-006.3: completed at its authorized checkpoint
- RV-007.1: completed
- RV-007.2: completed
- RV-006.4: completed
- RV-006.5: completed
- RV-006.6: completed
- RV-007.3/007.4: pending; hardware/provider evidence not present
- RV-007.6: pending until all declared adapter dependencies complete

This is a dated recovery snapshot, not a replacement for PostgreSQL authority.
PostgreSQL remains the authoritative operational state and must be queried for
current status and any roadmap transition.

## Provenance

The external deployment pattern was informed by the working Estate Comms8 Blue
implementation. That system is reference material only; Riverview's source,
runtime, configuration, service, browser state, credentials, and operational
data remain Riverview-owned.
