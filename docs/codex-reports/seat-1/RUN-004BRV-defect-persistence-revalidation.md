# RUN-004BRV — Defect Persistence / Repair-Loop Serialization Revalidation

Package: RUN-004BRV  
Role: C1 independent targeted repair revalidator  
Repair implementation commit: `f5250bbdb5d66fed18da8ab268116d1054bff2d9`  
Implementation repository: `ppow1/Riverview`, branch `main`

## Verdict

**PASS**

The RUN-004BV structured-defect serialization blocker is resolved. An
isolated real PostgreSQL schema proof completed the full repair/revalidation
cycle and reached accepted/completed state while preserving durable defects,
repair linkage, and resolution linkage.

## Original defect and implementation inspected

RUN-004BV reproduced a `TypeError: Object of type DefectInput is not JSON
serializable` at the one-go PostgreSQL result boundary. The repair commit adds:

- `DefectInput.as_payload()` and `DefectInput.from_payload()` in
  `src/riverview/campaign/lifecycle.py`;
- `_prepare_execution()` and `_structured_defects()` in
  `src/riverview/campaign/one_go.py`;
- focused serialization tests and PostgreSQL lifecycle assertions.

The repair uses a six-field canonical dictionary representation. It does not
flatten defects through `str(defect)`. Exact keys, non-empty bounded values,
and the allowed severity set are validated on both serialization and reload.

No relay/fencing, acceptance-gate, or downstream-dispatch architecture was
changed.

## Primary isolated PostgreSQL proof

Because the application role cannot create a separate database, I created a
temporary isolated schema in the existing PostgreSQL database, applied the
repository migrations there, forced all validation connections to that schema,
and dropped it after the probe.

The actual `CampaignOneGoRunner`, `RelayStore`, and
`CampaignLifecycleStore` then executed:

```text
writer → independent validator FAIL → structured defects persisted
→ repair_writer → independent revalidator PASS → acceptance
```

Observed result:

```text
OUTCOMES [('writer', 'succeeded'), ('validator', 'succeeded'),
          ('repair_writer', 'succeeded'), ('revalidator', 'succeeded')]
STAGE ('accepted', 'completed')
DEFECTS 1
RESOLVED_LINKED 1
```

The validator result crossed the real PostgreSQL JSONB boundary as canonical
dictionaries. The durable defect row was resolved with both
`repair_attempt_id` and `resolution_attempt_id` populated.

## Structured round trip and multiple defects

The focused serialization tests passed. They exercise JSON encode/decode,
`DefectInput.from_payload()`, equality of all six semantic fields, malformed
key rejection, and over-bound field rejection.

An additional isolated PostgreSQL proof used two defects, one blocking and one
non-blocking:

```text
MULTI [('writer', 'succeeded'), ('validator', 'succeeded'),
       ('repair_writer', 'succeeded'), ('revalidator', 'succeeded')]
      ('accepted', 'completed') 2 2
```

Both defects survived persistence and both received repair/resolution linkage.

## Restart/resume

In a second isolated schema proof, the first runner instance processed only the
writer and validator and stopped after durable defect persistence. A newly
constructed runner with repair/revalidator workers resumed:

```text
RESTART [('writer', 'succeeded'), ('validator', 'succeeded')]
        [('repair_writer', 'succeeded'), ('revalidator', 'succeeded')]
        ('accepted', 'completed') writers 0 defects 1
```

No writer role appeared in the resumed runner outcomes. The repair remained
durably eligible and no duplicate defect was created.

## Regression results

- Structured defect serialization tests: **PASS**.
- One-go unit suite: **PASS** (6 tests).
- First-pass PostgreSQL writer/validator test: **PASS**.
- Isolated PostgreSQL repair/revalidation loop: **PASS**.
- Multiple-defect isolated proof: **PASS**.
- Restart/resume isolated proof: **PASS**.
- Compile/import validation: **PASS**.
- Diff check: **PASS**.

The accepted evidence-bound acceptance, writer/validator independence, and
RUN-003 fencing seams were not weakened by the repair. The repair changes only
defect normalization/reconstruction around the existing fenced completion
boundary. Existing one-go stale/bounded/restart unit coverage passed.

## Contamination classification

The public shared-database repair-loop test did not provide clean evidence:
the fixture returned no claims because accumulated shared relay state and
other expired/claimed rows interfered with work selection. The RUN-003/RUN-004A
regression run also showed the previously observed expired-row contamination.

This is classified **PRE-EXISTING**, not a RUN-004BR regression. The isolated
schema proof crossed the same PostgreSQL JSONB and lifecycle transactions and
completed the full repair loop without that residue.

## Capability assessment

- Original RUN-004BV defect: **RESOLVED**.
- Structured `DefectInput` serialization: **PASS**.
- Structured defect round trip: **PASS**.
- PostgreSQL defect persistence: **PASS**.
- PostgreSQL repair/revalidation loop: **PASS**.
- History preservation: **PASS**; original writer, FAIL validation, defects,
  repair, revalidation, and acceptance remain separate durable records.
- Restart/resume: **PASS**.
- First-pass orchestration regression: **PASS**.
- Independent validator enforcement: **PASS**; no claim/lifecycle gate was
  weakened.
- Revalidator independence: **PASS** in the isolated complete lifecycle.
- Evidence-bound acceptance: **PASS**; no acceptance-gate code changed.
- RUN-003 fencing regression: **PASS by unchanged accepted seam and focused
  stale/bounded coverage**; one public expiry assertion was contaminated by
  unrelated expired rows.
- Stale-result handling: **PASS**.
- Objective-scoped isolation: **PASS**; isolated objectives were used and the
  repair data remained stage/objective scoped.
- Idempotency/bounded execution: **PASS**.
- Failure safety: **PASS**; malformed defect payloads fail closed before
  becoming repair authority and cannot produce acceptance.
- Downstream dispatch gating: **PASS**; repair dispatch follows durable FAIL
  defect persistence, and success follows revalidation acceptance.

## Campaign Runner completion gate

The authoritative RUN-004P/RUN-002 decomposition identifies RUN-004A durable
lifecycle/gates and RUN-004B one-go integration as the Campaign Runner core
packages. RUN-004BR repairs the only blocking RUN-004B defect found by
RUN-004BV. No additional required Campaign Runner core package was identified.

Dashboard, notifier, exceptional arbitration, provider-specific execution, and
later operational enhancements remain separately scoped and are not required
for core completion.

Remaining required Campaign Runner packages: **NONE**  
Campaign Runner core implementation: **COMPLETE**  
Campaign Runner readiness: **ACCEPTED**
