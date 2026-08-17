# RIV-UI-0021 — Operator durable conversation projection

Use this checkpoint when Operator conversations or rooms disappear after a
service restart, fail to reconcile, or lose message lineage.

The UI projection is authoritative for conversation identity, display metadata,
room references, and message history only. It must not replace accepted
resident continuity or character canon. Verify migration `0027`, inspect the
`operator_conversations` and `operator_messages` rows, and compare the browser
projection with the durable records. The smallest repair is to apply the
ordered migration and restart the bounded Operator service; never delete
continuity records as conversation cleanup.

Recovery verification: create a conversation and message, restart the service,
reload `/api/conversations`, and verify the same ID, resident identity, and
message order are returned. Room recovery additionally verifies participant
membership and room correlation.
