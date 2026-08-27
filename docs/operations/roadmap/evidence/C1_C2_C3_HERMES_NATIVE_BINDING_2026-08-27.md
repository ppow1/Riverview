# C1/C2/C3 Hermes-Native Codex Resource Binding

Date: 2026-08-27
Status: implementation and bounded live verification complete.

## Authority

The authoritative Riverview implementation root for this tranche is:

`A:\Riverview\standalone`

It is on `main`, ahead 13 / behind 1 relative to its configured origin. Existing dirty reconciliation artifacts and unrelated documentation were preserved. No repository relocation, branch creation, reset, cleanup, or history rewrite was performed.

The native Hermes implementation is in:

`A:\AI\Tools\Hermes\hermes-agent`

## Execution path

The verified path is:

`Riverview HermesReasoningProvider` -> loopback Hermes API request -> request-scoped `model_options.codex_seat_id` -> Hermes API server `_create_agent` -> strict seat resolver -> `AIAgent(codex_seat_id, codex_home, codex_identity_fingerprint)` -> `CodexAppServerSession(codex_home=...)` -> child Codex app-server with child-only `CODEX_HOME`.

The prior defect was that Riverview resource/seat metadata did not cross the Hermes API boundary, and native Hermes session construction did not receive a selected seat home.

## Implemented changes

Hermes:

- Added `agent/codex_seat.py` with one strict C1/C2/C3 mapping:
  - C1 -> `A:\AI\CodexProfiles\C1`
  - C2 -> `A:\AI\CodexProfiles\C2`
  - C3 -> `A:\AI\CodexProfiles\C3`
- Explicit seat resolution requires the mapped directory and its `auth.json` to exist.
- Unknown seats and unusable homes fail before child creation.
- AIAgent re-resolves every explicit seat and rejects a mismatched caller-supplied home.
- Native app-server construction receives the resolved home and starts the child with that `CODEX_HOME`.
- Native result runtime metadata records provider, seat, home, execution mode, and the safe identity fingerprint.
- Explicit-seat errors do not recommend or perform fallback through another Hermes runtime or credential source.
- Windows npm `.cmd` Codex launchers are resolved and invoked through `COMSPEC /d /s /c`; ordinary executable launchers remain unchanged.

Riverview:

- `src/riverview/reasoning/hermes.py` validates `codex_seat_id` and forwards it as request-scoped `model_options`.
- No credential material is placed in the request or result.

Tests:

- `tests/agent/test_codex_seat.py`
- `tests/agent/transports/test_codex_app_server_runtime.py`
- `tests/test_hermes_provider_adapter.py`

## Fail-closed contract

- Valid explicit seat + usable mapped home: execute using that home.
- Valid explicit seat + missing/unusable home: explicit failure.
- Unknown seat: explicit failure.
- Explicit seat cannot silently use Hermes' global credential pool, another seat, the default Codex home, or an unqualified Codex credential.
- Unqualified ordinary Hermes operation remains unchanged.
- The child environment is isolated by `CODEX_HOME`; Hermes profiles or additional gateways are not required for per-execution seat isolation.

## Safe identity provenance

Hermes reads the existing ID-token claim structure only to derive a non-secret fingerprint. For these homes, the login email is nested at `https://api.openai.com/profile.email`; only its normalized SHA-256/16 fingerprint is retained.

No raw email, account ID, access token, refresh token, ID token, cookie, password, or credential contents are persisted or emitted.

## Bounded live proof

Each proof used one minimal no-tool request: `Return exactly OK. Do not use tools.` No meaningful work was requested.

| Seat | Hermes-selected home | Execution fingerprint | Result |
|---|---|---|---|
| C1 | `A:\\AI\\CodexProfiles\\C1` | `000f32ae28fba7b8` | completed, `OK` |
| C2 | `A:\\AI\\CodexProfiles\\C2` | `20521e97b56e0445` | completed, `OK` |
| C3 | `A:\\AI\\CodexProfiles\\C3` | `ac91c17202d67add` | completed, `OK` |

The runtime provenance returned by each Hermes execution contained the matching seat, exact home, provider `openai-codex`, execution `codex_app_server`, and matching safe fingerprint.

## Telemetry correspondence

Telemetry was collected immediately before and after the three executions using the existing read-only Codex app-server collector.

Pre-execution:

- C1: fingerprint `000f32ae28fba7b8`, 68% weekly remaining, reset `2026-09-01T18:09:22Z`, available.
- C2: fingerprint `20521e97b56e0445`, 91%, reset `2026-09-01T18:16:02Z`, available.
- C3: fingerprint `ac91c17202d67add`, 94%, reset `2026-09-01T18:14:01Z`, available.

Post-execution:

- C1: fingerprint `000f32ae28fba7b8`, 68% weekly remaining, same reset, available.
- C2: fingerprint `20521e97b56e0445`, 91%, same reset, available.
- C3: fingerprint `ac91c17202d67add`, 94%, same reset, available.

The post-refresh observations remained associated with the same three seats. The rate-limit observations support independent quota pools; they do not by themselves establish separate billing-account semantics. The matching, pairwise-distinct login fingerprints provide the login-level correspondence.

## Verification

- Hermes focused tests: `29 passed`.
- Riverview focused tests with `PYTHONPATH=src`: `22 passed`.
- Hermes changed modules: `compileall` passed.
- Live C1/C2/C3 native app-server executions: 3 completed successfully.
- Report scan: no raw credential, token, email, or private account identifier content.

## Acceptance statements

1. Selecting C1 causes Hermes-native execution under C1 authentication: **proven** by the completed native turn, exact C1 `CODEX_HOME`, and matching C1 fingerprint.
2. Selecting C2 causes Hermes-native execution under C2 authentication: **proven** by the completed native turn, exact C2 `CODEX_HOME`, and matching C2 fingerprint.
3. Selecting C3 causes Hermes-native execution under C3 authentication: **proven** by the completed native turn, exact C3 `CODEX_HOME`, and matching C3 fingerprint.

Interactive authentication was not necessary. Existing authentication remains intact.

## Remaining limitations

- The explicit seat mapping is duplicated across the Estate bridge and Hermes because the repositories are separate runtimes; the two mappings are verified equal but are not imported across repository boundaries.
- The direct native Hermes proof exercised AIAgent/app-server construction. The live Riverview HTTP acceptance below now closes the loopback production-style path.
- The implementation does not infer seat selection from shared `chatgpt_account_id`; explicit C1/C2/C3 selection is required.

## Follow-on live Riverview acceptance

Date: 2026-08-27

### Runtime and entry point

- Riverview root: `A:\Riverview\standalone`
- Riverview runtime SHA at acceptance start: `b0e11ea01bbe8c30cc3275ae037e495741811b6d`
- Entry point: `HermesReasoningProvider.generate(ReasoningRequest)` from `src/riverview/reasoning/hermes.py`
- HTTP target: short-lived loopback Hermes API at `http://127.0.0.1:8643/v1/chat/completions`
- Hermes implementation root: `A:\AI\Tools\Hermes\hermes-agent`
- Gateway version: `0.20.5`
- The existing Hermes listener on 8642 was not restarted, replaced, or inspected for credentials. The acceptance gateway used a temporary Hermes home and a newly generated non-secret API test key, then was terminated after verification.

The request was the smallest practical bounded request: `Return exactly OK. Do not use tools.` It used no tools and requested no meaningful work.

### End-to-end result

| Riverview selected | Hermes request `model_options.codex_seat_id` | Returned provider | Returned seat | Returned `CODEX_HOME` | Returned safe fingerprint | Execution | Result |
|---|---|---|---|---|---|---|---|
| C1 | C1 | `openai-codex` | C1 | `A:\\AI\\CodexProfiles\\C1` | `000f32ae28fba7b8` | `codex_app_server` | `OK` |
| C2 | C2 | `openai-codex` | C2 | `A:\\AI\\CodexProfiles\\C2` | `20521e97b56e0445` | `codex_app_server` | `OK` |
| C3 | C3 | `openai-codex` | C3 | `A:\\AI\\CodexProfiles\\C3` | `ac91c17202d67add` | `codex_app_server` | `OK` |

For every row, the Riverview-selected seat, HTTP request seat, Hermes-resolved seat, exact child home, and returned safe fingerprint agreed. The HTTP response carried only the approved runtime fields; no raw email, token, account ID, cookie, password, or credential content appeared.

### Telemetry

Read-only telemetry immediately before the live run:

