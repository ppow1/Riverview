<!-- Version: 0.1.0 -->
# RIV-PLY-0001 - Doorbell boundary is not live-accepted

Component owner: `riverview.doorbell` / future Steward-approved Playwright adapter.

Inputs: a typed `DoorbellRequest` containing request identity, correlation identity, a designated conversation selector, the bounded MCP mailbox resource, and a 1–300 second timeout.

Outputs: a `DoorbellResult` retaining request and correlation identity, a bounded state, timestamp, and safe evidence reference.

Authoritative state location: PostgreSQL mailbox request/response state and River events. The local acceptance harness is test evidence only.

Failure classes: invalid selector/resource, timeout, authentication failure, wrong conversation, browser restart, and live acceptance not authorized.

Distinguishing probes: validate the typed request; run `tests/test_doorbell_contract.py`; verify that the harness emits `prepared` or induced `bounded-timeout` without opening a browser.

Smallest safe repair: repair the typed adapter contract or deterministic harness. Do not add credentials, bypass authentication, scrape conversations, or wake a live browser.

Recovery verification: rerun the deterministic unit tests and confirm request/correlation identity is unchanged. Live browser acceptance requires the Steward checkpoint for RV-008.3.

Provenance: RV-008.3 preparation, `src/riverview/doorbell/contract.py`, version 0.1.0.

Applicability: RV-008.3 preparation only; not live-accepted.

Escalation boundary: any real browser, authentication/session state, designated conversation ambiguity, or request to promote this capability in authoritative roadmap state.
