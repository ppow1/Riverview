<!-- Version: 0.1.0 -->
# Riverview Foundation Architecture

Status: Designed

## Mission

Preserve the Estate's mission, residents, offices, continuity, engineering capacity, and human-centered character while replacing accumulated internal complexity with a small, explicit, self-diagnosing mechanism.

## Governing model

- **Project Riverview** is the endeavor.
- **The Estate at Riverview** is the final environment.
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

Interfaces, residents, visual environments, Open WebUI, SillyTavern, Stream Deck, command-chair devices, voice, Bluetooth, remote access, and Quest/3D presentation remain adapters or consumers—not kernel responsibilities.

## Operational sentence

Playwright is the doorbell. MCP is the data bus. PostgreSQL is durable River memory. Grace controls progression. The Steward supplies ideation, bounded authority, selected checkpoints, exceptions, and final acceptance.

## Data boundary

Runtime data, private material, transcripts, screenshots, generated media, credentials, and large artifacts remain outside source code. PostgreSQL records identity, classification, ownership, hashes, lifecycle, and storage references. The Undercurrent uses explicit access and promotion boundaries.

## Anti-complexity rule

New mechanisms require a distinct responsibility that cannot be absorbed by an existing kernel component or adapter. Compatibility with the Estate is implemented through bounded adapters rather than copying entire subsystems.
