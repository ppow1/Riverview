# RIV-EXE-0011 — Same-lineage recovery after infrastructure repair

## SYMPTOM

An approved work order failed for a recoverable execution or reconciliation
reason, Riverview was repaired, and the repair made the approved repository base
stale before the same authorized job could be retried.

## GOVERNED MODEL

The original failure and successor-base eligibility are independent facts. The
original checkpoint does not need to be `RIV-EXE-0008`. `RIV-EXE-0008` describes
the base condition at the time it is discovered; it does not describe why the
first attempt failed.

The generic recovery gate requires an explicitly recoverable checkpoint,
incomplete objective, exact durable authority/specification lineage, unchanged
scope/capability/action/write policy/instruction/paths/acceptance/evidence, and
no existing successful or active successor. The failed work order and execution
remain immutable.

## SAFE RECOVERY

Compare the approved base with the current HEAD. An exact match queues the
canonical immutable successor. A descendant drift is assessed by
`RepositoryDriftAnalyzer`. Narrow drift records revalidation evidence and binds
the successor to the verified current base. Material drift fails closed.

Execution-infrastructure drift is material by default. It may be classified as
`infrastructure_repair_revalidation` only when evidence proves that repository
identity, target paths, capability, action, write policy, instruction,
reconciliation, authority, and task requirements are unchanged; the repair is a
descendant of the approved base; and the repaired behavior is covered by tests.
This bounded proof is not a second full specification approval. Governance or
ingress drift still requires Pat's narrow base confirmation.

## LOCAL RESIDUE

An untracked artifact from the failed attempt is forensic residue, not success
evidence. Preserve its bounded hash/path evidence, quarantine it through the
recovery boundary, and begin the successor from the authoritative clean base.
The successor must recreate and independently reconcile the artifact.

## VERIFY

Verify the successor envelope's refreshed base, exact changed paths, artifact
content, commit tree, publication SHA, reconciliation record, objective status,
and the unchanged original `failed` work order/checkpoint.
