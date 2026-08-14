<!-- Version: 0.1.0 -->
# RIV-MCP-0007 - Mailbox payload is outside the bounded contract

Component owner: `riverview.mailbox.store`.

Inputs: typed sender/requester identity, message type, idempotency key, one JSON payload or one safe local reference, classification, and bounded expiry.

Outputs: accepted PostgreSQL metadata or a deterministic rejection before persistence.

Authoritative state location: PostgreSQL `mailbox_messages`; protected/large data remains in classified local storage.

Failure classes: missing payload/reference, oversized payload, oversized reference, unsupported classification, invalid identity, and invalid expiry.

Distinguishing probes: run `pytest -q tests/test_mailbox_contract.py`; inspect only the request count and rejection result, never payload contents.

Smallest safe repair: bound or externalize the payload and retain a safe reference. Never widen the limit or store Undercurrent content in ordinary PostgreSQL/MCP paths.

Recovery verification: invalid input creates no mailbox row; valid bounded input produces one correlated request event.

Provenance: RV-008.2, migration 0011, `src/riverview/mailbox/store.py`, version 0.10.0.

Applicability: RV-008.1/RV-008.2 implementation.

Escalation boundary: protected classification, missing authority to expose a reference, or a request to exceed the payload bound.