- C1: fingerprint `000f32ae28fba7b8`, 67% weekly remaining, reset `2026-09-01T18:09:22Z`, available.
- C2: fingerprint `20521e97b56e0445`, 91%, reset `2026-09-01T18:16:02Z`, available.
- C3: fingerprint `ac91c17202d67add`, 93%, reset `2026-09-01T18:14:02Z`, available.

Read-only telemetry immediately after the live run:

- C1: fingerprint `000f32ae28fba7b8`, 67%, same reset, available.
- C2: fingerprint `20521e97b56e0445`, 91%, same reset, available.
- C3: fingerprint `ac91c17202d67add`, 93%, same reset, available.

No rounded percentage movement was expected from these tiny requests. Identity correspondence and home provenance are the decisive evidence.

### Invalid-seat live boundary check

Riverview attempted to construct `HermesReasoningProvider(..., codex_seat_id="INVALID")`. It was rejected with `ValueError: codex_seat_id must be C1, C2, or C3` before HTTP submission and therefore before Hermes agent or Codex child creation. No real credential store was modified.

### Verification after the live run

- Riverview provider/resource/campaign focused suite: 22 passed.
- Hermes focused suite using system Python fallback: 31 passed in 1.46s.
- Hermes `scripts/run_tests.sh` was attempted first, as required, but could not run because the checkout's `venv` lacks pytest and the runner refuses the system interpreter. No test failure was masked; the identical targeted files passed with `python -m pytest`.
- Hermes and Riverview `git diff --check`: passed.
- No authentication changes, repository relocation, branch creation, reset, cleanup, or unrelated-file modification occurred.

### Final acceptance

1. A real Riverview-originated C1 request executed under C1 authentication: **yes**.
2. A real Riverview-originated C2 request executed under C2 authentication: **yes**.
3. A real Riverview-originated C3 request executed under C3 authentication: **yes**.
4. An invalid explicit seat can reach Codex execution: **no**.
5. The original Tranche 2 seat-label != authenticated-resource defect is closed end-to-end: **yes**.

## Scheduling and resource operationalization

Date: 2026-08-27

### Existing architecture retained

- Estate `codex_seat_telemetry.py` remains the authoritative read-only source for C1/C2/C3 capacity, observation timestamps, reset windows, collection status, and safe identity fingerprints.
- Riverview `ResourceRegistry` remains the scheduler/resource selection layer. No second telemetry store or parallel scheduler was introduced.
- Estate `engineering_capacity_runtime.py` and the Resource & Work Command Center already consume the same `runtime/engineering_capacity/codex_seat_telemetry.json` artifact. Their seat observation projection includes the safe account object, freshness state, capacity, reset, collection status, and source.
- Campaign Runner remains the execution owner; its Hermes adapter continues to receive the selected provider/resource through the existing request envelope. Automatic selection is an upstream resource decision and still supplies the selected seat to the proven Hermes provider.

### Selection policy

`ResourceRegistry.select_codex_seat()` is a bounded wrapper around the existing `select()` policy:

1. Require bounded-engineering capability, River classification, and the requested role.
2. Exclude unhealthy, unavailable, role-incompatible, independently reserved, busy/running/claimed/starting, stale, and unobserved resources.
3. Prefer the greatest observed remaining capacity.
4. Prefer lower workload on equal capacity.
5. Use deterministic resource-id tie-breaking.
6. Return a clear no-eligible-resource result rather than substituting a resource.

Explicit C1/C2/C3 selection remains unchanged and is still pinned to the requested seat by the Hermes provider and strict Hermes resolver. Automatic selection is used only when the caller asks the registry for a Codex seat.

### Resource state projection

`ExecutionResource` now carries the available state needed by scheduling and reporting:

- `seat_id`;
- safe `identity_fingerprint`;
- observed remaining capacity;
- `observed_at` and reset timestamp;
- availability and health;
- optional `current_execution_state`;
- observed `reset_refill_observed` evidence.

The live telemetry currently does not publish a busy state, so no unreliable busy inference is performed. If a producer supplies `busy`, `running`, `claimed`, or `starting`, the registry excludes that resource.

### Reset/refill semantics

No pre-existing reset-jump detector was present in the searched Estate/Riverview paths. The registry now provides the small pure `reset_refill_observed(previous_capacity, current_capacity)` contract and records the result when adjacent observed capacities are supplied. A material upward observed jump is evidence; the advertised reset timestamp is never used as proof by itself.

### Automated coverage

`tests/test_resource_registry.py` covers:

- highest fresh observed capacity;
- explicit resource revalidation;
- stale capacity;
- unavailable capacity;
- unknown telemetry;
- busy-resource exclusion;
- independent-validator exclusion;
- deterministic ties;
- observed reset/refill jumps;
- seat/fingerprint/state projection.

Estate `tests/test_codex_seat_telemetry.py` additionally covers nested provider-profile email extraction into the existing safe fingerprint format. This fixes the current live telemetry shape without exposing the email.

### Live automatic-selection acceptance

Fresh read-only telemetry immediately before selection:

- C1: 66%, available, observed `2026-08-27T01:22:28Z`, fingerprint `000f32ae28fba7b8`.
- C2: 91%, available, observed `2026-08-27T01:22:29Z`, fingerprint `20521e97b56e0445`.
- C3: 93%, available, observed `2026-08-27T01:22:32Z`, fingerprint `ac91c17202d67add`.

The registry considered candidates `codex.seat.C1`, `codex.seat.C2`, and `codex.seat.C3`, and selected C3 with the auditable reason: `weekly fuel 93, fresh observation, workload 0; capacity evidence preferred over round-robin`.

The selected C3 fingerprint was `ac91c17202d67add`. Riverview then constructed the existing `HermesReasoningProvider` with only that registry-selected seat and submitted `Return exactly OK. Do not use tools.` through the real loopback Hermes API.

Returned provenance:

- Hermes requested seat: C3;
- Hermes resolved seat: C3;
- Codex home: `A:\\AI\\CodexProfiles\\C3`;
- safe fingerprint: `ac91c17202d67add`;
- provider: `openai-codex`;
- execution: `codex_app_server`;
- result: `OK`.

Post-execution telemetry remained consistent: C1 66%, C2 91%, C3 93%, all available, with the same three fingerprints and reset windows. No rounded capacity decrement was expected from the minimal request.

### Resource & Work Command Center correspondence

The Command Center and scheduler consume the same Estate telemetry artifact. The refreshed artifact contained exactly the three logical seats, current observed capacity, freshness timestamps, availability, reset information, and safe fingerprints. No duplicate dashboard truth source was added. Current execution state remains optional/unknown because the live telemetry producer does not publish active-run state.

### Files changed in this tranche

Riverview standalone:

- `src/riverview/resources/registry.py`
- `tests/test_resource_registry.py`
- `src/riverview/reasoning/hermes.py` (existing binding path retained; no new automatic execution path)
- this evidence report

Estate telemetry source:

- `src/estate/core/codex_seat_telemetry.py`
- `tests/test_codex_seat_telemetry.py`
- refreshed `runtime/engineering_capacity/codex_seat_telemetry.json` using the existing read-only collector.

Unrelated dirty files and preserved reconciliation artifacts were not changed. The existing Estate `git diff --check` warning for an unrelated Stream Deck file was left untouched.

### Scheduling acceptance

1. Riverview can automatically choose among C1/C2/C3 using live observed resource state: **yes**.
2. Explicit C1/C2/C3 requests remain pinned to that seat: **yes**.
3. The automatically selected seat propagates unchanged into Hermes authentication and execution: **yes, C3 live-proven**.
4. Scheduler and Resource & Work Command Center consume the same authoritative telemetry: **yes**.
5. Stale, unavailable, and unknown resources are safely excluded: **yes**.
6. Reset/refill detection is based on observed capacity evidence rather than advertised reset time alone: **yes**.

Remaining gap: active execution/busy state is accepted and enforced when supplied, but the current telemetry producer does not publish it; the system documents that state as unknown rather than inferring it.

## Strategic resource-management tranche

Date: 2026-08-27
Status: bounded planner and telemetry extension implemented; governed durable policy/claim control remains open.

### Native Codex quota windows

The live `account/rateLimits/read` payload does not label the windows weekly/monthly. It reports one `limit_id=codex` object with:

- `primary`: `windowDurationMins=300` (5 hours), `usedPercent`, `resetsAt`;
- `secondary`: `windowDurationMins=10080` (7 days), `usedPercent`, `resetsAt`.

Estate telemetry now retains both windows independently, including native duration, used percentage, remaining percentage, epoch and ISO reset time, and `reset_is_provider_advertised`. The seven-day window is displayed as the existing weekly fuel field for backward compatibility; no monthly interpretation is asserted.

Live read-only observations:

