<!-- Version: 0.1.2 -->
# Project Riverview

> **AI MODEL EXECUTIVE HANDOFF / CODEX:** [2026-10-13 runtime inventory and handoff](docs/handoffs/RIVERVIEW_AI_MODELS_EXECUTIVE_HANDOFF_2026-10-13.md) · [Grace Open Eyes Codex work order](docs/operations/GRACE_OPEN_EYES_CODEX_IMPLEMENTATION.md).

> **CURRENT AI MODEL DEFAULTS / STARTUP:** [CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md](CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md) — read this first before changing models, GPU assignments, or services. Includes **deployed and verified** 32K/8-slot Huihui vision profile, 80B isolation, [Grace Open Eyes reload runbook](docs/operations/GRACE_OPEN_EYES_FAST_LOAD.md), and [model registry](docs/model-evaluations/README.md).


Project Riverview is the purposeful rebuild of the Estate's operational mechanism. The final environment is **The Estate at Riverview**, its core architecture is **The River**, and the first technical implementation is **Riverview Kernel v0.1**.

The River is local-first, event-driven, durable, diagnostics-first, and designed to sustain momentum without making the Steward the routine router.

## Foundation commitments

- PostgreSQL is authoritative operational state.
- JSON is transport, configuration, fixtures, or export—not the workflow database.
- Grace owns workflow progression and capability routing.
- The Continuous Momentum Engine detects and advances eligible work.
- MCP is the reasoning data bus; Playwright is the ChatGPT doorbell.
- Local AI and Codex CLI are bounded execution providers.
- OpenAI API models are excluded from the architecture.
- The Undercurrent is the protected high-trust domain.
- Data is separated from actions and classified at ingestion.
- Every capability is delivered with diagnostics, failure checkpoints, tests, and Cookbook knowledge.

## OCTOMINER2 local-AI control

Current OCTOMINER2 hardware and active workload state is documented in
[`OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md`](docs/operations/octominer/OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md).
The dated OCTO Control feature/API guide also records its historical profile
catalog, authentication, instances, telemetry, monitoring, snapshots, and
Hermes integration:

[`docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`](docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md)

The versioned controller source, deployment notes, and managed-workload tests
are in [`deployment/octo2-control`](deployment/octo2-control/README.md).

Start with `AI_HINTS.md` and `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`.
