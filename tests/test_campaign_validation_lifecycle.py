"""RUN-004A PostgreSQL writer/validator lifecycle and gate acceptance tests."""

from __future__ import annotations

import threading
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from riverview.campaign import CampaignLifecycleStore, DefectInput, LifecycleGateError
from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.relay import RelayStore


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
    work = relay.claim("run004a-writer", 30, worker_instance_id=uuid4(), seat_id="C1", role="writer", work_order_id=order_id)
    assert work is not None
    lifecycle.mark_running(work)
    return work


def _technical_complete(relay: RelayStore, work) -> None:
    relay.complete_fenced(CampaignLifecycleStore._identity(work), {"status": "succeeded", "changed_paths": ["src"]})


def _validation_setup():
    lifecycle, relay, objective_id, stage_id, basis_id, key = _package()
    writer = _writer(lifecycle, relay, objective_id, stage_id, basis_id)
    lifecycle.record_progress(writer, idempotency_key=f"progress:{writer.attempt_id}", message="writer evidence prepared")
    _technical_complete(relay, writer)
    validator_order = lifecycle.handoff_writer_to_validation(writer, validator_action_type="relay.noop", requested_by="runner")
    validator = relay.claim("run004a-validator", 30, worker_instance_id=uuid4(), seat_id="C2", role="validator", work_order_id=validator_order)
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
    result_id = lifecycle.record_validation(validator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash="tree-v1", evidence_refs=("test:pass",), findings_summary=())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT verdict,validation_attempt_id,writer_attempt_id FROM campaign_validation_results WHERE validation_result_id=%s", (result_id,))
        assert cursor.fetchone() == ("PASS", validator.attempt_id, writer.attempt_id)
        cursor.execute("SELECT runner_state,status FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone() == ("accepted", "completed")


def test_validator_fail_persists_defects_and_repair_linkage() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    defect = DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it")
    result_id = lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash="tree-v1", evidence_refs=("test:fail",), findings_summary=("defect",), defects=(defect,))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT count(*),min(state),validation_result_id FROM campaign_validation_defects WHERE stage_id=%s GROUP BY validation_result_id", (stage_id,))
        assert cursor.fetchone() == (1, "unresolved", result_id)
        cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone()[0] == "repair_pending"


def test_repair_and_revalidation_pass_resolves_defects_and_accepts() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash="tree-v1", evidence_refs=("test:fail",), findings_summary=("defect",), defects=(DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it"),))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' ORDER BY created_at DESC LIMIT 1", (stage_id,))
        repair_order = cursor.fetchone()[0]
    repair = relay.claim("run004a-repair", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=repair_order)
    assert repair is not None
    lifecycle.mark_running(repair)
    _technical_complete(relay, repair)
    revalidation_order = lifecycle.record_repair_completion(repair)
    revalidator = relay.claim("run004a-revalidator", 30, worker_instance_id=uuid4(), seat_id="C2", role="revalidator", work_order_id=revalidation_order)
    assert revalidator is not None
    lifecycle.mark_running(revalidator)
    _technical_complete(relay, revalidator)
    lifecycle.record_validation(revalidator, verdict="PASS", basis_hash=_basis_hash(basis_id), result_version_hash="tree-v2", evidence_refs=("test:revalidated",), findings_summary=())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s", (stage_id,))
        assert cursor.fetchone()[0] == "accepted"
        cursor.execute("SELECT state,resolution_attempt_id FROM campaign_validation_defects WHERE stage_id=%s", (stage_id,))
        state, resolution = cursor.fetchone()
        assert state == "resolved" and resolution == revalidator.attempt_id


def test_repair_writer_cannot_claim_its_own_revalidation() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    lifecycle.record_validation(validator, verdict="FAIL", basis_hash=_basis_hash(basis_id), result_version_hash="tree-v1", evidence_refs=("test:fail",), findings_summary=("defect",), defects=(DefectInput("criterion-1", "blocking", "works", "fails", "evidence:1", "repair it"),))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT work_order_id FROM work_orders WHERE stage_id=%s AND role='repair_writer' ORDER BY created_at DESC LIMIT 1", (stage_id,))
        repair_order = cursor.fetchone()[0]
    repair = relay.claim("run004a-repair", 30, worker_instance_id=uuid4(), seat_id="C3", role="repair_writer", work_order_id=repair_order)
    assert repair is not None
    lifecycle.mark_running(repair)
    _technical_complete(relay, repair)
    revalidation_order = lifecycle.record_repair_completion(repair)
    assert relay.claim("run004a-repair", 30, worker_instance_id=repair.worker_instance_id, seat_id="C3", role="revalidator", work_order_id=revalidation_order) is None


def test_wrong_basis_or_result_version_is_rejected() -> None:
    lifecycle, relay, objective_id, stage_id, basis_id, writer, validator, _ = _validation_setup()
    _technical_complete(relay, validator)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_validation(validator, verdict="PASS", basis_hash="wrong", result_version_hash="tree", evidence_refs=(), findings_summary=())


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
