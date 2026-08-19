# RIV-UI-0020 — Operator client runtime boundary

Use this checkpoint when the Riverview Operator page renders but application
controls are inert while native browser controls still work, including the
shell-rendered/blank-Conversations signature. Extract the live inline script
and run a JavaScript syntax check first. A 200 response from `/health` and
`/api/conversations` does not prove client initialization succeeded. If syntax
fails, inspect the newest generated handler (especially approval-card bindings)
and repair the generated HTML/JavaScript source, then restart through the
Riverview Runtime Supervisor. Also verify that historical conversations, Grace
conversations, valid pending proposal metadata, and malformed proposal metadata
all render without blanking the primary view. Do not treat API health alone as
browser acceptance.

Safe probes: record served SHA, listener PID, `/health`, authenticated
`/api/conversations?archived=all`, and the served inline-script syntax result.
After repair, rerun syntax validation, authenticated conversation hydration,
Activity, Snapshot, and approval-card rendering. Never remove typed approval
validation or recover by inferring authority from conversation text. Escalate
only if the served script is valid but the API/state boundary or the managed
runtime remains inconsistent.
