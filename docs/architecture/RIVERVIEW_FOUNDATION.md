<!-- Version: 0.2.0 -->
# Riverview Foundation Architecture

Status: Designed; standalone repository/runtime root pending Phase 0 reconciliation

## Mission

Preserve the Estate's mission, residents, offices, continuity, engineering capacity, and human-centered character while replacing accumulated internal complexity with a small, explicit, self-diagnosing mechanism.

## Governing model

- **Project Riverview** is the endeavor.
- **The Estate** is the current/legacy operational system and capability source during migration.
- **Riverview** is a separate successor/replacement system; it is not a subsystem of The Estate.
- **The River** is the core event-driven architecture.
- **Riverview Kernel v0.1** is the first implementation.
- **The Undercurrent** is the restricted high-trust domain.

## Kernel boundaries

The kernel initially owns only:

1. Durable event recording.
2. Objective and workflow state.
3. Work assignment, ownership, attempts, and leases.
4. Diagnostic checkpoints and evidence.
5. Cookbook linkage and staleness.
6. Capability/provider registration.
7. Grace and Continuous Momentum Engine progression contracts.
8. MCP mailbox correlation.

Interfaces, residents, visual environments, Open WebUI, SillyTavern, Stream Deck, command-chair devices, voice, Bluetooth, remote access, and Quest/3D presentation remain adapters or consumers—not kernel responsibilities. Temporary reuse of Estate capabilities is a bounded migration dependency and does not establish repository or architectural subordination.

## Operational sentence

Playwright is the doorbell. MCP is the data bus. PostgreSQL is durable River memory. Grace controls progression. The Steward supplies ideation, bounded authority, selected checkpoints, exceptions, and final acceptance.

## Data boundary

Runtime data, private material, transcripts, screenshots, generated media, credentials, and large artifacts remain outside source code. PostgreSQL records identity, classification, ownership, hashes, lifecycle, and storage references. The Undercurrent uses explicit access and promotion boundaries.

## Anti-complexity rule

New mechanisms require a distinct responsibility that cannot be absorbed by an existing kernel component or adapter. Compatibility with the Estate is implemented through bounded adapters rather than copying entire subsystems.
