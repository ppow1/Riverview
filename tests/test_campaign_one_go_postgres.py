"""RUN-004B live PostgreSQL one-go lifecycle proofs."""

from __future__ import annotations

import json
from uuid import uuid4

from riverview.campaign import CampaignLifecycleStore, CampaignOneGoRunner, DefectInput, WorkerSlot
from riverview.database import connect
from riverview.relay import RelayStore
from test_campaign_validation_lifecycle import _basis_hash, _package


VERSION = "a" * 40
REPORT = {"status": "succeeded", "result_version_hash": VERSION,
          "implementation_ref": "commit:" + VERSION, "evidence_refs": ["execution:run004b"]}


def _runner(roles, executors, objective_id, relay):
    workers = tuple(
        WorkerSlot(f"run004b-{role}", "C3", (role,), uuid4())
        for role, seat in (("writer", "C1"), ("validator", "C2"),
                           ("repair_writer", "C3"), ("revalidator", "C2"))
        if role in roles
    )
    runner = CampaignOneGoRunner(workers, executors, relay=relay, lifecycle=CampaignLifecycleStore(), objective_id=objective_id, max_steps=12)
    # The lifecycle fixture explicitly queues the initial writer.  Keep this
    # live proof focused on persisted claim/handoff/acceptance; admission is
    # exercised separately without allowing unrelated shared-database rows to
    # enter the fixture's campaign.
    runner.admit_eligible_stages = lambda: ()
    return runner


def test_live_one_go_writer_validator_pass_requires_no_manual_handoff():
    lifecycle, relay, objective_id, stage_id, basis_id, _ = _package()
    lifecycle.queue_writer(objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                           action_type="relay.noop", requested_by="run004b-test",
                           idempotency_key=f"run004b-writer:{uuid4()}", parameters={"delay_seconds": 1}, seat_id="C3")
    basis_hash = _basis_hash(basis_id)
    runner = _runner(("writer", "validator"), {
        "writer": lambda _work: REPORT,
        "validator": lambda _work: {**REPORT, "verdict": "PASS", "basis_hash": basis_hash, "findings_summary": (), "defects": ()},
        "repair_writer": lambda _work: REPORT,
        "revalidator": lambda _work: {**REPORT, "verdict": "PASS", "basis_hash": basis_hash, "findings_summary": (), "defects": ()},
    }, objective_id, relay)
    outcomes = runner.run(max_steps=6)
    assert [item["role"] for item in outcomes] == ["writer", "validator"]


def test_live_one_go_fail_repair_revalidation_accepts_and_preserves_history():
    lifecycle, relay, objective_id, stage_id, basis_id, _ = _package()
    lifecycle.queue_writer(objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                           action_type="relay.noop", requested_by="run004b-test",
                           idempotency_key=f"run004b-repair-cycle:{uuid4()}", parameters={"delay_seconds": 1}, seat_id="C3")
    basis_hash = _basis_hash(basis_id)
    defect = DefectInput("criterion-1", "blocking", "valid", "invalid", "evidence:run004b", "repair")
    runner = _runner(("writer", "validator", "repair_writer", "revalidator"), {
        "writer": lambda _work: REPORT,
        "validator": lambda _work: {**REPORT, "verdict": "FAIL", "basis_hash": basis_hash, "findings_summary": ("defect",), "defects": (defect,)},
        "repair_writer": lambda _work: REPORT,
        "revalidator": lambda _work: {**REPORT, "verdict": "PASS", "basis_hash": basis_hash, "findings_summary": (), "defects": ()},
    }, objective_id, relay)
    outcomes = runner.run(max_steps=12)
    assert [item["role"] for item in outcomes] == ["writer", "validator", "repair_writer", "revalidator"]
    assert outcomes[-1]["status"] == "succeeded"
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("accepted", "completed")
        cursor.execute("SELECT a.role,a.seat_id FROM work_orders w JOIN work_order_attempts a ON a.work_order_id=w.work_order_id WHERE w.objective_id=%s ORDER BY a.started_at", (objective_id,))
        assert cursor.fetchall() == [("writer", "C3"), ("validator", "C3"), ("repair_writer", "C3"), ("revalidator", "C3")]
        cursor.execute(
            "SELECT result_report FROM work_orders WHERE objective_id=%s AND result_report->>'verdict'='FAIL'",
            (objective_id,),
        )
        persisted_report = cursor.fetchone()[0]
        restored_defects = tuple(DefectInput.from_payload(item) for item in json.loads(json.dumps(persisted_report["defects"])))
        assert restored_defects == (defect,)
        cursor.execute(
            "SELECT expected_behavior,observed_behavior,evidence_ref,required_repair,state,repair_attempt_id,resolution_attempt_id "
            "FROM campaign_validation_defects WHERE stage_id=%s",
            (stage_id,),
        )
        defect_row = cursor.fetchone()
        assert defect_row[:5] == ("valid", "invalid", "evidence:run004b", "repair", "resolved")
        assert defect_row[5] is not None
        assert defect_row[6] is not None
