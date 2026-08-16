# Riverview module contract 1.0

The frozen core owns River/PostgreSQL authority, event envelopes, diagnostics,
Grace/CME and objective stages, Relay/work-order lifecycle, provider capability
registry/dispatch, classification/security, notifications, canonical actions,
and the module registry itself. UI surfaces, adapters, providers, resident
presentation, Snapshot export, devices, projects, and Quest presentation are
modules.

Modules declare machine-readable manifests under `config/modules/`. They may
consume/publish declared River events, request named bounded actions, read
projections, register provider capabilities, expose bounded routes, declare
diagnostics, own their storage, and report lifecycle/health/recovery. They do
not mutate arbitrary core tables, import another module's private code, add
shell authority, bypass classification, or become authoritative merely by
being installed.

Core contract `riverview-core-contract-1.0` permits backward-compatible
additions in 1.x. Breaking event/envelope/authority/storage semantics require
core 2.0 and a migration. Deprecations require one release of compatibility,
an explicit replacement, and a migration note. Incompatible modules fail
closed at registry load and do not start. Disabling a module leaves core
healthy; dependent modules report degraded health.

The Operator and loopback Ollama adapter are proof manifests. They declare
events, actions, projections, diagnostics, routes, authority, dependencies,
storage ownership, and recovery without changing kernel responsibilities.
