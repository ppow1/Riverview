<!-- Version: 0.1.0 -->
# RIV-UI-0025 — Operator global rail actions and durable search

Use this checkpoint when conversation creation actions behave differently by
route or when search only filters a client-loaded sidebar subset.

Safe probes are live clicks from each primary route, inspection of the
authoritative conversation projection, and a bounded search query against the
PostgreSQL message index. Search must return identifiers, bounded snippets,
state, and navigation targets without loading all message bodies into the
browser. Resident-selector changes must be explicit and must not silently
create an unrelated conversation.

Recovery verification covers New/Room actions from every route, confirmed room
creation, explicit resident-to-room conversion, archived and active search,
direct history hydration, and matching-message navigation.
