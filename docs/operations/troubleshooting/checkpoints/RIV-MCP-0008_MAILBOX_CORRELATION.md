<!-- Version: 0.1.0 -->
# RIV-MCP-0008 - Mailbox lineage or lifecycle cannot be reconciled

Component owner: `riverview.mailbox.store` and `riverview.river`.

Inputs: idempotent typed request, correlation/causation identities, acknowledgement, bounded claim lease, response identity, and expiry.

Outputs: one PostgreSQL request lineage, at most one response, and River events for accepted, acknowledged, claimed, completed, or expired lifecycle transitions.

Authoritative state location: PostgreSQL `mailbox_messages`, `mailbox_responses`, and `river_events`.

Failure classes: duplicate delivery, duplicate response, claim conflict, expired request, missing response identity, and correlation loss.

Distinguishing probes: run `python -m riverview.mailbox.live_acceptance`; query rows by the generated idempotency key and correlation ID; compare River event aggregate identity and correlation.

Smallest safe repair: reconcile by idempotency key and return the existing request/response. Do not insert a second work item or create a parallel event system.

Recovery verification: duplicate delivery returns the original request and correlation; duplicate response returns the original response; lifecycle River events retain one correlation.

Provenance: RV-008.2, migration 0011, `src/riverview/mailbox/store.py`, version 0.10.0.

Applicability: RV-008.2 implementation; not full-loop execution.

Escalation boundary: unknown or contradictory PostgreSQL state, protected payload access, or a request to dispatch work.
