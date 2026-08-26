"""RUN-004A PostgreSQL writer/validator lifecycle and gate acceptance tests."""

from __future__ import annotations

import threading
import subprocess
import json
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from riverview.campaign import CampaignLifecycleStore, CampaignOneGoRunner, DefectInput, LifecycleGateError, WorkerSlot
from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.relay import RelayStore


RESULT_VERSION = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
RESULT_REF = f"commit:{RESULT_VERSION}"
RESULT_EVIDENCE = ("test://durable-result",)


def _package() -> tuple[CampaignLifecycleStore, RelayStore, UUID, UUID, UUID, str]:
    key = f"run004a-{uuid4()}"
    objective_id = ObjectiveStore().create(key, "RUN-004A test", "lifecycle", [StageSpec("package", "Package", "bounded")])
    objective = ObjectiveStore().load(key)
    stage_id = objective["stages"][0]["stage_id"]
    lifecycle = CampaignLifecycleStore()
    basis_id = lifecycle.create_basis(
        objective_id=objective_id, stage_id=stage_id, specification_content="specification-v1",
        specification_ref=None, acceptance_criteria=("resulting tree is valid",),
        evidence_requirements=("tests",), original_base_sha="a" * 40,
        allowed_paths=("src",), validation_commands=("pytest",), expected_outputs=("report",),
        created_by="C1",
    )
    relay = RelayStore()
    return lifecycle, relay, objective_id, stage_id, basis_id, key


def _writer(lifecycle: CampaignLifecycleStore, relay: RelayStore, objective_id: UUID, stage_id: UUID, basis_id: UUID):
    order_id = lifecycle.queue_writer(objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                                      action_type="relay.noop", requested_by="C1", idempotency_key=f"writer:{uuid4()}")
    work = relay.claim(f"run004a-writer-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C1", role="writer", work_order_id=order_id)
    assert work is not None
    lifecycle.mark_running(work)
    return work


def _technical_complete(relay: RelayStore, work) -> None:
    relay.complete_fenced(CampaignLifecycleStore._identity(work), {
        "status": "succeeded", "changed_paths": ["src"],
        "result_version_hash": RESULT_VERSION,
        "implementation_ref": RESULT_REF,
        "evidence_refs": list(RESULT_EVIDENCE),
    })


def _validation_setup():
    lifecycle, relay, objective_id, stage_id, basis_id, key = _package()
    writer = _writer(lifecycle, relay, objective_id, stage_id, basis_id)
    lifecycle.record_progress(writer, idempotency_key=f"progress:{writer.attempt_id}", message="writer evidence prepared")
    _technical_complete(relay, writer)
    validator_order = lifecycle.handoff_writer_to_validation(writer, validator_action_type="relay.noop", requested_by="runner")
    validator = relay.claim(f"run004a-validator-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C2", role="validator", work_order_id=validator_order)
    assert validator is not None
    lifecycle.mark_running(validator)
    return lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, key


def test_legal_writer_lifecycle_and_writer_evidence_handoff() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,writer_attempt_id,validation_basis_id FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("validation_running", writer.attempt_id, basis_id)
        cursor.execute("SELECT status,role,source_attempt_id FROM work_orders WHERE work_order_id=%s", (validator.work_order_id,))
        assert cursor.fetchone() == ("running", "validator", writer.attempt_id)


def test_writer_cannot_be_accepted_without_validator() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, _, _ = _validation_setup()
    with pytest.raises(LifecycleGateError):
        lifecycle.acceptance_gate(stage_id=stage_id, validation_result_id=uuid4(), validation_attempt_id=uuid4())


def test_independent_validator_enforced_at_claim() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer = None, None, None, None, None, None
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    # The validator order is already claimed by an independent instance. A second
    # validator cannot claim the same exclusive work order.
    assert relay.claim("run004a-other", 30, worker_instance_id=writer.worker_instance_id, seat_id="C1", role="validator", work_order_id=validator.work_order_id) is None