- C1: 5-hour 49% remaining, reset `2026-08-27T02:36:44Z`; 7-day 65%, reset `2026-09-01T18:09:22Z`.
- C2: 5-hour 100% remaining, reset `2026-08-27T05:26:11Z`; 7-day 91%, reset `2026-09-01T18:16:02Z`.
- C3: 5-hour 96% remaining, reset `2026-08-27T05:24:54Z`; 7-day 93%, reset `2026-09-01T18:14:01Z`.

Reset timestamps are valid forward-planning inputs. They are not treated as historical refill confirmation. Historical refill evidence remains a material observed capacity increase or other provider evidence.

### Usage-reset investigation

The live payload exposes `rateLimitResetCredits` for each of C1/C2/C3. Each currently returned:

- `availableCount=1`;
- one `status=available` credit;
- `resetType=codexRateLimits`;
- title `Full reset (Weekly + 5 hr)`;
- grant and expiry timestamps.

The official Codex app-server documentation identifies `account/rateLimitResetCredit/consume` as the consuming operation. No consume request was sent. Opaque credit IDs are not persisted by the Estate telemetry projection.

The evidence does **not** establish:

- whether the credit is seat-, workspace-, organization-, subscription-, or billing-scoped;
- whether the displayed counts are independently allocated or backed by a shared pool;
- the governing reset-credit period beyond the individual credit expiry timestamps;
- eligibility conditions beyond provider-returned `status=available`;
- exactly what restoration occurs in every provider state;
- whether activation changes a window boundary, plan, or billing state.

Accordingly, scope, period, eligibility, restoration semantics, and programmatic activation authority remain `unknown`. The only known activation mechanism is the documented consuming RPC, and it remains deliberately uncalled. No automatic reset policy exists.

### Planner implementation

Riverview now exposes `ResourcePolicy` and `ResourcePlanner` over the existing `ResourceRegistry`. Supported deterministic modes are:

- `HIGHEST_CAPACITY` (backward-compatible default);
- `BALANCED` (capacity-first balancing behavior, represented through the same bounded selector);
- `ROUND_ROBIN` (in-process deterministic cursor, skipping ineligible resources);
- `DRAIN` with a target seat;
- `PRESERVE` with a target seat while alternatives exist;
- `SOONEST_ROLLOVER` using the earliest retained native-window reset;
- `MAXIMIZE_RUNWAY` using the most constrained retained window;
- `PRIORITY` with an explicit seat order.

All modes share the existing eligibility rules for availability, health, freshness, observed capacity, role, independence reservations, and supplied busy/claimed/running/starting state. Explicit seat selection remains outside this automatic policy path and continues to mean that seat or fail.

### Live policy evaluation and execution

The refreshed live fleet was evaluated without execution under two modes:

- `HIGHEST_CAPACITY` selected C3 because its limiting observed capacity was strongest.
- `SOONEST_ROLLOVER` selected C1 because its 5-hour window rolled over first.

This is a material policy difference and demonstrates that planning is no longer highest-percentage-only.

One minimal live execution was then run under `HIGHEST_CAPACITY`:

- candidates: C1, C2, C3;
- selected seat: C3;
- selected fingerprint: `ac91c17202d67add`;
- Riverview transmitted seat: C3;
- Hermes received/resolved seat: C3;
- Codex home: `A:\\AI\\CodexProfiles\\C3`;
- Hermes fingerprint: `ac91c17202d67add`;
- execution: `codex_app_server`;
- result: `OK`.

The disposable gateway was stopped after the run. No meaningful quota consumption was requested.

### Resource & Work Command Center

The Command Center continues to consume the same Estate telemetry artifact and now renders every retained native window, reset time, reset-credit count, safe fingerprint, freshness, and collection status in its human-readable formatter. Its JSON projection currently contains the three seat observations and both windows per seat.

The regenerated Command Center artifact does not yet carry authoritative resource-policy state, claim identity, or reset-credit fields in the JSON observation projection because that existing projection predates this tranche. It is therefore not claimed to be fully policy-state-parity complete.

### Claims, concurrency, and lifecycle

Existing Campaign Runner PostgreSQL claims are transactionally fenced with `FOR UPDATE SKIP LOCKED`, lease generation, fencing token, worker identity, heartbeats, terminal fencing, and expiry recovery. They safely protect work-order attempts, and release the work-order claim on success/failure through the existing lifecycle. However, they are not yet atomically coupled to `ResourcePlanner` seat selection, so this tranche does not claim that two independent automatic planners cannot select the same free seat before Campaign Runner admission.

The current telemetry producer does not authoritatively publish seat claim/running state. The registry excludes those states when supplied, but no new busy-state truth or inferred timer was introduced.

### Policy control and authority boundary

Repository investigation found no existing durable resource-policy table, control API, or accepted Grace capability for resource-utilization mutations. Existing `GraceAuthority` rules cover bounded authoritative-state reading and coordination, but not drain/preserve/priority policy mutation. Grace HOME Cognition remains separately fail-closed when its authoritative continuity state is unavailable.

Therefore this tranche does not claim:

- one durable authoritative policy state shared by Grace, Steward, scheduler, and Command Center;
- policy mutations through an operational control surface;
- audit records for policy changes;
- Steward lock/override behavior for resource policy;
- live Grace inspection, explanation, or policy mutation;
- Grace-authorized claim lifecycle control.

No YAML/JSON file was promoted as a policy authority. No Grace identity, UUID, authority reference, canon, or HOME Cognition state was fabricated.

### Workload classification

The existing Campaign Runner carries role/request metadata but no verified quantitative token or capacity-cost forecast. The planner therefore does not pretend to forecast token consumption. Workload remains the existing bounded workload field where supplied; cost-aware planning is future work.

### Tests and verification

- Riverview `tests/test_resource_registry.py`, `tests/test_hermes_provider_adapter.py`, and `tests/test_hermes_campaign_executor.py`: passed.
- Estate `tests/test_codex_seat_telemetry.py` and `tests/test_engineering_capacity_runtime.py`: 12 passed.
- Riverview planner/resource modules: compileall passed.
- Estate telemetry/dashboard modules: compileall passed.
- Riverview `git diff --check`: passed.
- Estate `git diff --check`: existing unrelated `tools/streamdeck/estate-status-bridge/src/actions.js:595` blank line warning remains; no unrelated cleanup was performed.
- No reset credit was consumed.
- No authentication, billing, account, repository, branch, Grace, Jessica, or Octominer changes were performed.

### Strategic-tranche acceptance matrix

1. Actual native windows identified: **yes — 5-hour primary and 7-day secondary under `limit_id=codex`; no monthly claim**.
2. All relevant windows retained independently: **yes in Estate telemetry and registry; Command Center JSON projection parity remains incomplete**.
3. Independent C1/C2/C3 rollover times retained: **yes**.
4. Planning uses percentage and time-to-rollover: **yes in the in-process planner**.
5. Soonest-expiring capacity can outrank higher percentage: **yes; live C1 vs C3 policy evaluation**.
6. Advertised reset distinguished from observed refill: **yes**.
7. Usage-reset semantics: **partially known; reset credits are provider-reported full weekly + 5-hour credits**.
8. Reset scope: **unknown**.
9. Reset allocation independent/shared: **unknown; all three currently report one, which is insufficient to prove independence**.
10. Current count: **one provider-reported available credit for each C1/C2/C3**.
11. Eligibility: **provider status `available`; deeper eligibility unknown**.
12. Activation: **documented `account/rateLimitResetCredit/consume`; not invoked**.
13. Restoration: **provider title says weekly + 5-hour full reset; broader restoration semantics unverified**.
14. Safe observation: **yes**.
15. Programmatic activation technically exposed: **consume RPC exists; activation authority and safe policy are not established**.
16. Required authority: **not yet established; future activation must be separately governed**.
17. Multiple strategies: **yes in the in-process planner**.
18. Balanced: **represented and tested through bounded capacity-first balancing behavior; not yet durable policy state**.
19. Highest capacity: **yes**.
20. Round robin: **yes in-process; durable cross-process cursor is not implemented**.
21. Drain C3: **yes in-process policy evaluation; no operational control surface yet**.
22. Preserve C1: **yes in-process policy evaluation; no operational control surface yet**.
23. Soonest rollover: **yes**.
24. Manual priority: **yes**.
25. First-class durable operational policy: **no — existing durable control seam not found and not fabricated**.
26. Durable policy across restart: **no**.
27. Auditable policy mutations: **no**.
28. Grace inspection through accepted seam: **not yet; existing Grace HOME Cognition state remains separately blocked**.
29. Grace policy changes without files/code: **no**.
30. Grace authoritative selection explanation: **planner explanations exist; Grace control integration does not**.
31. Steward override: **not implemented for resource policy**.
32. Steward policy lock: **not implemented for resource policy**.
33. Grace prevented from credentials/subscriptions: **yes; no resource policy capability grants those actions**.
34. Reset activation separately authority-gated: **not implemented; activation remains uncalled and out of scope**.
35. Authoritative live claim/running state: **no; accepted as optional input only**.
36. Automatic selection concurrency-safe at planner-to-claim boundary: **no; existing Campaign Runner claims are safe only after admission**.
37. Two planners can accidentally preselect one seat: **yes, currently possible before atomic claim coupling**.
38. Explicit busy seat substitution: **no; explicit path remains pinned/fail-closed**.
39. Claim release on success/failure: **yes for existing Campaign Runner work-order leases**.
40. Abandoned claim recovery: **yes for existing Campaign Runner leases; not yet seat-planner coupled**.
41. Scheduler/control/durable policy/Command Center all share one policy state: **no; policy control state is not yet present**.
42. Evidence-backed explanation for planner decisions: **yes for in-process planner selections**.
43. Selected/claimed/authenticated resource identity invariant: **yes for the live policy-selected C3 execution; atomic planner claim coupling remains open**.
44. Grace HOME Cognition boundary reported without fabrication: **yes**.

