<!-- Version: 0.10.0 -->
# RIV-RDM-0007 - RV-008.3 promotion evidence

Owner: Riverview roadmap transition owner.

## SYMPTOM

Live-looking evidence exists but RV-008.3 remains pending, a transition is
rejected, dependencies do not match, or source/evidence identities differ.

## LIKELY BOUNDARY

Authoritative PostgreSQL roadmap state, transition mechanism, publication SHA,
or incomplete real-boundary evidence.

## SAFE DIAGNOSTIC

```powershell
@'
from riverview.database.connection import connect
with connect() as c, c.cursor() as cur:
    cur.execute("select waypoint_id,status,steward_checkpoint from roadmap_items where waypoint_id in ('RV-004.5','RV-008.3') order by waypoint_id")
    print(cur.fetchall())
'@ | .venv\Scripts\python.exe -
git rev-parse origin/main
```

Compare PostgreSQL state with the accepted transition evidence, not with
GitHub roadmap prose. Trace the same `request_id`, `correlation_id`, source
SHA, Comms version, and doorbell evidence reference across the records.

## EXPECTED HEALTHY RESULT

Only a genuinely accepted end-to-end browser-to-ChatGPT-to-Comms-to-PostgreSQL
result permits the normal RV-008.3 transition. The resulting PostgreSQL row is
`completed`; RV-004.5 remains untouched until its own dependency evaluation.

## KNOWN FAILURE RESULT

- `RIV-RDM-0006`: database roadmap acceptance failure.
- `RIV-RDM-0007`: transition/evidence mismatch.
- `RIV-RDM-0008`: published source SHA mismatch.
- `RIV-RDM-0009`: dependency state mismatch.

The current tranche intentionally remains pending because HTTPS ingress and
ChatGPT application acceptance were not proven.

## REPAIR

Repair only the incomplete evidence or normal transition input. Publish source
before promotion. Use the existing roadmap transition mechanism; never update
the status directly, rewrite history, or infer PostgreSQL state from GitHub.

## VERIFY

Rerun the exact live acceptance, verify all identities and River/mailbox
evidence, then query PostgreSQL after the accepted transition. Confirm
RV-004.5 was not implemented or activated.

## DO NOT

Do not promote on local HTTP health, browser exit code, registration metadata,
GitHub documentation, or a simulated mailbox request.

## EVIDENCE

Transition evidence belongs in PostgreSQL and the bounded diagnostic record;
source identity belongs in GitHub. Keep protected payloads and credentials out
of both.
