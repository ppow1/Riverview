# RIV-UI-0032 — Operator room membership projection reconciliation

Use this checkpoint when a durable room transcript or title exists but the
current participant projection is empty, or the room header, Manage Room,
gateway roster, and execution target disagree.

Diagnostic order:

1. Identify the exact conversation ID and room ID.
2. Inspect `operator_room_memberships` active rows and administrator rows.
3. Resolve active resident profiles and check duplicate active membership.
4. Compare the derived resident-gateway roster with durable active membership.
5. Inspect River membership/turn lineage and the room-turn correlation.
6. Reconcile runtime gateway state from durable membership only.

A title, historical River event, transcript speaker, or browser state is not a
current membership authority. If durable membership is empty or cannot be
reconciled with confidence, expose `membership_projection_inconsistent` and
block provider execution. Do not fabricate membership from a title or erase
history.

Healthy result: one canonical active participant set feeds the room header,
Manage Room, gateway, Snapshot, and room-turn gate. A provider failure records
the bounded participant outcome and correlation rather than collapsing all
cases to `ValueError` or a generic room failure.

Evidence: room/conversation IDs, active membership IDs/states, profile IDs,
gateway IDs, bounded failure class, correlation ID, and restart verification.
Protected provider payloads and credentials are excluded.