### Remaining next tranche

The next bounded tranche should introduce one PostgreSQL-backed resource-policy/control aggregate through the existing governed control and Grace authority patterns, add an atomic seat claim or lease coupled to planner evaluation, project that aggregate into the Command Center, and expose read/change/explain operations with Steward override/lock semantics. It must be designed against the existing migration and authority conventions before implementation. Usage-reset activation must remain excluded until provider scope, eligibility, restoration, and authority semantics are independently established.

## Durable policy and atomic-claim tranche

Date: 2026-08-27
Status: implementation and deterministic service tests complete; live migration/application and Campaign Runner wiring remain pending.

### PostgreSQL aggregate

Added migration `database/migrations/0049_resource_policy_and_seat_claims.sql` using the repository's append-only numbered migration convention. It defines:

- one `resource_policy` aggregate keyed by `codex-fleet`;
- policy mode, JSONB parameters, revision, actor, authority, rationale, timestamps, and Steward lock;
- append-only `resource_policy_audit` rows containing previous/new revision, mode, parameters, actor, authority, rationale, source request identity, and timestamp;
- one `resource_seat_claims` table with C1/C2/C3 validation, owner/work identity, lifecycle state, safe fingerprint, lease/heartbeat timestamps, and release information;
- a partial unique index over active seat states (`claimed`, `starting`, `running`), making simultaneous active claims for one seat a database conflict;
- a lease-expiry index and an idempotent initial `HIGHEST_CAPACITY` policy row.

The migration has not been applied to a live database in this tranche. No external database state was mutated.

### Control service

Added `src/riverview/resources/control.py`:

- `ResourcePolicyStore.get`, `ensure_default`, `set`, `set_lock`, and `audit`;
- row-locking with `FOR UPDATE` for policy mutation;
- optimistic revision conflict detection;
- Steward-only lock/unlock;
- lower-authority mutation rejection while locked;
- explicit prohibition on reset-credit consumption through ordinary resource policy;
- `SeatClaimStore.claim`, `transition`, `release`, and `recover_expired`;
- `DurableResourcePlanner.claim_automatic`, which loads durable policy, evaluates the existing planner, attempts an atomic database claim, excludes a race loser, re-evaluates, and records the race in its returned explanation.

The resource package exports these services. The existing planner and explicit-seat identity path remain unchanged.

### Governed operational seam

The existing Comms5 surface now exposes:

- `resource_policy_status` — read-only durable policy and audit projection;
- `set_resource_policy` — Steward transport-attested mutation with explicit confirmation and optional expected revision;
- `set_resource_policy_lock` — Steward transport-attested lock/unlock.

Client-body identity is not authority. The current Comms5 transport attests Steward only. No Grace mutation capability was invented: Grace remains escalated by absence of an explicit authority rule and by the separately blocked HOME Cognition authoritative state.

No reset-credit consumption operation is exposed through this ordinary policy surface.

### Atomic claim boundary

The new database index prevents two successful active claims for the same seat. The coordinator re-evaluates automatic selection after a claim conflict and can choose the next eligible seat. Explicit-seat callers are still expected to claim exactly their requested seat and receive a busy/error result rather than substitute.

This service is not yet wired into `HermesCampaignRoleExecutor` or the Campaign Runner admission path. Existing Campaign Runner work-order leases remain authoritative for work-order ownership; the new seat claim table is a prepared, tested resource-level seam, not yet a live end-to-end admission invariant.

### Tests

- `tests/test_resource_control.py`: policy validation, lock rejection, Steward mutation, reset prohibition, duplicate claim rejection, lifecycle transitions, recovery, and claim-race re-evaluation.
- `tests/test_comms5_transport_probe.py`: governed operation classification and unauthenticated mutation rejection.
- `tests/test_resource_registry.py`: exclusion after claim race plus existing strategic policies.
- Combined Riverview focused suite: 41 tests passed.
- Riverview resource/MCP compileall: passed.
- Riverview `git diff --check`: passed.

The tests use injected/fake connections for service behavior and do not represent live Grace or live PostgreSQL acceptance.

### Current acceptance answers

1. Authoritative durable PostgreSQL policy exists in code/migration: **yes; not yet applied live**.
2. Policy survives restart/reload: **schema supports it; live proof pending migration/application**.
3. Planner consumes exact durable state: **yes through `DurableResourcePlanner`; Campaign Runner wiring pending**.
4. Command Center exposes exact durable policy: **not yet; Comms5 status is the current governed read seam**.
5. Policy mutations auditable: **yes in aggregate/service and migration; live proof pending**.
6. Steward can change policy: **yes through the new attested Comms5 operation; live database proof pending**.
7. Steward can lock policy: **yes in service/migration; live database proof pending**.
8. Lower-authority mutation is rejected by lock: **yes in deterministic service test**.
9. Accepted Grace-ready policy control seam: **readiness seam exists at service/authority boundary; Grace mutation transport/rule is not yet accepted**.
10. Grace can inspect state once authoritative HOME exists: **not yet integrated; no fabricated Grace state**.
11. Grace live boundary preserved: **yes; live Grace control remains blocked and unclaimed**.
12. Planner selection atomically coupled to claim: **coordinator and database constraint implemented; production admission wiring pending**.
13. Can two independent planners successfully claim one seat: **no after migration is applied; current pre-claim Campaign Runner path is not yet coupled**.
14. Losing automatic planner re-evaluates: **yes in deterministic test**.
15. Explicit busy seat substitutes: **no; explicit path remains pinned/fail-closed**.
16. Claims release after success: **service release exists; executor wiring pending**.
17. Claims release after failure: **service supports failed release; executor wiring pending**.
18. Abandoned claims recover safely: **lease-expiry recovery exists; live operational recovery proof pending**.
19. Round-robin durable/concurrency-safe: **not yet; current planner cursor remains process-local**.
20. Command Center JSON exposes claims: **not yet**.
21. Every selection has structured provenance: **coordinator returns bounded reason; durable decision record/table is not yet added**.
22. Grace/Steward explanation without LLM reconstruction: **service/planner reason exists; governed read projection pending**.
23. Claimed resource equals authenticated execution: **previous live C3 proof remains valid; new claim-to-executor invariant pending wiring**.
24. Reset credits untouched: **yes**.
25. Unknown reset semantics: **scope, shared-vs-independent ownership, replenishment period, eligibility, exact restoration, and activation authority remain unknown**.

### Remaining implementation tranche

The next step is to wire `DurableResourcePlanner` into the real Campaign Runner admission/execution lifecycle, pass the returned claim identity through Hermes execution, release it from a `finally` path for success/failure/timeout/cancellation, and expose policy/claims/provenance in the existing Command Center read model. The live migration should be applied only through the normal database migration authority, followed by a bounded persistence and claim-race acceptance. Grace mutation remains blocked until an explicit authority rule and valid authoritative Grace HOME state exist.

## Live integration tranche

Date: 2026-08-27
Status: PostgreSQL policy/claim/provenance integration and bounded live proofs complete; native Hermes success remains blocked by an existing registered-command hash mismatch before Hermes dispatch.

### Migration and live policy

The active database target was reverified through the DPAPI-backed application connection boundary without exposing the password: PostgreSQL `127.0.0.1:5432`, database `riverview`, application role `riverview_app`. Before mutation, migration 0049 was absent and all three resource tables were absent. It was applied through `riverview.database.migrations.apply_migration`, not by direct table edits.

