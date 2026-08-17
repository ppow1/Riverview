# RIV-UI-0022 — Operator event reconciliation and reconnect

Use this checkpoint when the Operator does not reflect River activity until a
new user turn or full refresh, or when reconnecting duplicates history.

The browser event stream is a wake/update path only. PostgreSQL/River and the
Operator projection remain authoritative. Verify the authenticated bounded
`/api/events?after=<sequence>` stream, resume from the last event ID, and then
reconcile `/api/conversations` by stable IDs. The smallest repair is to fix
cursor handling or reconnect backoff; never make browser state authoritative.

Recovery verification: append a bounded event, observe one browser update,
disconnect/reconnect, and confirm the same projection is recovered without a
duplicate message.
