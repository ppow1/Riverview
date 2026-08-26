# Hermes/Campaign Runner Bootstrap and Recovery Contract

Status: Tranche 2 bounded recovery contract.

## Problem

If Campaign Runner itself is defective, using the same defective Runner instance
to validate its own repair can create circular false acceptance.

## Authority split

- Campaign Runner normally owns package identity, attempts, leases, fences,
  repair generations, candidate identity, validation, and acceptance.
- Hermes may diagnose and implement a bounded repair package.
- An external bootstrap validator owns only the temporary validation basis for a
  Runner repair when normal Runner validation cannot safely operate.
- Riverview/PostgreSQL remains authoritative for the durable repair record and
  the transition back to normal governance.
- Steward acceptance remains outside all machine completion claims.

## Bootstrap trigger

Use the bootstrap path only when a stable diagnostic checkpoint identifies a
Campaign Runner defect that prevents safe use of the normal claim, repair,
validation, reconciliation, or acceptance path. A model timeout, ordinary
provider failure, stale result, or failed package does not justify bypassing
Campaign Runner.

## Required sequence

1. Identify the defective component and exact checkpoint. Capture the current
   Git SHA, database migration revision, affected objective/package/work-order,
   failure evidence, and the boundary that cannot safely govern itself.
2. Freeze the affected normal path. Do not delete history, expire unrelated
   leases, or manually advance stages.
3. Create a bounded repair specification outside the defective transition. The
   specification must state allowed paths, expected base SHA, acceptance
   criteria, validation commands, classification, and prohibited scope.
4. Allocate a separate repair identity and independent validator identity. A
   Hermes session/profile, worker, or skill is implementation identity only; it
   does not become authority.
5. Execute the smallest repair through the safest available bounded mechanism:
   an external accepted Runner instance, a deterministic local adapter, or a
   Steward-directed bootstrap operation. No arbitrary shell or SQL path is
   introduced.
6. Independently validate the exact candidate against the immutable repair
   basis. The validator must not be the package engineer, must not rely on the
   package engineer's acceptance narrative, and must record PASS/FAIL with
   candidate hash, basis hash, evidence, and defects.
7. If FAIL, stop at repair. Do not loop recursively without a bounded repair
   generation and explicit recovery budget.
8. If PASS, record the bootstrap evidence and repair provenance in PostgreSQL,
   then run the normal Campaign Runner health/reconciliation probes before
   reopening ordinary work.
9. Return to normal governance only after the repaired Runner instance passes
   independent lifecycle, fencing, stale-result, restart/resume, and acceptance
   boundary tests. The bootstrap validator never grants institutional
   acceptance by itself.

## Recovery evidence

Minimum durable references:

- defective component and checkpoint;
- original and repair candidate identity/hash;
- validation basis/hash;
- external validator identity;
- worker and provider/resource identity;
- repair generation and attempt lineage;
- exact test/diagnostic evidence;
- transition-back verification;
- unresolved Steward attention, if any.

## Current status

Tranche 2 defines this contract but does not activate a bootstrap repair or
create a competing lifecycle. The live Campaign Runner/Hermes proof must first
use the normal path. A future bootstrap implementation requires a concrete
Runner defect and a separately accepted repair basis.
