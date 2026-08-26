# Hermes Campaign Engineering Execution Budget

Status: Active bounded Tranche 2 execution policy.

## Policy

Ordinary Riverview relay actions retain their existing short budgets. Substantial
Campaign Runner/Hermes engineering work uses the explicit action type:

```text
campaign.hermes.engineering
```

Migration `0047_campaign_hermes_execution_budget.sql` registers that action with:

- expected duration: 1,200 seconds;
- hard timeout: 1,800 seconds;
- retry-safe: false;
- execution seam: `internal:hermes-campaign-role-adapter`.

The work-order hard timeout is lifecycle authority. Hermes completion never
advances acceptance, and a timeout remains a truthful failed/interrupted result
subject to Campaign Runner recovery.

`RelayStore.claim_fenced` keeps ordinary leases at 30 seconds. For a substantial
action whose hard timeout exceeds 600 seconds, it derives a lease of
`hard_timeout_seconds + 60` seconds. The additional 60 seconds is cancellation
and stale-result grace, not extra execution authority. Heartbeats and exact
attempt/fence matching remain required.

## Hermes adapter class

`HermesReasoningProvider` accepts:

```text
execution_class="bounded-advisory"
```

for ordinary bounded work, with the existing short timeout bound, or:

```text
execution_class="campaign-engineering"
```

for a maximum transport timeout of 1,800 seconds. The larger bound is not
available by accident to ordinary calls.

## Hermes CLI/profile guidance

For a substantial Campaign Runner role started through Hermes CLI, use a
session/run-scoped budget:

```text
hermes chat --run-budget 1800 ...
```

If a dedicated Campaign Runner Hermes profile is later configured, its
`agent.run_budget_seconds` may be set to `1800`; do not set this globally for
ordinary conversations.

For the selected model/provider, a per-model stale timeout may be configured
through the existing Hermes provider model seam:

```yaml
providers:
  <provider>:
    models:
      <model>:
        stale_timeout_seconds: 1800
```

This is a per-provider/per-model override, not a global timeout change. Keep
provider upstream limits and resource health authoritative; extending a local
watchdog does not prove the provider is healthy.

## Outer execution tooling

The foreground terminal tool has its own 600-second call ceiling. That is not
Riverview or Hermes lifecycle policy and is not changed globally. A tracked
background process with an explicit completion notification is the safe way to
run an 1,800-second Campaign Runner proof through this operator surface. The
process remains independently observable and must be verified through
PostgreSQL afterward.

## Fail-closed behavior

- Campaign Runner owns the persisted hard timeout.
- Hermes transport timeout returns failure/interruption evidence.
- A stale lease or fence rejects the result.
- A late result is recorded as stale/late, never accepted.
- No timeout extension may delete history, expire another work item, or bypass
  independent validation.
- Workload class is evidence and routing metadata, not resident identity or
  authority.

## Iteration budget policy

The active Hermes profile currently sets `agent.max_turns: 150` in
`A:/AI/Tools/Hermes/data/config.yaml`. Hermes resolves this through the existing
`agent.max_turns`/`--max-turns` seam; `HERMES_MAX_ITERATIONS` is only a legacy
environment bridge and is not changed here.

Ordinary bounded work keeps the active default. A substantial governed
Campaign Runner/Hermes run may explicitly use:

```text
hermes chat --max-turns 300 --run-budget 1800 ...
```

This is a per-run allowance. It does not alter the profile default, remove the
iteration guardrail, or make runs unlimited. The current API-controlled
conversation cannot safely mutate its own max-turn setting in place; a future
continuation must be started with the explicit CLI override rather than
reconstructing or globally rewriting Tranche 2 configuration.
