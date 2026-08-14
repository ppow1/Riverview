<!-- Version: 0.1.0 -->
# Riverview Persistent Execution Plan

Status: Active

This file is the persistent scope-control reference for the Riverview build.

## Phase 0 — Foundation

- Repository structure and source provenance
- PostgreSQL authority decision and initial migration
- Diagnostic event contract
- Troubleshooting Cookbook structure
- Tests for the diagnostic contract
- Local audit and synchronization tools

Exit: foundation tests pass locally; Cookbook covers every implemented failure checkpoint; exact commit is published and verified.

## Phase 1 — The River

- Append-only event ledger
- Transactional projections
- Objectives, workflows, stages, dependencies, attempts, and leases
- Idempotency and correlation
- Discovery and health surfaces
- Induced-failure acceptance

## Phase 2 — Momentum and routing

- Grace progression loop
- Continuous Momentum Engine
- Capability-aware worker registry
- Parallel lanes and path ownership
- Stalled-work recovery
- Execution envelopes that avoid routine approval drip

## Phase 3 — Execution adapters

- Deterministic local commands
- RTX 4090 local-AI adapter
- P100 local-AI adapter
- Codex CLI adapter
- Evidence capture and result reconciliation

## Phase 4 — Reasoning bridge

- MCP mailbox lifecycle
- Playwright ChatGPT wake worker
- Correlated structured responses
- `submit_seed_to_grace` interactive Steward path
- No OpenAI API model path

## Phase 5 — Operator environment

- Open WebUI and SillyTavern adapters
- Notification adapter, initially compatible with the Estate
- Stream Deck and command-chair input adapters
- Dictation, screenshots, voice, remote, and later Quest/3D surfaces

## Scope controls

- Revisit this plan before every material addition.
- Park useful non-current ideas rather than implementing them.
- Prefer working vertical slices over broad scaffolding.
- Do not mark later phases complete from documents or mocks.
- Every phase preserves diagnostics, rollback provenance, data separation, and Undercurrent boundaries.