Verified after application:

- migration 0049 recorded at version `0.1.0` with matching source checksum;
- `resource_policy`, `resource_policy_audit`, and `resource_seat_claims` exist;
- active-seat partial uniqueness and lease indexes exist;
- exactly one bootstrap `codex-fleet` policy existed at revision 1 / `HIGHEST_CAPACITY`;
- no bootstrap audit row was fabricated.

Migration 0050 was then applied through the same runner. It added the durable round-robin cursor and `resource_planner_decisions` with created/work indexes.

The live Steward control proof changed revision 1 `HIGHEST_CAPACITY` to revision 2 `BALANCED` through `Comms5Service.set_resource_policy` with authenticated Steward transport and explicit confirmation. PostgreSQL, Comms5 status, and the matching audit row agreed. The original policy was restored at revision 3. A live lock proof moved to revision 4 locked; a lower-authority `grace`/`grace` service mutation was rejected without changing policy; Steward unlocked at revision 5. A bounded durable round-robin proof then produced C1 → C2 → C3 across fresh planner instances, with all claims released, and restored `HIGHEST_CAPACITY` at revision 7.

Separate service instances read the same revision 5 policy before the round-robin test, proving policy persistence across reload/process-equivalent construction. The final live policy is revision 7, `HIGHEST_CAPACITY`, unlocked.

### Live claims and provenance

Two concurrent live `DurableResourcePlanner` calls ranked the same preferred seat under `HIGHEST_CAPACITY`; one claimed C3 and the other re-evaluated after the database conflict and claimed C2. Both claims were released. No duplicate active claim existed.

The live claim lifecycle proof verified:

- C1 claim with established safe fingerprint `000f32ae28fba7b8`;
- `claimed → starting → running`;
- heartbeat/lease renewal;
- successful release;
- controlled failed release for C2;
- one-second C3 lease expiry and recovery to `expired`;
- no active resource claims remained afterward.

The structured decision proof persisted a decision ID, policy revision/mode, candidate list, ranking/claim attempts, selected C3, claim ID, and safe fingerprint `ac91c17202d67add`. Comms5 showed C3 unavailable during the claim and selectable again after release. The latest decision is exposed through the same Comms5/operator projection used for policy and claims.

The telemetry artifact has no flattened reset-credit field at this observation point; the projection reports reset-credit count as unknown rather than inferring it. No reset-credit consuming operation was invoked.

### Campaign Runner integration

`CampaignOneGoRunner` now accepts the durable planner/claim store as one ownership scope. With that seam enabled:

1. automatic `AUTO` workers claim through `DurableResourcePlanner` before `RelayStore.claim_fenced`;
2. fixed workers atomically claim their requested seat and fail with `OneGoError` if busy;
3. the selected seat is passed into Relay admission;
4. admitted work seat must equal selected seat;
5. the resource claim is attached to the actual work-order ID;
6. claim transitions are `claimed → starting → running` around lifecycle/executor boundaries;
7. one `finally` releases success or failure claims, including handled exceptions and stale-fence errors;
8. Hermes providers can derive a provider bound to the admitted seat through `HermesReasoningProvider.for_seat`; fixed provider/work-seat mismatches fail closed.

Claim scope is one individual Campaign Runner role/Hermes execution, not the entire multi-stage work-order lifecycle. Writer, validator, repair-writer, and revalidator stages can therefore select independently; a multi-stage workflow does not hold a seat across unrelated idle periods.

The real live runner boundary was exercised with a temporary explicitly named objective. The existing background Campaign Runner claimed/preempted that temporary work and it failed before Hermes at `RIV-RUN-0003: Registered command hash mismatch` for the existing `relay.noop` command registration. The resource reservation was released with `no work admitted`; no Codex/Hermes request was transmitted. This is a pre-existing command-registration drift, not a resource-claim failure. No unrelated runtime was stopped or altered.

The new `SeatClaimStore.renew` API exists, and the live renewal proof passed. Periodic renewal is not yet scheduled by the Campaign Runner around arbitrary long-running executors; the existing Relay heartbeat remains the current long-run owner mechanism.

### Command Center/operator projection

The existing Comms5 `resource_policy_status` and `operator.read_campaign_runner_snapshot` paths now project the same authoritative sources:

- policy mode, parameters, revision, actor, authority, rationale, update time, and lock;
- safe telemetry identity/capacity/health/freshness, quota windows, reset timestamps, observed refill, and reset-credit field when available;
- active and historical claims with safe work/owner identifiers, lifecycle timestamps, lease/heartbeat, and release reason;
- selectable state and exclusion reason per seat;
- latest structured planner decision.

Live projection verification returned policy revision 7, three resources, and the decision record. During the live C3 claim, Comms5 marked C3 non-selectable with reason `active claim`; after release it became selectable again. No separate Command Center state source was introduced.

### Automated validation

- combined resource, Comms5, provider, Campaign Runner, and Hermes adapter focused suite: 50 tests passed;
- Campaign Runner/resource control focused suite: 16 tests passed;
- compileall for resources, campaign, reasoning, MCP, and operator modules: passed;
- Riverview `git diff --check`: passed.

### Acceptance matrix for this live tranche

1. Migration 0049 applied to live Riverview PostgreSQL: **yes**.
2. One authoritative live policy in PostgreSQL: **yes, revision 7 / HIGHEST_CAPACITY / unlocked**.
3. Policy survives planner/service reload: **yes, separate instances read the same policy; restart proof is process-equivalent rather than a service restart**.
4. Campaign Runner real automatic admission uses DurableResourcePlanner: **implemented in `CampaignOneGoRunner` when the durable seam is supplied; no accepted production construction site outside this runner was found, so full runtime wiring is not yet accepted**.
5. Seat atomically claimed before Hermes begins: **yes at the integrated runner seam; native Hermes success proof blocked before Hermes by command hash guard**.
6. Two independent planners claim the same seat simultaneously: **no; live race produced C3 and C2**.
7. Claim loser re-evaluates: **yes, live and deterministic proof**.
8. Explicit claimed seat substitutes: **no; fixed-seat path fails closed**.
9. Claim scope: **one individual Campaign Runner role/Hermes execution**.
10. Claim transitions wired to real execution state: **yes in integrated runner seam; live pre-Hermes failure exercised the cleanup boundary**.
11. Success releases claim: **yes, service/runner tests and live claim proof**.
12. Hermes/provider failure releases claim: **yes for runner handled exception path; native provider failure before dispatch was not reached**.
13. Timeout/cancellation releases claim: **`finally` covers handled timeout/cancellation exceptions; dedicated native timeout/cancellation live proof remains pending**.
14. Stale/orphan recovery: **yes, live lease-expiry recovery proof**.
15. Legitimate long-running lease retention: **renewal API and live renewal pass; periodic Campaign Runner renewal integration remains pending**.
16. Durable round-robin state: **yes, migration-backed cursor**.
17. Round-robin concurrency-safe: **cursor advancement is row-lock protected; live sequence proof passed across fresh planners**.
18. Structured authoritative provenance: **yes, migration-backed decision rows**.
19. Exact selection/exclusion explanation: **yes from candidate/claim-attempt/ranking/reason fields; live claim race is persisted**.
20. Command Center authoritative policy: **yes through existing operator/Comms5 projection**.
21. Command Center real claims: **yes, active and historical claim projection**.
22. Claimed/running seat unavailable: **yes, live C3 projection proof**.
23. Steward live mutation: **yes, revision/audit/readback matched; restored**.
24. Steward lock blocks lower authority: **yes, live lock proof**.
25. Automatic seat through policy → decision → claim → Campaign Runner → Riverview → Hermes → CODEX_HOME → fingerprint → authenticated execution: **not fully accepted; the real attempt stopped at existing `RIV-RUN-0003` before Hermes, while the prior native C3 proof remains valid outside this claim-integrated path**.
26. Controlled execution failure releases claim: **yes in deterministic integrated runner test and live pre-Hermes terminal failure; native Hermes failure was not reached**.
27. Reset credits untouched: **yes**.
28. Grace mutation fail-closed: **yes**.
29. Grace-ready read/control seam without fabricated identity: **reusable read/service APIs exist; no Grace transport or mutation authority was fabricated**.
30. Remaining before operational completion: **wire the durable seam into the accepted production Campaign Runner construction; repair or migrate the stale `relay.noop` command hash through its normal authority; add periodic claim renewal to the long-run owner; complete native Hermes success/failure end-to-end with claim ID/decision ID; and expose/verify the projection through the final Command Center client surface if distinct from Comms5/operator JSON.**

