"""Persistent River-driven Continuous Motion Engine runtime.

The bounded ``ContinuousMomentumEngine`` remains the evaluator.  This module
owns the missing lifecycle: durable cursor recovery, PostgreSQL wakeup, and a
runtime-originated heartbeat projection.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from uuid import UUID, uuid4

import psycopg

from riverview.autonomy.control import ContinuousMomentumEngine, GraceMomentum
from riverview.database import connect
from riverview.database.connection import load_database_config
from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity
from riverview.grace.objectives import ObjectiveStore
from riverview.river import Classification, EventStore, RiverEvent

HEARTBEAT_FRESHNESS_SECONDS = 5.0
HEARTBEAT_INTERVAL_SECONDS = 1.0
CONSUMER_ID = "cme.primary"


class CMEV1ContinuationPolicy:
    """Bounded root-scoped handling of Hermes objective dispositions."""
    PARKED_OUTCOMES = frozenset({"OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION", "READY_FOR_STEWARD_REVIEW", "BLOCKED_REQUIRES_STEWARD", "STEWARD_DECISION_REQUIRED", "RETRYABLE_FAILURE", "TERMINAL_FAILURE"})

    def __init__(self, *, enqueue: Any, event_sink: Any | None = None, event_store: EventStore | None = None, max_no_progress: int = 3) -> None:
        if not callable(enqueue) or max_no_progress < 1:
            raise ValueError("RIV-GRC-0009: CME continuation policy bounds are invalid.")
        self.enqueue, self.event_sink, self.event_store = enqueue, event_sink, event_store
        self.max_no_progress = max_no_progress
        self._last_progress: dict[str, str] = {}
        self._no_progress: dict[str, int] = {}

    def _event(self, event_type: str, result: dict[str, Any]) -> None:
        if self.event_sink is not None:
            self.event_sink(event_type, result)
        if self.event_store is not None:
            self.event_store.append(RiverEvent(event_type=event_type, aggregate_type="autonomous_root_task", aggregate_id=UUID(str(result["root_task_id"])), correlation_id=UUID(str(result["correlation_id"])), idempotency_key=f"cme:{event_type}:{result['root_task_id']}:{result.get('result_id', 'none')}", classification=Classification.INTERNAL, payload={k: v for k, v in result.items() if k != "summary"}))

    def observe(self, result: dict[str, Any]) -> dict[str, Any]:
        required = ("root_task_id", "correlation_id", "request_id", "result_id", "semantic_outcome")
        if any(not result.get(key) for key in required):
            raise ValueError("RIV-GRC-0010: CME result correspondence is incomplete.")
        root, outcome = str(result["root_task_id"]), str(result["semantic_outcome"])
        progress = str(result.get("result_digest") or result.get("resulting_sha") or result["result_id"])
        if outcome == "CONTINUE":
            if self._last_progress.get(root) == progress:
                self._no_progress[root] = self._no_progress.get(root, 0) + 1
            else:
                self._last_progress[root], self._no_progress[root] = progress, 0
            if self._no_progress[root] >= self.max_no_progress:
                self._event("momentum.anomaly", result)
                return {"state": "MOMENTUM_ANOMALY", "root_task_id": root, "correlation_id": str(result["correlation_id"]), "reason": "CONTINUE produced no observable progress within the bounded V1 limit."}
            continuation = {"root_task_id": root, "correlation_id": str(result["correlation_id"]), "source_result_id": str(result["result_id"]), "source_request_id": str(result["request_id"])}
            self.enqueue(continuation)
            self._event("continuation.selected", continuation)
            self._event("continuation.queued", continuation)
            return {"state": "CONTINUATION_QUEUED", **continuation}
        if outcome not in self.PARKED_OUTCOMES:
            raise ValueError(f"RIV-GRC-0011: unsupported CME semantic outcome {outcome}.")
        self._event("root.parked", result)
        state = "AWAITING_ACCEPTANCE" if outcome in {"OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION"} else "PARKED"
        return {"state": state, "root_task_id": root, "correlation_id": str(result["correlation_id"]), "semantic_outcome": outcome}


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


class CMEStatusStore:
    """Authoritative, bounded CME runtime status and durable event cursor."""

    def ensure(self, runtime_instance_id: UUID) -> None:
        now = datetime.now(UTC)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT last_river_sequence_seen FROM cme_runtime_status WHERE status_id=true")
            existing = cursor.fetchone()
            if existing is None:
                cursor.execute("SELECT COALESCE(MAX(sequence_id),0) FROM river_events")
                initial_cursor = int(cursor.fetchone()[0])
            else:
                initial_cursor = int(existing[0])
            cursor.execute(
                """INSERT INTO cme_runtime_status(
                    status_id,consumer_id,runtime_instance_id,runtime_started_at,last_heartbeat_at,
                    current_state,current_state_since,last_river_sequence_seen,updated_at
                ) VALUES(true,%s,%s,%s,%s,'STARTING',%s,%s,%s)
                ON CONFLICT(status_id) DO UPDATE SET
                    consumer_id=EXCLUDED.consumer_id,runtime_instance_id=EXCLUDED.runtime_instance_id,
                    runtime_started_at=EXCLUDED.runtime_started_at,last_heartbeat_at=EXCLUDED.last_heartbeat_at,
                    current_state='STARTING',current_state_since=EXCLUDED.current_state_since,
                    waiting_reason=NULL,steward_attention_required=false,last_failure_code=NULL,
                    last_failure_at=NULL,updated_at=EXCLUDED.updated_at""",
                (CONSUMER_ID, runtime_instance_id, now, now, now, initial_cursor, now),
            )

    def update(self, **fields: Any) -> None:
        fields["last_heartbeat_at"] = datetime.now(UTC)
        fields["updated_at"] = datetime.now(UTC)
        assignments = ", ".join(f"{key}=%s" for key in fields)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(f"UPDATE cme_runtime_status SET {assignments} WHERE status_id=true", tuple(fields.values()))

    def heartbeat(self, state: str | None = None) -> None:
        fields: dict[str, Any] = {}
        if state:
            fields["current_state"] = state
            fields["current_state_since"] = datetime.now(UTC)
        self.update(**fields)

    def observe(self, event: dict[str, Any]) -> None:
        self.update(
            current_state="EVENT_OBSERVED",
            current_state_since=datetime.now(UTC),
            last_river_sequence_seen=event["sequence_id"],
            last_event_id=event["event_id"],
            last_event_type=event["event_type"],
            last_causation_id=event.get("causation_id"),
            last_event_observed_at=datetime.now(UTC),
            current_correlation_id=event.get("correlation_id"),
        )

    def cursor(self) -> int:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT last_river_sequence_seen FROM cme_runtime_status WHERE status_id=true")
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def read(self) -> dict[str, Any] | None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT runtime_instance_id,runtime_started_at,last_heartbeat_at,current_state,
                    current_state_since,last_river_sequence_seen,last_event_id,last_event_type,last_causation_id,
                    last_event_observed_at,current_objective_id,current_stage_id,current_correlation_id,
                    current_action,last_progress_at,last_successful_progress_summary,waiting_reason,
                    steward_attention_required,last_failure_code,last_failure_at,updated_at
                    FROM cme_runtime_status WHERE status_id=true"""
            )
            row = cursor.fetchone()
            if row is None:
                return None
            names = [item.name for item in cursor.description]
        result = dict(zip(names, row, strict=True))
        heartbeat = result["last_heartbeat_at"]
        age = max(0.0, (datetime.now(UTC) - heartbeat).total_seconds())
        result["heartbeat_age_seconds"] = round(age, 3)
        result["heartbeat_health"] = "HEALTHY" if age <= HEARTBEAT_FRESHNESS_SECONDS else "STALE"
        result["effective_state"] = result["current_state"] if age <= HEARTBEAT_FRESHNESS_SECONDS else "UNHEALTHY"
        return {key: _iso(value) if hasattr(value, "isoformat") else str(value) if isinstance(value, UUID) else value for key, value in result.items()}

    def event_rows(self, after_sequence: int, limit: int = 64) -> list[dict[str, Any]]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT sequence_id,event_id,event_type,aggregate_type,aggregate_id,
                    correlation_id,causation_id FROM river_events
                    WHERE sequence_id>%s ORDER BY sequence_id LIMIT %s""",
                (after_sequence, limit),
            )
            names = [item.name for item in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


class ContinuousMomentumRuntime:
    """Long-lived River consumer that keeps CME listening while work is idle."""

    def __init__(self, *, consumer_id: str = CONSUMER_ID, poll_seconds: float = 1.0) -> None:
        if poll_seconds <= 0:
            raise ValueError("RIV-GRC-0008: poll_seconds must be positive.")
        self.consumer_id = consumer_id
        self.poll_seconds = poll_seconds
        self.status = CMEStatusStore()
        self.engine = ContinuousMomentumEngine()
        self.diagnostics = DiagnosticStore()
        self.stop_event = threading.Event()
        self.runtime_instance_id = uuid4()
        self._listener: psycopg.Connection[Any] | None = None

    def _diagnose(self, failure_class: str, summary: str, detail: str | None = None) -> None:
        bounded = summary if not detail else f"{summary} Detail: {detail[:240]}"
        self.diagnostics.emit(DiagnosticEvent(
            checkpoint_id="RIV-GRC-0008", component="riverview.autonomy.runtime",
            operation="river_consumer", severity=Severity.ERROR, failure_class=failure_class,
            summary=bounded[:500], cookbook_entry="CB-RIV-GRC-0008",
            evidence_refs=("cme://runtime-status",), recovery_state=RecoveryState.UNVERIFIED,
        ))

    def _promoted_seed_validation(self, event: dict[str, Any]) -> None:
        if event["event_type"] != "steward.seed.promoted":
            return
        objective_id = event.get("aggregate_id")
        if not objective_id:
            return
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT objective_key FROM objectives WHERE objective_id=%s", (objective_id,))
            row = cursor.fetchone()
        if row is None:
            self._diagnose("objective-not-found", "Promoted seed event references no objective.")
            return
        ObjectiveStore().add_evidence(row[0], "validate", "seed:confirmed")

    def _process(self, event: dict[str, Any]) -> None:
        if event["event_type"] in {"execution.reconciled", "execution.reconciliation.recorded"}:
            try:
                outcome = GraceMomentum().reconcile_execution(UUID(str(event["aggregate_id"])))
                if outcome.get("progressed"):
                    self.status.update(
                        current_state="DISPATCHING", current_state_since=datetime.now(UTC),
                        current_action="reconciled execution", last_progress_at=datetime.now(UTC),
                        last_successful_progress_summary="Accepted bounded execution result and advanced objective.",
                        current_objective_id=None, current_stage_id=None,
                    )
                self.status.observe(event)
            except (RuntimeError, ValueError) as exc:
                self._diagnose("result-reconciliation-failure", "CME could not reconcile an execution result.", str(exc))
            return
        if event["event_type"] == "work.order.queued":
            # Queue creation is evidence of dispatch, not a new objective
            # frontier. Record it durably and return to listening; completion
            # or failure events are the reevaluation triggers.
            self.status.update(
                current_state="HEALTHY_LISTENING", current_state_since=datetime.now(UTC),
                current_action="declared approved action", last_river_sequence_seen=event["sequence_id"],
                last_successful_progress_summary="Bounded work order queued for Relay execution.",
            )
            self.status.observe(event)
            return
        self.status.update(current_state="EVALUATING", current_state_since=datetime.now(UTC))
        self._promoted_seed_validation(event)
        result = self.engine.cycle_until_quiescent(
            # Keep each event handling slice bounded. Independent objectives are
            # revisited by their own durable events or the next reconciliation
            # pass; one busy frontier must not starve the listener heartbeat.
            correlation_id=event.get("correlation_id"), max_cycles=1, limit=8,
            priority_objective_id=event.get("aggregate_id") if event.get("aggregate_type") == "objective" else None,
        )
        remaining = result.get("remaining_frontier", [])
        frontier_item = remaining[0] if remaining else None
        if result.get("redispatched", 0):
            self.status.update(
                current_state="DISPATCHING", current_state_since=datetime.now(UTC),
                current_action="declared approved action", last_progress_at=datetime.now(UTC),
                last_successful_progress_summary=f"Redispatched {result['redispatched']} bounded stage(s).",
                current_objective_id=frontier_item.get("objective_id") if frontier_item else event.get("aggregate_id"),
                current_stage_id=frontier_item.get("stage_id") if frontier_item else None,
            )
        elif remaining:
            self.status.update(
                current_state="WAITING_EXTERNAL", current_state_since=datetime.now(UTC),
                waiting_reason="No approved declared action or external evidence currently permits progression.",
                steward_attention_required=False,
                current_objective_id=frontier_item.get("objective_id") if frontier_item else event.get("aggregate_id"),
                current_stage_id=frontier_item.get("stage_id") if frontier_item else None,
            )
        else:
            self.status.update(
                current_state="HEALTHY_LISTENING", current_state_since=datetime.now(UTC),
                waiting_reason=None, current_action=None,
                last_progress_at=datetime.now(UTC),
                last_successful_progress_summary="Authoritative event evaluated; no eligible frontier remains.",
            )
        self.status.update(last_river_sequence_seen=event["sequence_id"])
        self.status.observe(event)

    def _recover_declared_actions(self) -> None:
        """Replay only already-bound actions after restart or cursor recovery.

        A River cursor is a delivery checkpoint, not proof that the evaluation
        and work formation side effects completed.  Re-querying the authoritative
        ready frontier closes that gap without granting any new authority: only
        stages with a persisted, typed declared action are considered, and Relay
        owns idempotent work-order formation.
        """
        try:
            frontier = self.engine.frontier(limit=64, declared_only=True)
            for item in frontier:
                if not isinstance(item.get("declared_action"), dict):
                    continue
                self.engine.cycle_until_quiescent(
                    limit=1,
                    max_cycles=1,
                    correlation_id=item.get("correlation_id"),
                    priority_objective_id=item["objective_id"],
                )
        except (RuntimeError, ValueError, TypeError) as exc:
            self._diagnose("declared-action-recovery-failure", "CME could not replay a persisted declared action.", str(exc))

    def _reconcile(self) -> None:
        while not self.stop_event.is_set():
            rows = self.status.event_rows(self.status.cursor())
            if not rows:
                return
            for event in rows:
                self._process(event)

    def _heartbeat_loop(self) -> None:
        """Keep liveness independent from one bounded evaluation slice."""
        while not self.stop_event.wait(HEARTBEAT_INTERVAL_SECONDS):
            try:
                self.status.heartbeat()
            except (RuntimeError, OSError, psycopg.Error) as exc:
                # A database outage is not healthy telemetry; the supervisor
                # observes the unchanged projection and owns recovery.
                self._diagnose("heartbeat-write-failure", "CME heartbeat update failed.", str(exc))

    def serve(self, ready: threading.Event | None = None) -> None:
        config = load_database_config()
        self.status.ensure(self.runtime_instance_id)
        self._recover_declared_actions()
        heartbeat_thread: threading.Thread | None = None
        failed = False
        try:
            with psycopg.connect(
                host=config.host, port=config.port, dbname=config.database,
                user=config.user, password=config.password, autocommit=True,
            ) as listener:
                self._listener = listener
                listener.execute("LISTEN riverview_river_events")
                self.status.heartbeat("HEALTHY_LISTENING")
                heartbeat_thread = threading.Thread(target=self._heartbeat_loop, name="cme-heartbeat", daemon=True)
                heartbeat_thread.start()
                self._reconcile()
                if ready:
                    ready.set()
                last_heartbeat = monotonic()
                while not self.stop_event.is_set():
                    next(listener.notifies(timeout=self.poll_seconds, stop_after=1), None)
                    # The notification is only a wake hint.  ``_process`` sets
                    # EVENT_OBSERVED after reading an actual durable row; do
                    # not repaint a settled state for duplicate/late hints.
                    self._reconcile()
                    if monotonic() - last_heartbeat >= self.poll_seconds:
                        self.status.heartbeat()
                        last_heartbeat = monotonic()
        except Exception as exc:  # runtime must expose failure, then remain stopped rather than lie
            if self.stop_event.is_set():
                return
            failed = True
            try:
                self.status.update(current_state="UNHEALTHY", current_state_since=datetime.now(UTC), last_failure_code="RIV-GRC-0008", last_failure_at=datetime.now(UTC))
                self._diagnose("consumer-runtime-failure", f"CME River consumer failed: {type(exc).__name__}.", str(exc))
            finally:
                if ready:
                    ready.set()
            raise
        finally:
            self.stop_event.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join(timeout=2.0)
            self._listener = None
            try:
                if not failed:
                    self.status.update(current_state="STOPPED", current_state_since=datetime.now(UTC))
            except (RuntimeError, OSError, psycopg.Error):
                self._diagnose("status-projection-failure", "CME stopped but its final status projection could not be written.")

    def stop(self) -> None:
        self.stop_event.set()
        if self._listener is not None:
            try:
                self._listener.close()
            except (OSError, psycopg.Error):
                return


def main() -> None:
    runtime = ContinuousMomentumRuntime()
    try:
        runtime.serve()
    except KeyboardInterrupt:
        runtime.stop()


if __name__ == "__main__":
    main()
