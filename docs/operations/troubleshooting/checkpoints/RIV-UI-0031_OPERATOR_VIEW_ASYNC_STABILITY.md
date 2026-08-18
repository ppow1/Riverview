# RIV-UI-0031 — Operator view async stability and reconciliation

Use this checkpoint when a primary-view click is delayed, a highlighted tab and
visible workspace disagree, or a late Activity/Architecture/Notifications
response overwrites a newer user-selected view. Also use it when the
conversation rail jumps to the top during event reconciliation, when persisted
room-admin state is not reflected in Manage Room, or when a previously working
Architecture projection reports unavailable.

The required order is: commit the explicit primary-view state, render that
view's shell immediately, then perform bounded asynchronous loading. Each load
must carry the current view generation and may mutate the workspace only when
the generation and primary view still match. SSE is a wake/reconciliation path;
it never changes explicit navigation. Rail scrollTop is user state and must be
preserved across routine list replacement.

Recovery verification covers rapid view changes, delayed stale responses,
Architecture recovery, notification/activity failure states, rail scroll
preservation, and Snapshot agreement with canonical view state.