No authentication, billing, subscription, reset-credit, Grace identity, Jessica, Octominer, repository, branch, or unrelated runtime state was modified. Temporary acceptance objectives were explicitly named; their resource claims were released, while their durable test records remain as evidence rather than being deleted directly.

## Production runner and integrity follow-up

The accepted production construction path is `riverview.runtime.supervisor` → managed `relay-worker` → `riverview.relay.worker.RelayWorker` → `riverview.runner.RestrictedRunner`. There is no `CampaignOneGoRunner` construction in the runtime `src` tree; its durable seam remains the explicit campaign orchestration API and test path. The actual managed worker now constructs `ResourceRegistry.from_codex_telemetry()`, `ResourcePolicyStore`, `SeatClaimStore`, and `DurableResourcePlanner` by default. Automatic worker admission is therefore `DurableResourcePlanner.claim_automatic` → PostgreSQL resource claim/decision → `RelayStore.claim(... seat_id=selected)` → restricted execution. The worker was reloaded three times through the supervisor allow-listed `reload_service` request; only the owned `relay-worker` was recycled. Final status showed one supervisor-owned running worker, PID `13232` at the final readback, with no duplicate worker ownership.

The `relay.noop` integrity drift was traced to a legitimate current implementation at `tools/powershell/relay/Invoke-RiverviewNoOp.ps1` whose SHA-256 was `c5d14d0480b734847c89d7b5f79e1bcf185037359a2affd1ca93d036066ce6a9`, while both `relay.noop` and `relay.timeout_probe` stored stale SHA-256 `6c8adf56de0e92b6a479aab4eb12606541dd224388aa8b191fae82194c7f6bb4`. The existing repository-owned `riverview.runner_health.acceptance` authority computed the current digest and reconciled both approved registrations, then exercised bounded success and timeout probes. PostgreSQL readback now matches the current script digest. The hash check in `RestrictedRunner._command` was not bypassed, weakened, or caught-and-ignored; future genuine drift remains fail-closed at `RIV-RUN-0003`.

The health utility initially reported failure twice because a concurrent legitimate worker consumed the unique acceptance order, making the temporary worker’s `completed_orders` counter an invalid completion assertion. The harness was corrected to assert the unique work-order status and persisted notification instead. The corrected production worker health acceptance passed: notification received, work completed, polling recovery true, and bounded stop true.

Production resource lease timing is now explicit: 300-second lease, 100-second renewal cadence, renewal owner is the executing `RestrictedRunner` worker, renewal begins only after resource claim attach and `starting`/`running` transitions, and renewal stops before terminal release. A renewal error is recorded and causes failed terminal cleanup; orphaned claims remain recoverable by `SeatClaimStore.recover_expired`. The existing Relay heartbeat remains active as the work-order fence heartbeat. A dedicated long-running native Codex execution beyond one lease was not run in this bounded tranche; the renewal loop is unit-covered at construction and integrated in the real worker path.

Decision/claim/execution correlation was corrected at the compatibility boundary: `RelayStore.claim()` now preserves the fenced work correlation ID. Final live readback correlated work order `8dd0207c-a02f-463a-bc13-97acf11b6c84` with Relay correlation `f3420d24-7c08-457c-8ef3-2d24c8595cbb`, seat `C3`, claim `0316e413-03ab-4341-950b-6564a7330208` (released), safe fingerprint `ac91c17202d67add`, decision `5a2571f1-100a-405b-bfab-bc0c1ab1aa12`, policy revision `7`, and decision execution correlation `f3420d24-7c08-457c-8ef3-2d24c8595cbb`. Active resource claims were zero after completion.

The actual client-facing Resource & Work surface is the existing operator projection `operator.read_campaign_runner_snapshot`, which now embeds `Comms5Service.resource_policy_status`; Comms5 HTTP/MCP exposes the same authoritative resource bundle. No second state system or separate client projection was introduced. The live operator projection returned policy, three resources, claims, and the latest decision. The final desktop/web visual consumer was not found in the Riverview repository, so a distinct UI-client acceptance is not claimed.

The requested true service-restart persistence proof was performed as a supervisor-owned `relay-worker` recycle. Policy remained revision 7 / `HIGHEST_CAPACITY` / unlocked, round-robin cursor remained 3, and durable decision/audit state remained present. This proves service restart does not alter policy/control state; the resource stores themselves are PostgreSQL-backed and were also reconstructed in the restarted worker.

Native Hermes/Codex success remains not accepted in this tranche. The production worker proof reached real planner, claim, Relay admission, integrity verification, execution, and release using the bounded registered no-op action, but it did not dispatch a native `HermesReasoningProvider` request. The earlier native Hermes attempt was correctly stopped before Hermes by the stale hash guard. Native Hermes success, native provider failure, and native timeout therefore remain pending rather than being represented as completed.

Campaign stages continue to claim independently at the individual role/execution granularity. No stage executes without a resource claim in the integrated runner seam. Writer/validator/repair/revalidator continuity is not held across idle stage boundaries; each active role can be selected by current policy. Cancellation is not a first-class production RelayWorker operation, so no artificial cancellation interface was added. Grace read access is structurally ready through the same Comms5/operator resource read seam; Grace mutation remains fail-closed without legitimate authority. Reset credits remain read-only and untouched: C1=1, C2=1, C3=1.

### Updated acceptance answers

1. Accepted production path: Runtime Supervisor → RelayWorker → RestrictedRunner → durable planner/claims → Relay → restricted executor/Codex path.
2. Every production automatic Relay/Codex admission through the managed worker now uses DurableResourcePlanner; no runtime `CampaignOneGoRunner` constructor exists in `src`.
3. `RIV-RUN-0003` was caused by stale PostgreSQL command hashes for a legitimate unchanged-in-purpose no-op script.
4. Yes. Existing `runner_health.acceptance` reconciled both registrations; hash enforcement stayed active.
5. Yes. Genuine future drift still fails closed at `RIV-RUN-0003`.
6. Yes. The final production worker request created decision `5a2571f1-100a-405b-bfab-bc0c1ab1aa12`.
7. Yes. It atomically claimed C3.
8. Yes. Claim `0316e413-03ab-4341-950b-6564a7330208` correlated to the admitted work order and Relay correlation.
9. Yes for the real Relay execution path; native Hermes receipt remains pending.
10. Not accepted for this claim-integrated live path; the native Hermes dispatch was not reached.
11. Yes. C3 matched `ac91c17202d67add`.
12. Bounded native Codex execution: not accepted; registered no-op execution succeeded. Native Hermes/Codex: pending.
13. Yes. The production claim was released and active claims returned to zero.
14. Yes for controlled/integrated executor failure paths; native Hermes failure remains pending.
15. Yes for the controlled runner timeout/failure cleanup path; dedicated native timeout remains pending.
16. Cancellation is not a first-class supported RelayWorker operation; no fake proof was created.
17. Yes. Production renewal runs at 100 seconds against a 300-second lease.
18. Yes. Expiry and recovery remain live-verified.
19. The renewal design protects valid long work; a multi-minute native execution proof remains pending.
20. Yes through the existing operator snapshot plus Comms5 resource projection; a distinct visual client was not found.
21. Yes. Claimed seats project unavailable with active-claim reason.
22. Yes. Released seats project selectable again.
23. Yes. Supervisor-owned relay-worker restart preserved policy/control state.
24. Yes. Durable cursor value and decision/audit rows survived restart.
25. Yes structurally through Comms5/operator read APIs.
26. Yes. Grace mutation remains authority-gated and fail-closed.
27. Yes. Reset credits were not consumed.
28. Full operational completion still requires native Hermes success/failure/timeout acceptance carrying decision/claim provenance, a dedicated valid long-running renewal proof, and confirmation of any external client UI beyond the existing operator/Comms5 JSON projection. Production durable admission, hash integrity, claim lifecycle, renewal implementation, service restart persistence, and claim/execution correlation are now live and accepted.

## Native Hermes follow-up

The live Hermes loopback endpoint was reverified at `http://127.0.0.1:8642/health` and returned healthy Hermes Agent status (`0.20.5`). A single bounded request with instruction `Return exactly OK. Do not use tools.` and `model_options.codex_seat_id=C3` was attempted through `HermesReasoningProvider` using the existing loopback endpoint. The endpoint returned `HermesAuthenticationError`; the Riverview process environment contained neither `HERMES_API_SERVER_KEY` nor `API_SERVER_KEY`. No credential was read from files or copied from the managed Hermes process. Native Hermes/Codex success was therefore not claimed.

