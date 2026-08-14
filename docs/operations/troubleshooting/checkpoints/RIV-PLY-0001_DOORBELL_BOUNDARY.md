<!-- Version: 0.2.0 -->
# RIV-PLY-0001 - Estate bounded doorbell bridge is not live-accepted

Component owner: Estate `tools/riverview_doorbell_bridge.cjs` and Riverview
`riverview.doorbell.estate_bridge`; RV-008.3 remains Steward/live accepted.

Inputs: a typed `DoorbellRequest`. Riverview accepts only the literal target
selector `estate-riverview-designated` and mailbox resource
`riverview://mailbox`. The Estate bridge receives request/correlation IDs and
bounded timeout only. The local Estate target configuration contains one
conversation ID and remains outside Riverview/GitHub/PostgreSQL.

Outputs: a `DoorbellResult` retaining request/correlation identity, bounded
state, timestamp, safe evidence reference, and stable failure class. The
Estate bridge returns no page content, conversation text, selectors, URLs,
cookies, or assistant output.

Authoritative state location: PostgreSQL mailbox request/response state and River events. The local acceptance harness is test evidence only.

Fixed operation: the Estate-owned bridge submits the constant
`Riverview doorbell v1: inspect the Riverview MCP mailbox.` to the exact
configured conversation. It does not read or interpret a response.

Failure classes: invalid bridge input (`RIV-PLY-0002`), CDP/runtime unavailable
(`RIV-PLY-0003`), authentication/session failure (`RIV-PLY-0004`), target absent
(`RIV-PLY-0005`), duplicate target (`RIV-PLY-0006`), composer unavailable
(`RIV-PLY-0007`), fixed action unavailable (`RIV-PLY-0008`), timeout
(`RIV-PLY-0009`), and live acceptance not authorized.

Distinguishing probes: run `node A:\theestate\tools\riverview_doorbell_bridge.cjs --preflight`; run the Estate bridge contract tests and Riverview doorbell tests. Preflight is metadata-only and never rings the doorbell.

Smallest safe repair: verify the Estate-local target configuration, authenticated
CDP runtime, and fixed bridge operation. Do not call the broad Estate mailbox
worker, add credentials, bypass authentication, enumerate chats, or expose
browser primitives through Riverview.

Recovery verification: rerun Estate and Riverview bridge tests, confirm the
preflight reports the exact target, and confirm request/correlation identity is
unchanged. Live browser acceptance requires the Steward checkpoint for RV-008.3.

Provenance: RV-008.3 preparation and Estate reconnaissance; Estate bridge
version 1.0.0; Riverview adapter version 1.0.0.

Applicability: RV-008.3 bounded implementation; not live-accepted.

Escalation boundary: any real browser, authentication/session state, designated conversation ambiguity, or request to promote this capability in authoritative roadmap state.
