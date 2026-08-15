# Riverview Comms interaction matrix

Version: 0.19.0
Status: canonical schema-freeze audit

This matrix classifies the foreseeable ChatGPT-facing interaction for every
roadmap waypoint. The stable contract is semantic, not waypoint-specific:

| Family | Stable interaction | Authority |
|---|---|---|
| READ / STATUS | bounded set projections for roadmap, objectives, work, capacity, bindings, diagnostics, and evidence | read-only |
| REASONING MAILBOX | inspect, acknowledge, claim, return bounded advisory response | named mailbox operations |
| STEWARD INTENT | submit a bounded server-classified intent draft | draft only |
| STEWARD DECISION | approve, reject, choose a published option, acknowledge, or confirm an existing target | existing target only |
| TRACE / CORRELATION | retrieve one bounded lineage by correlation or identity | read-only |
| DIAGNOSTIC / RECOVERY | inspect checkpoint/Cookbook guidance and recovery state | bounded recovery |
| BINDING / ROLLOVER | inspect candidate/active/retired binding and verification state | explicit Steward activation |
| REFERENCE / ARTIFACT | submit or retrieve a bounded reference to an existing artifact | metadata/reference only |
| SEARCH / RETRIEVAL | query approved indexed metadata or excerpts when that index is accepted | classification-filtered |

Unknown interaction kinds fail closed. No family is an arbitrary SQL, filesystem,
shell, browser, work-creation, roadmap-mutation, secret, or Undercurrent channel.

## Complete waypoint classification

The IDs below are the complete current master-roadmap set. A family entry applies to
each listed waypoint; “internal” means no ChatGPT interaction is required for the
implementation path, though bounded status/trace remains available.

| Waypoints | Classification | Can use the stable contract without a new waypoint-specific MCP tool? |
|---|---|---|
| RV-001, RV-002, RV-003, RV-004.1, RV-004.2, RV-005.2, RV-006.1, RV-006.2, RV-006.4, RV-006.6, RV-007.1, RV-007.2, RV-007.3, RV-007.4, RV-007.6, RV-015.1, RV-015.4, RV-015.6, RV-018.1, RV-018.4 | internal + READ / STATUS + TRACE | yes |
| RV-004, RV-004.3, RV-004.4, RV-005, RV-005.1, RV-005.3, RV-005.4, RV-005.5, RV-005.6, RV-006, RV-006.3, RV-006.5, RV-007, RV-008, RV-008.1, RV-008.2, RV-008.6 | READ / STATUS + TRACE / CORRELATION + DIAGNOSTIC / RECOVERY | yes |
| RV-004.5, RV-008.3, RV-008.4 | REASONING MAILBOX + TRACE / CORRELATION | yes |
| RV-008.5, RV-012.1, RV-012.3, RV-012.5, RV-012.6 | STEWARD INTENT + STEWARD DECISION + READ / STATUS | yes |
| RV-009, RV-009.1, RV-009.2, RV-009.3, RV-009.4, RV-009.5 | SEARCH / RETRIEVAL + REFERENCE / ARTIFACT + READ / STATUS | yes, once the bounded index exists |
| RV-010, RV-010.1, RV-010.2, RV-010.3, RV-010.4, RV-010.5, RV-010.6 | REFERENCE / ARTIFACT + READ / STATUS + STEWARD DECISION where declared | yes |
| RV-011, RV-011.1, RV-011.2, RV-011.3, RV-011.4, RV-011.5 | READ / STATUS + STEWARD DECISION + DIAGNOSTIC / RECOVERY | yes |
| RV-012, RV-012.2, RV-012.4 | STEWARD INTENT + READ / STATUS + TRACE / CORRELATION | yes |
| RV-013, RV-013.1, RV-013.2, RV-013.3, RV-013.4, RV-013.5, RV-013.6 | READ / STATUS + STEWARD DECISION; protected/Undercurrent paths remain outside ordinary Comms payloads | yes |
| RV-014, RV-014.1, RV-014.2, RV-014.3, RV-014.5 | READ / STATUS + REASONING MAILBOX + STEWARD DECISION | yes |
| RV-007.5, RV-014.4 | protected/Undercurrent + READ / STATUS; no ordinary ChatGPT payload | yes |
| RV-015, RV-015.2, RV-015.3, RV-015.5 | READ / STATUS + STEWARD DECISION + DIAGNOSTIC / RECOVERY | yes |
| RV-016, RV-016.1, RV-016.2, RV-016.3, RV-016.4, RV-016.5 | READ / STATUS + REFERENCE / ARTIFACT + STEWARD DECISION | yes |
| RV-017, RV-017.1, RV-017.2, RV-017.3, RV-017.4, RV-017.5, RV-017.6 | READ / STATUS + REFERENCE / ARTIFACT + STEWARD DECISION + DIAGNOSTIC / RECOVERY | yes |
| RV-018, RV-018.2, RV-018.3, RV-018.5, RV-018.6 | READ / STATUS + TRACE / CORRELATION + STEWARD DECISION + DIAGNOSTIC / RECOVERY | yes |

## Binding and continuity

Authoritative binding state is stored in PostgreSQL `comms_bindings`. The active
`designated_reasoning` row is verified before a bounded doorbell submission; local
configuration is a consistency check, not an alternate authority. Candidate
conversation/app rollover is candidate -> initialized -> verified -> Steward
activation -> previous binding retired. The continuity package references the
repository, mandatory documents, contract version, consumer, role, and authority
boundaries; it does not copy conversation history or carry credentials.

Detailed boundary and recovery procedures are in
[`RIV-COMMS-0004_BINDING_ROLLOVER.md`](troubleshooting/checkpoints/RIV-COMMS-0004_BINDING_ROLLOVER.md).
