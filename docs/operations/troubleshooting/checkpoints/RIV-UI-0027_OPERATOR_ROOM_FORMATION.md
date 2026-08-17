<!-- Version: 0.1.0 -->
# RIV-UI-0027 — Operator room formation and bounded context transfer

Use this checkpoint when room creation is invisible, a resident selector creates
an unrelated conversation, a room displays General Operator as a phantom
participant, or a room turn is not persisted.

Verify the modal boundary, admitted participant IDs, room projection, room chat
endpoint, provider/session initialization, and durable message append. Derived
rooms must record source conversation lineage and an explicit bounded context
window. The selected inherited messages must be visible in the hydrated room
transcript and must be distinguished from post-formation turns. Never copy
rendered HTML or resident continuity into an unrelated room.

Recovery verification covers visible `showModal()` room creation, canonical
activation, room participant presentation, a persisted room turn after refresh,
and an explicit Add Participant branch with bounded inherited context.