The production worker path remains independently live-verified after this attempt: its latest accepted bounded order correlated a durable decision, C3 claim, Relay correlation, safe fingerprint, successful registered command, and release, with zero active resource claims afterward. The current live state remains policy revision 7 / `HIGHEST_CAPACITY` / unlocked, round-robin cursor 3, migration 0049 and 0050 applied, and `relay.noop` registration equal to the current script SHA. Reset credits remain untouched.

### Final status

- Production durable planner injection: accepted.
- PostgreSQL claim/decision lifecycle: accepted.
- Command-hash reconciliation: accepted; future drift remains fail-closed.
- Periodic 300-second/100-second production renewal: implemented and loaded by the supervisor-owned worker.
- Decision → claim → work-order → execution correlation: accepted for the production Relay path.
- Supervisor-owned relay-worker restart persistence: accepted.
- Production bounded success/failure/timeout cleanup: accepted at the restricted execution boundary.
- Native Hermes success: blocked by missing authorized API-server credential in the calling process; not claimed.
- Native Hermes controlled failure and native timeout: not reached; not claimed.
- Cancellation: not a first-class RelayWorker operation; no artificial interface added.
- Visual Command Center client: no distinct consumer found in the Riverview repository; the existing operator/Comms5 JSON projection is the accepted client-facing read surface for this codebase.
- Grace read seam: ready; Grace mutation remains fail-closed.
- Reset-credit consumption: none.

## Supported Hermes authentication projection

Date: 2026-08-27

The Hermes API server authenticates HTTP callers with a bearer API key. Hermes
resolves that key from the active profile's process environment, populated by
the profile-scoped `.env`; loopback locality does not bypass authentication.
The supported Hermes configuration command is `hermes config set
API_SERVER_KEY <generated-value>`. A source-routing defect omitted
`API_SERVER_KEY` from Hermes' environment-key allowlist, causing the first
attempt to write an ineffective YAML setting. That defect was fixed and
covered by `TestExplicitAllowlist.test_explicit_key_routes_to_env`.

The authoritative credential now lives only in the managed Hermes profile
`.env` at `A:\\AI\\Tools\\Hermes\\data\\.env`. The stale top-level YAML
assignment was removed through the supported Hermes config commands. The key
value is not recorded here and is not present in Riverview planner decisions,
claims, work orders, resource telemetry, operator/Comms5 projections, logs, or
evidence.

Riverview uses the existing Runtime Supervisor child-environment projection.
The `relay-worker` service declares the Hermes `.env` as `secret_file`,
`API_SERVER_KEY` as `secret_key`, and `API_SERVER_KEY` as `secret_env`. The
Supervisor extracts the named scalar only at child start and injects it into
the Relay worker environment; Riverview does not scrape Hermes, inspect a
Hermes process environment, or require manual key pasting. The reference is
durable across Supervisor and worker restarts. The Supervisor was reloaded
through its normal request-file protocol and reported `credential_available:
true` for the running worker.

Hermes gateway restart and key rotation were performed through `hermes gateway
restart`. A bounded provider request executed under the exact Supervisor
projection returned `OK` with C3 metadata preserved. A provider invocation
without the projected environment failed closed with `HermesAuthenticationError`;
there is no unauthenticated localhost fallback. Transport authentication is
independent of C1/C2/C3 Codex authentication: the transport key authorizes the
Riverview-to-Hermes HTTP request, while the selected seat, CODEX_HOME, and
safe fingerprint remain resource-specific.

The production Relay worker health acceptance passed after projection and
reload: notification received, work completed, polling recovery true, and
bounded stop true. The Riverview focused suite passed 58 tests. Hermes' focused
config-routing test passed 14 tests. A broader Hermes gateway test invocation
was not accepted as a clean suite result because this Windows environment's
Hermes virtual environment lacks `concurrent_log_handler`; 122 tests passed,
12 failed at import/setup for that missing dependency, and 62 async tests
were skipped by the unavailable async pytest plugin. No authentication result
is inferred from that incomplete suite.

### Authentication acceptance boundary

Authentication projection and an authenticated Hermes adapter request are now
accepted. The managed `codex.engineering.v1` production worker still invokes
`CodexCliAdapter`; it does not construct `HermesCampaignRoleExecutor` or
dispatch a native `HermesReasoningProvider` request. Therefore the following
are deliberately not claimed as complete: claim-integrated native Hermes
success, native Hermes/provider failure cleanup, native timeout cleanup, and
multi-minute native Hermes lease renewal. The next implementation must wire
the existing Hermes campaign executor into the accepted production execution
boundary without weakening command integrity, claim semantics, seat identity,
Grace authority, or reset-credit isolation.

Grace remains read-ready and mutation fail-closed. Reset credits remain
read-only and untouched: C1=1, C2=1, C3=1.

## Production Hermes routing follow-up

The previous managed production path for `codex.engineering.v1` resolved an
`ExecutionEnvelope` and invoked `CodexCliAdapter` directly. That behavior was
authoritative in `RestrictedRunner._execute_codex`; it was not a fallback
selected by configuration.

The routing boundary now dispatches `codex.engineering.v1` to
`RestrictedRunner._execute_hermes`, which constructs the existing
`HermesReasoningProvider` and `HermesCampaignRoleExecutor` seam. The provider
is created only after durable claim admission and is bound to the claimed
seat. A missing seat/correlation or provider seat mismatch fails closed.
Hermes/provider errors propagate through the existing runner terminal cleanup;
there is no direct `CodexCliAdapter` fallback for this action class. The
registered no-op and timeout actions retain their existing command execution
adapter.

The Hermes request carries runtime correlation through the typed request and
work-order boundary, not prompt authority. The returned report includes only
non-secret execution metadata: execution class, provider identity, Hermes
response identity/evidence references, work-order correlation, and claimed
seat. The Supervisor-projected `API_SERVER_KEY` remains process environment
only and is not added to request metadata, planner state, or provenance.

Validation passed:

- routing regression proves `codex.engineering.v1` selects Hermes and does not
  invoke the direct Codex adapter;
- Hermes campaign executor/provider tests passed;
- complete focused Riverview suite passed (61 tests in this routing tranche);
- compileall and `git diff --check` passed;
- managed Relay worker health remained healthy after the routing change.

Full live native acceptance was not performed because the authoritative
PostgreSQL database contains no queued `codex.engineering.v1` work order and
no active Steward authority grant. No intent, authority grant, or work order
was fabricated. Consequently, the following remain unaccepted: a live
claim-integrated Hermes success, CODEX_HOME/fingerprint readback through the
new production route, Hermes authentication-failure cleanup, authenticated
post-provider failure cleanup, native timeout, and a native execution crossing
the 100-second renewal cadence. Existing claim cleanup, renewal, and
operator/Comms5 projection proofs remain valid for their accepted boundaries.

No active Steward authority was changed. Grace remains read-ready and
mutation fail-closed. Reset credits remain untouched: C1=1, C2=1, C3=1.

## Comms5 Steward transport restoration attempt

On 2026-08-27 the authoritative root was independently verified as
`A:\\Riverview\\standalone`, on `main`, and the live Runtime Supervisor status
reported the same repository root and the Windows Task Scheduler supervisor.
Existing unrelated dirty work was preserved.

The Supervisor-owned `comms5-transport` service is the documented SSH reverse
tunnel launched from the service registry as:
`ssh.exe -N -T -o ExitOnForwardFailure=yes -o ServerAliveInterval=30
-o ServerAliveCountMax=3 -o ConnectTimeout=10 -i <approved user SSH key>
-R 127.0.0.1:11826:127.0.0.1:11826 root@64.227.21.54`.
Its topology is VPS loopback `127.0.0.1:11826` -> SSH reverse forwarding ->
Windows loopback `127.0.0.1:11826` -> Comms5 HTTP. Caddy runs on the approved
VPS and proxies the authenticated external `/comms5/mcp` route to that VPS
loopback listener.

The exact exit-255 root cause was a stale prior SSH forwarding session already
holding the VPS listener. SSH authentication and network reachability were
successful, but `ExitOnForwardFailure=yes` correctly terminated the new
Supervisor attempt with `remote port forwarding failed for listen port 11826`.
The stale process was identified by exact command, age, parentage, and matching
remote listener before removal. It was terminated, and the current Supervisor
was asked through its normal request-file control protocol to reload the
service.

Restoration verification:

- `comms5-http`: running;
- `comms5-transport`: running under the active Supervisor;
- exactly one actual matching Windows `ssh.exe` reverse-tunnel process;
- VPS listener present on `127.0.0.1:11826`;
- approved public endpoint rejects unauthenticated access with HTTP 401;
- local loopback backend is reachable and returns protocol-level 406 to an
  incomplete request;