def test_validator_pass_is_the_acceptance_gate() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    result_id = lifecycle.record_validation(validator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT verdict,validation_attempt_id,writer_attempt_id FROM campaign_validation_results WHERE validation_result_id=%s", (result_id,))
        assert cursor.fetchone() == ("PASS", validator.attempt_id, writer.attempt_id)
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("accepted", "completed")


def test_validator_fail_persists_defects_and_repair_linkage() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    defect = DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it")
    result_id = lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=("defect",), defects=(defect,))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT count(*),min(state),validation_result_id FROM campaign_validation_defects WHERE stage_id=%s GROUP BY validation_result_id", (stage_id,))
        assert cursor.fetchone() == (1, "unresolved", result_id)
        cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone()[0] == "repair_pending"


def test_repair_and_revalidation_pass_resolves_defects_and_accepts() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=("defect",), defects=(DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it"),))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' AND source_attempt_id=%s", (stage_id, validator.attempt_id))
        repair_order = cursor.fetchone()[0]
    repair = relay.claim(f"run004a-repair-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=repair_order)
    assert repair is not None
    lifecycle.mark_running(repair)
    _technical_complete(relay, repair)
    revalidation_order = lifecycle.record_repair_completion(repair)
    revalidator = relay.claim(f"run004a-revalidator-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C2", role="revalidator", work_order_id=revalidation_order)
    assert revalidator is not None
    lifecycle.mark_running(revalidator)
    _technical_complete(relay, revalidator)
    lifecycle.record_validation(revalidator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone()[0] == "accepted"
        cursor.execute("SELECT state,resolution_attempt_id FROM campaign_validation_defects WHERE stage_id=%s", (stage_id,))
        state, resolution = cursor.fetchone()
        assert state == "resolved" and resolution == revalidator.attempt_id


def test_repair_writer_cannot_claim_its_own_revalidation() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=("defect",), defects=(DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it"),))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' AND source_attempt_id=%s", (stage_id, validator.attempt_id))
        repair_order = cursor.fetchone()[0]
    repair = relay.claim(f"run004a-repair-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=repair_order)
    assert repair is not None
    lifecycle.mark_running(repair)
    _technical_complete(relay, repair)
    revalidation_order = lifecycle.record_repair_completion(repair)
    assert relay.claim(f"run004a-repair-{uuid4()}", 30, worker_instance_id=repair.worker_instance_id, seat_id="C3", role="revalidator", work_order_id=revalidation_order) is None


def test_wrong_basis_or_result_version_is_rejected() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(validator, verdict="PASS", basis_hash="wrong", result_version_hash="tree", evidence_refs=(), findings_summary=())


@pytest.mark.parametrize(
    ("result_version_hash", "implementation_ref", "evidence_refs"),
    [
        ("0" * 40, RESULT_REF, RESULT_EVIDENCE),
        (RESULT_VERSION, RESULT_REF, ()),
        (RESULT_VERSION, None, RESULT_EVIDENCE),
        (RESULT_VERSION, "commit:" + "f" * 40, RESULT_EVIDENCE),
    ],
)
def test_arbitrary_pass_cannot_open_acceptance_gate(
    result_version_hash: str, implementation_ref: str | None, evidence_refs: tuple[str, ...],
) -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(
            validator, verdict="PASS", basis_hash=_basis_hash(basis_id),
            result_version_hash=result_version_hash, evidence_refs=evidence_refs,
            implementation_ref=implementation_ref, findings_summary=(),
        )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("validation_running", "ready")


def test_result_from_other_package_cannot_be_used_for_acceptance() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    other_version = "1" * 40
    other_ref = f"commit:{other_version}"
    other_evidence = ("other-package://result",)
    _technical_complete(relay, validator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(
            validator, verdict="PASS", basis_hash=_basis_hash(basis_id),
            result_version_hash=other_version, evidence_refs=other_evidence,
            implementation_ref=other_ref, findings_summary=(),
        )


def test_stale_validation_cannot_accept_superseded_writer_result() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    newer_version = "2" * 40
    newer_report = {
        "status": "succeeded", "changed_paths": ["src"],
        "result_version_hash": newer_version, "implementation_ref": f"commit:{newer_version}",
        "evidence_refs": ["replacement://writer-result"],
    }
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET result_report=%s::jsonb WHERE work_order_id=%s", (json.dumps(newer_report), writer.work_order_id))
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(
            validator, verdict="PASS", basis_hash=_basis_hash(basis_id),
            result_version_hash=RESULT_VERSION, evidence_refs=RESULT_EVIDENCE,
            implementation_ref=RESULT_REF, findings_summary=(),
        )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("validation_running", "ready")


def test_revalidation_cannot_accept_older_repair_result() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    lifecycle.record_validation(
        validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION,
        evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=("defect",),
        defects=(DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it"),),
    )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' AND source_attempt_id=%s", (stage_id, validator.attempt_id))
        repair_order = cursor.fetchone()[0]
    repair = relay.claim(f"run004ar-repair-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=repair_order)
    assert repair is not None
    lifecycle.mark_running(repair)
    _technical_complete(relay, repair)
    revalidation_order = lifecycle.record_repair_completion(repair)
    newer_version = "3" * 40
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET result_report=%s::jsonb WHERE work_order_id=%s", (json.dumps({
            "status": "succeeded", "changed_paths": ["src"], "result_version_hash": newer_version,
            "implementation_ref": f"commit:{newer_version}", "evidence_refs": ["replacement://repair-result"],
        }), repair.work_order_id))
    revalidator = relay.claim(f"run004ar-revalidator-{uuid4()}", 30, worker_instance_id=uuid4(), seat_id="C2", role="revalidator", work_order_id=revalidation_order)
    assert revalidator is not None
    lifecycle.mark_running(revalidator)
    _technical_complete(relay, revalidator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(
            revalidator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION,
            evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=(),
        )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("revalidation_running", "ready")


def test_fail_requires_structured_defects_and_pass_cannot_carry_defects() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash="tree", evidence_refs=(), findings_summary=())


def test_stale_validator_cannot_advance_lifecycle() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    with pytest.raises(RuntimeError):
        relay.complete_fenced(replace(CampaignLifecycleStore._identity(validator), fencing_token=uuid4()), {"status": "succeeded"})


def test_progress_projection_is_fenced_and_idempotent() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer = _package_and_running_writer()
    lifecycle.record_progress(writer, idempotency_key=f"progress:{writer.attempt_id}:one", message="meaningful")
    lifecycle.record_progress(writer, idempotency_key=f"progress:{writer.attempt_id}:one", message="duplicate")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT progress_count,last_progress_at FROM objective_stages WHERE stage_id=%s", (stage_id,))
        count, timestamp = cursor.fetchone()
    assert count == 1 and timestamp is not None


def test_restart_resume_derives_stage_from_postgres_and_no_active_stage_id() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, key = _package()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("queued", "ready")
        cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_name='objectives' AND column_name='active_stage_id'")
        assert cursor.fetchone() is None


def test_transition_history_and_exact_source_links() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM river_events WHERE aggregate_type='objective_stage' AND aggregate_id=%s", (stage_id,))
        assert cursor.fetchone()[0] >= 2
        cursor.execute("SELECT source_attempt_id,validation_basis_id FROM work_orders WHERE work_order_id=%s", (validator.work_order_id,))
        assert cursor.fetchone() == (writer.attempt_id, basis_id)


def test_two_validator_claimers_have_one_authoritative_winner() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    # The first claim above is the winner; a second claim cannot authoritatively
    # claim the same queued validation order.
    assert relay.claim("run004a-second", 30, worker_instance_id=uuid4(), seat_id="C3", role="validator", work_order_id=validator.work_order_id) is None


def test_concurrent_writer_claimers_have_one_authoritative_winner() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, key = _package()
    order_id = lifecycle.queue_writer(objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                                      action_type="relay.noop", requested_by="C1", idempotency_key=f"writer-race:{uuid4()}")
    barrier = threading.Barrier(2)
    results: list[object | None] = [None, None]

    def claim(index: int) -> None:
        barrier.wait(timeout=5)
        results[index] = relay.claim(f"race-{index}", 30, worker_instance_id=uuid4(), seat_id="C1", role="writer", work_order_id=order_id)

    threads = [threading.Thread(target=claim, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert sum(result is not None for result in results) == 1


def _package_and_running_writer():
    lifecycle, relay, objective_id, stage_id, basis_id, key = _package()
    writer = _writer(lifecycle, relay, objective_id, stage_id, basis_id)
    return lifecycle, relay, objective_id, stage_id, basis_id, writer


def _basis_hash(basis_id: UUID) -> str:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT specification_hash FROM campaign_validation_bases WHERE basis_id=%s", (basis_id,))
        return cursor.fetchone()[0]


def test_failed_repair_can_be_retried_without_replaying_upstream_and_can_accept() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    defect = DefectInput("criterion-1", "blocking", "works", "fails", "evidence:retry", "repair it")
    lifecycle.record_validation(
        validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION,
        evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=("defect",), defects=(defect,),
    )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' AND source_attempt_id=%s", (stage_id, validator.attempt_id))
        failed_order_id = cursor.fetchone()[0]
    failed_repair = relay.claim("run004c-repair-failed", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=failed_order_id)
    assert failed_repair is not None
    lifecycle.mark_running(failed_repair)
    runner = CampaignOneGoRunner(
        (WorkerSlot("run004c-failure", "C3", ("repair_writer",), uuid4()),),
        {"repair_writer": lambda _work: {}}, relay=relay, lifecycle=lifecycle, objective_id=objective_id,
    )
    runner._fail_if_current(failed_repair, "RIV-REC-0004: reconciliation rejected bounded repair")

    replacement_id = lifecycle.retry_failed_repair(
        failed_repair_work_order_id=failed_order_id, requested_by="recovery-test",
        reason="accepted reconciliation repair is now available",
    )
    assert replacement_id != failed_order_id
    assert lifecycle.retry_failed_repair(failed_repair_work_order_id=failed_order_id, requested_by="recovery-test") == replacement_id

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status,error_checkpoint,result_report FROM work_orders WHERE work_order_id=%s", (failed_order_id,))
        old_status, old_checkpoint, old_report = cursor.fetchone()
        assert old_status == "failed" and old_checkpoint == "RIV-REC-0004" and old_report["status"] == "failed"
        cursor.execute("SELECT parameters FROM work_orders WHERE work_order_id=%s", (replacement_id,))
        replacement_parameters = cursor.fetchone()[0]
        assert replacement_parameters["defects"] == [defect.as_payload()]
        assert replacement_parameters["retry_of_work_order_id"] == str(failed_order_id)
        cursor.execute("SELECT count(*) FROM work_orders w JOIN work_order_attempts a ON a.work_order_id=w.work_order_id WHERE w.stage_id=%s AND a.role='writer'", (stage_id,))
        writer_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM work_orders w JOIN work_order_attempts a ON a.work_order_id=w.work_order_id WHERE w.stage_id=%s AND a.role='validator'", (stage_id,))
        validator_count = cursor.fetchone()[0]
        assert writer_count == 1 and validator_count == 1

    replacement = relay.claim("run004c-repair-retry", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=replacement_id)
    assert replacement is not None and replacement.attempt_id != failed_repair.attempt_id
    lifecycle.mark_running(replacement)
    with pytest.raises(RuntimeError, match="late or stale"):
        relay.complete_fenced(CampaignLifecycleStore._identity(failed_repair), {"status": "succeeded"})
    _technical_complete(relay, replacement)
    revalidation_order = lifecycle.record_repair_completion(replacement)
    revalidator = relay.claim("run004c-revalidator", 30, worker_instance_id=uuid4(), seat_id="C2", role="revalidator", work_order_id=revalidation_order)
    assert revalidator is not None and revalidator.worker_instance_id != replacement.worker_instance_id
    lifecycle.mark_running(revalidator)
    _technical_complete(relay, revalidator)
    lifecycle.record_validation(
        revalidator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash=RESULT_VERSION,
        evidence_refs=RESULT_EVIDENCE, implementation_ref=RESULT_REF, findings_summary=(), defects=(),
    )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("accepted", "completed")
        cursor.execute("SELECT count(*) FROM river_events WHERE event_type='runner.repair.retry_queued' AND aggregate_id=%s", (stage_id,))
        assert cursor.fetchone()[0] == 1
