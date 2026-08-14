<!-- Version: 0.1.0 -->
# RIV-GRC-0001 - Grace authority contract unavailable or exceeded

Component owner: `riverview.grace.authority`.

Trigger: Grace evaluates a coordination capability and the durable identity/rule is missing, unknown, out of scope, or prohibited.

Failure classes:
- Grace identity missing or disabled.
- Explicit authority rule missing.
- Requested scope exceeds the allowed scope.
- A prohibited capability is requested.
- Conversation text is being treated as implicit authority.

Evidence captured:
- Grace identity and authority version.
- Requested capability and scope.
- Allow/deny/escalate decision.
- Reason and evidence references.
- Optional correlation ID.

Safe distinguishing probes:
1. Run `python -m riverview.grace.acceptance`.
2. Inspect the bounded Grace authority tables through approved diagnostics.
3. Confirm the current roadmap checkpoint and Steward authorization.

Smallest safe repair:
- Restore the missing durable Grace identity/rule from the accepted migration.
- Do not widen authority to make a failing request pass.
- Unknown or broader-than-declared requests escalate instead of defaulting to allow.

Recovery verification:
- Contract tests pass.
- Live PostgreSQL-backed acceptance passes.
- Arbitrary SQL/shell, Steward-checkpoint bypass, Undercurrent access, mission/authority changes, and conversation-derived authority are rejected.

Escalation boundary:
- Any requested widening of Grace authority.
- Any mission, authority-model, or protected-boundary change.
- Any ambiguity about Steward intent.

Applicable revision: RV-005.1 / Grace authority v0.1.0.

Validation state: first-pass implementation evidence.