- no bearer or credential value was read, logged, or recorded.

The current Hermes session has no Comms5 connector bearer and no authenticated
Steward transport context. Therefore no `comms5_store_specification`,
`comms5_submit_steward_seed`, or `comms5_confirm_and_promote_seed` mutation was
performed. In particular, no client-supplied identity or forged
`X-Riverview-Comms5` header was used. Promotion remains gated on the trusted
Caddy-injected `X-Riverview-Comms5: 1` and
`X-Riverview-Comms5-Principal: steward` attestation.

The exact next Steward operation remains
`comms5_confirm_and_promote_seed`, following storage of a new bounded
acceptance specification and submission of its new draft seed through the
authenticated connector. No new specification, seed, authority grant, or
work order was created in this restoration attempt. Grace remains read-ready
Grace remains read-ready and mutation fail-closed; reset credits remain untouched.

## Exactly-once formation incident (2026-08-27)

This incident record supersedes any earlier statement that this acceptance had no
queued work order. The authoritative root remained
`A:\\Riverview\\standalone`; the current live PostgreSQL state was read without
creating a specification, seed, authority, intent, or replacement order.

The authenticated Steward invoked `comms5_form_and_queue_work` once with
idempotency key `6b2dd3e2-4d7e-4b2a-bf07-5f5d1e6a3a4c`. It formed the existing
EngineeringIntent `098e2e1d-fc3f-4010-a7a3-c1d92ba37c68` and created order
`08c86a2e-4f26-4907-9692-6ce9714fa825` at approximately
`2026-08-27 13:24:20.101504 -04:00`. The authority
`688b357d-c5f9-4403-9cb1-fd6f122fdf6a` is legitimately consumed and was not
reactivated.

A second order, `10c5352f-4c4f-4a63-9e49-9281003a11e8`, was created at
approximately `2026-08-27 13:24:21.284587 -04:00`. It has the same durable
correlation and the same `engineering_intent_id` parameter, but its idempotency
key is `grace:seed:d617aa55-6e40-4102-82ee-02e64e6c0367:validate`; its objective
and stage columns are null. Its queued event causation is its own work-order ID.

The first creator is proven by the code path
`Comms5Service.form_and_queue_work -> EngineeringIntentStore.form_and_enqueue
-> EngineeringIntentStore.bind(on_bound=enqueue) ->
RelayStore.enqueue_in_transaction`. The first order uses
`engineering-work-order:authority:688b357d-c5f9-4403-9cb1-fd6f122fdf6a`.

The second creator is proven by the existing Grace continuation path:
`ContinuousMomentumEngine.cycle_until_quiescent ->
ContinuousMomentumEngine.enqueue_declared_action ->
GraceMomentum.enqueue_declared_action -> RelayStore.enqueue`. The relevant
implementation is `src/riverview/autonomy/control.py:389-397` and
`:205-223`. Its key is derived from objective/stage (`grace:{objective_key}:{stage_key}`),
not from the consumed authority or EngineeringIntent. The topology graph also
explicitly identifies Grace as an enqueue owner. This is not a second Steward
formation call.

Root cause: Model A and the automatic Grace redispatch path were both acting as
initial work-order creators. The database uniqueness constraint covers only
`work_orders.idempotency_key`; the two producers supplied different keys. There
is no durable uniqueness constraint on the initial EngineeringIntent identity.
Therefore timing and in-process behavior allowed two queued rows for one typed
intent.

Immediate live state after containment attempt:

- both orders remain `queued`;
- neither has a claim, attempt, lease, worker, started timestamp, or terminal result;
- no C1/C2/C3 claim is active for either order;
- Relay worker `relay.primary` is reported `running`, but the normal Supervisor
  stop request was refused with `RIV-RUN-0001: service ownership is ambiguous;
  refusing recycle`;
- no database row was deleted or altered and no arbitrary cancellation was
  performed;
- no execution has occurred, and both executions remain a live admission risk.

The repository has no existing accepted work-order cancellation, duplicate-mark,
hold, or admission-pause operation. Because Supervisor refused the normal stop
and no approved durable duplicate-reconciliation operation exists, this report
intentionally does not invent one or directly update either work-order row.
Accordingly, the acceptance remains `FAILED/BLOCKED` at the exactly-one
work-order invariant.

Corrective implementation is blocked pending an approved reconciliation
capability for these two existing queued rows. The safe architectural correction
is Model A: direct governed formation remains the sole initial enqueue owner;
Grace must recognize an already-bound/enqueued intent and never independently
create an initial order. A database-level unique invariant on initial work orders
by `parameters->>'engineering_intent_id'` (excluding explicitly modeled successor
orders) is also required, but cannot be applied while the two existing queued
rows remain unreconciled.

---

## Closeout: accepted C1/C2/C3 Hermes resource-binding lane

Date: 2026-08-27
Status: C1/C2/C3 HERMES RESOURCE-BINDING ACCEPTANCE: CLOSED / PASSED

This section supersedes the earlier interim state above. The forensic incident
history is retained unchanged.

### Accepted governed lineage

- EngineeringIntent: `098e2e1d-fc3f-4010-a7a3-c1d92ba37c68`
- consumed authority: `688b357d-c5f9-4403-9cb1-fd6f122fdf6a`
- original initial work order: `08c86a2e-4f26-4907-9692-6ce9714fa825`
- former duplicate: `10c5352f-4c4f-4a63-9e49-9281003a11e8` — preserved,
  cancelled, and non-admissible
- governed successor: `10bb0db2-fb9d-48af-9e98-0501502c758f`
- successful attempt: `58efdeb7-b0a3-4ed3-bb39-c2f7a81b28e4`

The original failed attempt remains preserved. Recovery used the existing
successor model and a bounded idempotent same-successor requeue for a proven
pre-execution infrastructure failure. No new EngineeringIntent, authority,
initial order, specification, seed, reset credit, or unrelated work order was
created.

### Resource and Hermes proof

- policy: `codex-fleet`, revision `7`, mode `HIGHEST_CAPACITY`
- selected resource: `C3`
- safe fingerprint: `ac91c17202d67add`
- Hermes resource identity: `codex:C3`
- provider: `hermes:codex.engineering.v1`
- execution mode: `hermes-http`
- native mechanism: Codex app-server
- Hermes request: `hermes:request:6470769c-9945-4df1-a04a-19e5d3045b04`
- Hermes response: `hermes:response:8e61c214-ed1b-4168-a0d4-5eb703ddcd1c`
- result: exactly `OK`
- successor terminal state: `succeeded`, exit code `0`
- resource claim: released after completion

Riverview selected C3, propagated `codex_seat_id=C3`, and Hermes resolved the
same `codex:C3` identity. The earlier native C1/C2/C3 proof records the exact
mapped homes and safe fingerprints. No raw email, access token, refresh token,
ID token, bearer, password, cookie, account ID, API key, or credential content
is present in this report.

### Runtime and database corrections

The accepted implementation includes strict C1/C2/C3 binding and safe
fingerprints, Riverview-to-Hermes seat propagation, durable resource policy and
planner decisions, claim/binding lifecycle, Supervisor-projected Hermes
authentication, production `codex.engineering.v1` routing, governed formation,
duplicate reconciliation, Grace/CME exactly-once reuse, the one-initial-order
per EngineeringIntent database invariant, governed successor recovery, targeted
exact-work-order admission, and bounded PostgreSQL connection retry.

The PostgreSQL correction retries only transient connection establishment with
bounded backoff; query and schema failures remain fail-fast. Focused tests and
compile checks passed before closeout, and the final live execution completed
through the authenticated production path without modifying the bounded payload.

### Invariants after acceptance

- exactly one non-cancelled initial work order remains for the EngineeringIntent;
- the former duplicate remains cancelled/non-admissible;
- only one governed recovery successor exists;
- the successor is terminally successful;
- the acceptance-specific claim is released;
- no new acceptance work was created.

### Non-blocking follow-up items

These are explicitly outside this closeout and do not block the passed
acceptance:

1. `CODEX_HOME` is not yet durably surfaced in the current execution-result
   schema.
2. The legacy campaign execution-envelope/result join remains incomplete for
   this path.
3. Comms5 resource-policy discovery still publishes an open parameters object.
4. PostgreSQL churn/startup stability may warrant a separate follow-up despite
   bounded connect retry supporting this successful run.
5. Resource-binding/reset-first/default scheduling semantics remain parked in
   `PL-0013 Codex Resource Binding and Reset-First Capacity Policy`; PL-0013 is
   preserved but not activated here.
