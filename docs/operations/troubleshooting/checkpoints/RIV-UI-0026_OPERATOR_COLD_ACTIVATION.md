<!-- Version: 0.1.0 -->
# RIV-UI-0026 — Operator cold conversation activation

Use this checkpoint when a durable conversation is visible in the rail but a
cold click leaves another conversation or room active in the center/Snapshot.

The required probe follows the complete boundary: rail/search ID, active
conversation state, loading state, durable conversation fetch, message
hydration, resident/room replacement, center rendering, and Snapshot capture.
The selected ID becomes active immediately, while the durable record remains
the source of truth. Search and sidebar navigation must share this activation
function. Reconciliation must not replace a newer user selection with stale
local state.

Recovery verification covers Grace, another resident, and a room after page
refresh and Operator restart without sending a new message.
