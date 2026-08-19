# RIV-RES-0002 — Resident room/session boundary

Resident room turns require an authoritative in-process room, admitted resident
IDs, bounded classification, automatically initialized resident sessions, an
eligible provider, and one preserved correlation ID. Diagnostics contain only
bounded IDs/types and never resident payloads or credentials.

Recovery: validate the room and participant set, select the configured local
provider, initialize sessions through the resident gateway, run one ordered
round, and preserve the room snapshot. A failed provider turn must not transfer
authority or create recursive resident work.

Direct Grace execution-intent boundary: a Grace response or a Steward message
containing words such as “proceed”, “authorize”, or “implement” is only a
candidate and never creates authority. The governed direct-Grace path requires
an authenticated Operator session plus a typed `direct_grace_approval` envelope
containing one complete immutable specification, validated read-only formation
contract, stable idempotency key, approval-operation UUID, and explicit Steward
confirmation. The server supplies the Steward principal from the authenticated
Operator boundary; the client cannot select it. The envelope enters the same
specification → seed → promotion → `steward_authority_grants` path used by
Comms5, so one approval produces one replay-safe objective/authority lineage.

If Activity records `execution_intent_detected=false` after Grace says it is
proceeding, inspect the correlated `grace.conversation.completed` event and
distinguish `execution_intent_candidate` from `governed_execution_intent`.
Missing typed approval is a real Steward checkpoint; malformed contract,
missing specification fields, hash/version conflict, or idempotency conflict
fails closed. Never reconstruct an exact specification from conversation prose
or insert an objective/work order directly.
