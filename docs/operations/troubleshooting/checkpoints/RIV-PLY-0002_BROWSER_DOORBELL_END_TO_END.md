<!-- Version: 0.10.0 -->
# RIV-PLY-0002 - Browser and doorbell end-to-end boundary

Owner: Riverview browser runtime and bounded doorbell adapter.

## SYMPTOM

Browser preflight fails, the owned browser is absent, CDP is unavailable, the
session is unauthenticated, the exact target is missing or duplicated, the
fixed action cannot be submitted, or the browser reports success without a
downstream mailbox observation.

## LIKELY BOUNDARY

Riverview-owned browser profile/configuration, localhost CDP, exact target
resolution, fixed doorbell action, or the downstream ChatGPT Comms connection.

## SAFE DIAGNOSTIC

From `A:\Riverview\repo`:

```powershell
node tools/riverview_browser_runtime.cjs --preflight
node tools/riverview_doorbell_bridge.cjs --preflight
```

These commands return metadata only. The first proves browser/CDP/profile
availability; the second additionally proves authenticated session, exact
target, and fixed-action readiness.

## EXPECTED HEALTHY RESULT

Both reports contain `ready=true`, with one configured exact target and the
Riverview-owned profile under `A:\Riverview\runtime\browser\profile`.

## KNOWN FAILURE RESULT

- `RIV-PLY-0003`: CDP/runtime unavailable.
- `RIV-PLY-0004`: authentication/session unavailable.
- `RIV-PLY-0005`: target absent; `RIV-PLY-0006`: duplicate target.
- `RIV-PLY-0007`: composer unavailable; `RIV-PLY-0008`: fixed action unavailable.
- `RIV-PLY-0009`: bounded invocation timeout/failure.
- `RIV-PLY-0010`/`0011`: missing or invalid local configuration.
- `RIV-PLY-0012`/`0013`: browser lifecycle or executable failure.
- A first ring attempt exposed a tranche-local `UUID is not defined` defect
  before browser submission; the bounded bridge was repaired and published.
  The exact configured ChatGPT project route was then accepted by the target
  matcher without enabling fallback discovery.
- The final authorized attempt returned durable `succeeded` evidence, but a
  bounded 51-second PostgreSQL observation still showed the request as
  unacknowledged, unclaimed, and pending with no response. This correctly
  separates RV-008.3 browser-wake acceptance from later RV-008.4 response
  return and RV-004.5 full-loop mailbox behavior.

## REPAIR

Use the Riverview-owned runtime start/recovery command and configuration
bootstrap. If authentication is missing, require the one-time Steward login
in the Riverview-owned browser profile. If target count is zero or greater
than one, repair only the exact target configuration; never enumerate chats or
fall back to fuzzy/latest selection.

## VERIFY

Rerun both preflights. For a live attempt, reconcile the returned attempt,
request, and correlation identities with PostgreSQL mailbox/River evidence and
then verify that the designated conversation used Riverview Comms.

For later response-return or full-loop work, verify the same request's
acknowledgement, claim, response, completion, and River-event lineage through
PostgreSQL. Do not pull those later criteria backward into RV-008.3 or add
write authority to the read-only Comms surface.

## DO NOT

Do not scrape responses, inspect unrelated conversations, use arbitrary
selectors/navigation/JavaScript, or treat browser submission/exit code as
end-to-end success.

## EVIDENCE

Store metadata-only reports under `A:\Riverview\runtime\diagnostics\`. Trace
one request using `request_id` and `correlation_id`; do not include page text,
DOM, cookies, or credentials.
