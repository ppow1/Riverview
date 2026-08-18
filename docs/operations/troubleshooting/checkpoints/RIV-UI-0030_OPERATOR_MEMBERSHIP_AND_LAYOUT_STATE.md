# RIV-UI-0030 — Operator membership governance and layout state

Use this checkpoint when a neutral conversation inherits a resident, an
initial selector remains after assignment, Add Participant creates an empty
unrelated room, room membership cannot be extended/removed, or room
administration is not durable. Also use it when the hamburger changes primary
view or asynchronous reconciliation overwrites explicit navigation.

The canonical state machine is unassigned conversation, single-resident
conversation, and multi-participant room. Initial assignment updates the same
durable conversation ID. Add Participant derives/extends the current durable
discussion with an explicit bounded context policy; + Room creates an
independent room. Membership and room-scoped administrator history belong in
the durable Operator room projection, never in resident continuity or global
authority.

Primary view and rail/context layout are separate client state dimensions.
Hamburger changes layout only, while primary navigation changes the primary
workspace only. Do not repair stale reconciliation by adding another browser
handler or by allowing SSE to overwrite explicit user navigation.

Recovery verification covers neutral assignment without an ID change,
repeated room expansion, removal/re-add with preserved history, co-admin and
last-admin guards, room membership events in Activity, and layout toggles from
every primary view.
