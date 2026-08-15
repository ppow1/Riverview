<!-- Version: 0.5.0 -->
# Riverview Troubleshooting Cookbook

Status: Designed; initial kernel entries pending implementation evidence.

The Cookbook is a living operational knowledge system connected to implementation revisions, diagnostic events, induced-failure tests, and recovery verification.

## Required checkpoint knowledge

Every checkpoint records:

- Stable checkpoint ID
- Component and seam ownership
- Triggering operation
- Known failure classes
- Evidence captured automatically
- Safe distinguishing probes
- Smallest permitted repair
- Recovery verification
- Escalation boundary
- Applicable implementation revisions
- Validation and staleness state

## Initial checkpoint namespace

- `RIV-DB-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â database, migration, transaction, and projection
- `RIV-DIA-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â diagnostic persistence and emergency evidence spooling
- `RIV-BLD-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â build, packaging, and dependency-environment failures
- `RIV-EVT-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â event acceptance and delivery
- `RIV-WRK-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â worker assignment, attempts, ownership, and leases
- `RIV-RUN-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â restricted local process execution and enforcement
- `RIV-RDM-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â master-roadmap structure, dependencies, revisions, and database acceptance
- `RIV-CME-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â momentum detection and recovery
- `RIV-MCP-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â mailbox, correlation, claims, and responses
- `RIV-PLY-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Playwright doorbell and conversation state
- `RIV-LOC-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â local execution adapters
- `RIV-SEC-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â classification and Undercurrent boundaries
- `RIV-UI-*` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â read-only Steward status and operator surfaces

## Acceptance rule

No capability is operationally complete until a new AI conversation can identify the checkpoint, distinguish modeled failures, perform the smallest safe repair, and verify recovery from repository guidance and captured evidence.

- `RIV-WRK-0005` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â invalid polling recovery configuration
- `RIV-WRK-0006` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â persistent worker runtime failure
- `RIV-WRK-0007` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â PostgreSQL listener startup failure
- `RIV-WRK-0008` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â bounded worker stop failure
- `RIV-WRK-0009` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â notification-loop invariant failure

- `RIV-UI-0001` through `RIV-UI-0006` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â status routing, projection, bind, acceptance, environment, and exit failures

- `RIV-RDM-0001` through `RIV-RDM-0006` ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â roadmap source and persistence failures

- `RIV-BLD-0010` - Windows PowerShell 5.1 UTF-8 no-BOM encoding incompatibility

- `RIV-MCP-0001` through `RIV-MCP-0006` - read-only MCP projection, authority boundary, database read, Cookbook, bounded limits, and fresh-conversation acceptance failures

- `RIV-COMMS-0001` - Riverview Comms connection boundary
- `RIV-COMMS-0002` - Riverview Comms service runtime
- `RIV-COMMS-0003` - HTTPS ingress, bearer authentication, and ChatGPT registration
- `RIV-PLY-0001` - bounded doorbell contract
- `RIV-PLY-0002` - browser and doorbell end-to-end boundary
- `RIV-MCP-0009` - full-loop mailbox and bounded reasoning response
- `RIV-MCP-0007`/`RIV-MCP-0008` - mailbox payload and correlation lifecycle
- `RIV-RDM-0007` - RV-008.3 promotion evidence and authoritative-state reconciliation
