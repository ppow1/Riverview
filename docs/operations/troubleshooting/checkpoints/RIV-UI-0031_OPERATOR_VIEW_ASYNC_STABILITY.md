# RIV-UI-0031 — Operator view async stability and reconciliation

Use this checkpoint when a primary-view click is delayed, a highlighted tab and
visible workspace disagree, or a late Activity/Architecture/Notifications
response overwrites a newer user-selected view. Also use it when the
conversation rail jumps to the top during event reconciliation, when persisted
room-admin state is not reflected in Manage Room, or when a previously working
Architecture projection reports unavailable.

The required order is: commit the explicit primary-view state, render that
view's shell immediately through the single primary render owner, then perform
bounded asynchronous loading. The owner mounts one `#primary` root with a
`data-primary-view` marker; no child loader or reconciliation callback may
replace that root directly. Each load must carry the requested view and current
view generation and may mutate the workspace only when the generation, primary
view, and mounted marker still match. Discarded mutations should be retained in
a bounded Snapshot ring buffer. SSE is a wake/reconciliation path; it never
changes explicit navigation. Rail scrollTop is user state and must be preserved
across routine list replacement.

Recovery verification covers rapid view changes, delayed stale responses,
Architecture recovery, notification/activity failure states, rail scroll
preservation, and Snapshot agreement with canonical view state.
