<!-- Version: 0.1.0 | Applicable source: Comms5 contract 5.0, Riverview main 7f0b6d3 -->
# RIV-COMMS5-0021 — Camrui Comms5 runtime alignment

## Symptom and verified boundary

The Steward reports five Comms5 discovery tools callable and sixteen contract
operations returning `NOT_IMPLEMENTED`. The public endpoint currently returns
HTTP 401 to an unauthenticated MCP initialization request, as expected. An
Ionoge loopback health probe returned HTTP 200. These checks verify ingress and
authentication behavior only; they do not identify the authenticated backend
release or prove tool execution.

The fetched `ppow1/Riverview` source at `7f0b6d3` contains all 21 registered MCP
tools and concrete Comms5 service methods. Its handlers use the legacy
`riverview` package, Windows DPAPI-backed database credentials, and the legacy
Comms5/PostgreSQL schema. The inspected Camrui engineering checkout
`/home/admin1/projects/Riverview-New-Core` uses `riverview_core`, a different
authority and assignment schema, and contains no Comms5 adapter or seed/specification
registry. Therefore the legacy implementation cannot be assumed to be the
currently deployed Camrui implementation or copied into that runtime without
schema and authority reconciliation.

## Operation-to-backend migration matrix

| Operation | Historical Riverview implementation | Camrui `Riverview-New-Core` integration state |
|---|---|---|
| `comms5_contract_info` | `Comms5Service.contract_info` | No adapter in checkout; live callable per Steward report |
| `comms5_help` | `Comms5Service.help` | No adapter in checkout; live callable per Steward report |
| `comms5_capabilities` | `Comms5Service.capabilities` | No adapter in checkout; live callable per Steward report |
| `comms5_describe_operation` | `Comms5Service.describe_operation` | No adapter in checkout; live callable per Steward report |
| `comms5_examples` | `Comms5Service.examples` | No adapter in checkout; live callable per Steward report |
| `comms5_store_specification` | `comms5_specifications`, `EventStore` | No equivalent proposal/specification registry or adapter found |
| `comms5_submit_steward_seed` | `StewardSeedStore`, `steward_seed_drafts` | No seed draft store or adapter found |
| `comms5_confirm_and_promote_seed` | `StewardSeedStore.confirm_and_promote`, durable Steward grant and objective creation | Grace objective and exact-grant assignment intake exist; seed promotion bridge absent |
| `comms5_seed_status` | `steward_seed_drafts` bounded projection | No seed records or adapter found |
| `comms5_seed_lineage` | Seed lifecycle, objective, authority, intent, work-order, River-event and CME stores | No seed lineage projection; related objective and assignment state exists in different tables |
| `comms5_objective_status` | `ObjectiveStore`, grants, intents, work orders, CME | Objective pipeline/dashboard projections exist; Comms5 adapter absent |
| `comms5_cme_status` | `CMEStatusStore` | CME monitor and dashboard projection exist; Comms5 adapter absent |
| `comms5_recent_steward_submissions` | `steward_seed_drafts` | No bounded submission projection or adapter found |
| `comms5_transport_probe` | Transport diagnostic recorder plus bounded PostgreSQL `SELECT 1` | No Comms5 transport probe or correlation projection found |
| `comms5_form_and_queue_work` | `StewardAuthorityStore` plus `EngineeringIntentStore.form_and_enqueue` | Exact-grant assignment intake/CME pipeline exists; Comms5 bridge absent |
| `comms5_revalidate_and_queue_work` | `StaleBaseRecoveryStore` | No Comms5 stale-base recovery adapter found; runtime equivalence not verified |
| `comms5_cancel_draft` | `StewardSeedStore.cancel_draft` | No seed lifecycle adapter found |
| `comms5_supersede_seed` | `StewardSeedStore.supersede_seed` | No seed lifecycle adapter found |
| `comms5_resource_policy_status` | `ResourcePolicyStore`, seat claims, `ResourceRegistry`, decisions | No resource-policy service or Comms5 adapter found |
| `comms5_set_resource_policy` | Steward-attested `ResourcePolicyStore.set` | No resource-policy service or Comms5 adapter found |
| `comms5_set_resource_policy_lock` | Steward-attested resource-policy lock | No resource-policy service or Comms5 adapter found |

“No adapter found” describes the inspected source checkout, not a claim about
uninspected files or the running host. The reported live `NOT_IMPLEMENTED`
results still require correlation to the exact deployed package and process.

## Confirmed source defects corrected in the candidate

The historical `cancel_draft` and `supersede_seed` service methods previously
trusted the body field `authenticated_principal` plus a confirmation boolean.
Unlike promotion, formation, and resource-policy writes, they did not require
the server-injected `X-Riverview-Comms5` Steward attestation. Their MCP wrappers
also had no `Context` parameter. A caller could therefore forge the body
principal and reach the mutation path. The candidate now requires transport
attestation and records `steward` as the actor only after that attestation is
verified. Input field names and write semantics remain unchanged.

The candidate also accepts a valid linked Git worktree `.git` pointer in the
Engineering intent repository-root validation. A malformed or dangling pointer
is rejected. This fixes a source-level formation failure for the isolated
worktree layout used by the Engineering execution path.

## Required live diagnosis and recovery

Use the authenticated Camrui operator path to capture, without credential
values:

1. The Comms5 service unit, executable, working directory, environment-file
   path, and active release pointer.
2. The package source commit and imported module path reported by that process.
3. Authenticated `initialize` and `tools/list` output and a comparison against
   the 21-name source registry.
4. Migration ledger versions and table/catalog presence for each required
   operation. Never apply legacy migrations to the current core database as a
   diagnostic.
5. Sanitized per-operation result/error records correlated by MCP request ID.

If the running process is an old/stub package, stage a compatible adapter
against the current `riverview_core` stores and exact grants, test it against a
disposable PostgreSQL database, then deploy using the managed runtime
supervisor and its preserved predecessor. Do not point Camrui at the historical
Windows package or recreate the historical schema.

## Verification and escalation

- Local source: Comms5 discovery/contract, OAuth/HTTP transport, authority,
  resource-policy, seed, transport-probe and formation tests.
- Public unauthenticated request: HTTP 401 is expected and is not a functional
  operation test.
- Live acceptance: each read must return authoritative Camrui state; each write
  must demonstrate the existing authorization decision, durable transition,
  idempotent replay and resulting event/assignment state in an isolated or
  explicitly approved production objective.
- Escalate only if the authenticated Camrui connection or exact runtime
  configuration is unavailable, or if its schema/authority contract cannot be
  reconciled without a separately authorized migration.

Do not report a tool as implemented from registry presence, schema discovery,
or a successful transport health check alone.
