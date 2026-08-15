<!-- Version: 0.3.0 -->
# RIV-PLY-0001 - Riverview-owned doorbell acceptance

Component owner: Riverview `tools/riverview_doorbell_bridge.cjs`,
`tools/riverview_browser_runtime.cjs`, and
`riverview.doorbell.browser_bridge`. RV-008.3 bounded wake acceptance is
complete; later response-return and full-loop behavior remain separate
waypoints.

Inputs: a typed `DoorbellRequest`. Riverview accepts only the literal target
selector `riverview-designated` and mailbox resource `riverview://mailbox`.
The local configuration contains one conversation ID, browser executable,
localhost CDP port, and adapter version.

Outputs: a `DoorbellResult` retaining request/correlation identity, bounded
state, timestamp, safe evidence reference, and stable failure class. The
bridge returns no page content, conversation text, selectors, URLs, cookies,
or assistant output.

Authoritative state location: PostgreSQL mailbox/request state and River
events. Local bridge evidence is metadata-only diagnostic evidence.

Fixed operation: the Riverview-owned bridge submits the constant
`Riverview doorbell v1: inspect the Riverview MCP mailbox.` to the exact
configured conversation. It does not read or interpret a response.

Failure classes: invalid bridge input (`RIV-PLY-0002`), CDP/runtime unavailable
(`RIV-PLY-0003`), authentication/session failure (`RIV-PLY-0004`), target absent
(`RIV-PLY-0005`), duplicate target (`RIV-PLY-0006`), composer unavailable
(`RIV-PLY-0007`), fixed action unavailable (`RIV-PLY-0008`), timeout
(`RIV-PLY-0009`), missing configuration (`RIV-PLY-0010`), invalid configuration
(`RIV-PLY-0011`), and lifecycle failure (`RIV-PLY-0012`/`0013`).

Distinguishing probes:

```powershell
node tools/riverview_browser_runtime.cjs --preflight
node tools/riverview_doorbell_bridge.cjs --preflight
```

Both are metadata-only and never ring the doorbell.

Smallest safe repair: create or update the Riverview-owned configuration with
`python -m riverview.doorbell.bootstrap`, start the Riverview-owned browser
runtime, and rerun preflight. Do not add credentials, bypass authentication,
enumerate chats, or expose browser primitives.

Recovery verification: rerun configuration, lifecycle, bridge, and doorbell
tests; confirm preflight resolves exactly one configured target; confirm
request/correlation identity is unchanged.

Provenance: Estate browser mechanics were inspected as reference only. Estate
source, data, configuration, profile, and worker state are not runtime
dependencies.

Applicability: RV-008.3 bounded implementation and accepted live wake evidence.

Escalation boundary: missing authenticated profile/session or any request for
arbitrary browser interaction requires the Steward; RV-004.5 remains blocked.
