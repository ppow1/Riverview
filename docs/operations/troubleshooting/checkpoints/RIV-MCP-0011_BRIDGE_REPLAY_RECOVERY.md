# RIV-MCP-0011 — Bounded bridge replay and recovery

SYMPTOM: A wake or bounded MCP transport attempt fails, is replayed, or reaches
its retry limit without losing request/correlation identity.

LIKELY BOUNDARY: Bridge transport/recovery state, not PostgreSQL mailbox authority.

SAFE DIAGNOSTIC: Inspect `bridge_recovery_attempts` by `recovery_id` and
`correlation_id`; compare `attempt_count`, `state`, `failure_class`, and the
associated `river_events` rows. Use the bounded `BridgeRecoveryStore` operations.

EXPECTED HEALTHY RESULT: One recovery identity exists for one request/correlation/
operation. A retry is `retryable`, a successful replay is `recovered`, and an
exhausted retry budget creates exactly one `RIV-0086-0001` Steward escalation.

KNOWN FAILURE: Induced transport failure is recorded without a second request or
unbounded retry. A second failure at the configured limit becomes `escalated`.

REPAIR: Retry only through the same recovery identity while it is `retryable`.
Record bounded success after the real boundary recovers. Escalated recovery requires
the Steward boundary; it must not be silently resumed.

VERIFY: Query the recovery row and River events by the same correlation. Require
preserved request/correlation IDs, one escalation at most, and no duplicate logical
recovery event on replay.

DO NOT: create a replacement request to mask a recovery failure, widen browser
authority, scrape ChatGPT responses, or treat a local retry as successful boundary
acceptance.

EVIDENCE: PostgreSQL `bridge_recovery_attempts`, `steward_escalations`, and
`river_events`; checkpoint `RIV-0086-0001`; migration `0018`.
