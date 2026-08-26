"""Derived, secret-safe Hermes execution status projection.

This is an operator read model only.  It does not persist state and never
changes Campaign Runner, River, diagnostics, or acceptance state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from riverview.database import connect

_SECRET_KEYS = {
    "api_key", "apikey", "authorization", "password", "secret", "client_secret",
    "access_token", "refresh_token", "credential", "credentials",
}


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in _SECRET_KEYS or normalized.endswith("_secret") or normalized.endswith("_api_key")


def _redact(value: Any) -> tuple[Any, bool]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        redacted = False
        for key, item in value.items():
            if _is_secret_key(str(key)):
                result[key] = "[REDACTED]"
                redacted = True
            else:
                result[key], child_redacted = _redact(item)
                redacted = redacted or child_redacted
        return result, redacted
    if isinstance(value, list):
        values = []
        redacted = False
        for item in value:
            clean, child_redacted = _redact(item)
            values.append(clean)
            redacted = redacted or child_redacted
        return values, redacted
    if isinstance(value, tuple):
        clean, redacted = _redact(list(value))
        return tuple(clean), redacted
    return value, False


def project_hermes_execution(execution: Mapping[str, Any]) -> dict[str, Any]:
    """Project one execution envelope into a stable basic operator view."""
    if not isinstance(execution, Mapping) or not execution.get("execution_id"):
        raise ValueError("execution_id is required for Hermes projection")
    projected, secrets_redacted = _redact(dict(execution))
    projected.update({
        "execution_id": execution["execution_id"],
        "correlation_id": execution.get("correlation_id"),
        "resident": execution.get("resident_id"),
        "office": execution.get("office") or execution.get("role"),
        "campaign_package_id": execution.get("campaign_package_id") or execution.get("package_id"),
        "attempt_id": execution.get("attempt_id"),
        "hermes_profile": execution.get("hermes_profile") or execution.get("profile"),
        "worker": execution.get("worker_id") or execution.get("worker"),
        "provider": execution.get("provider_id"),
        "model": execution.get("model_ref") or execution.get("model"),
        "resource": execution.get("resource_class_ref") or execution.get("resource"),
        "state": execution.get("state") or execution.get("status"),
        "spawned_workers": list(execution.get("spawned_workers") or ()),
        "evidence_available": bool(execution.get("evidence_refs")),
        "failure": execution.get("failure"),
        "repair_state": execution.get("repair_state"),
        "canonical_reconciliation": execution.get("canonical_reconciliation", "unknown"),
        "acceptance_state": execution.get("acceptance_state", "not_accepted"),
        "secrets_redacted": secrets_redacted,
    })
    return projected


def project_campaign_runner_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project one PostgreSQL Campaign Runner row for a later Operator UI."""
    if not isinstance(record, Mapping) or not record.get("work_order_id"):
        raise ValueError("work_order_id is required for Campaign Runner projection")
    clean, _ = _redact(dict(record))
    status = str(record.get("status") or "unknown")
    runner_state = str(record.get("runner_state") or "unknown")
    acceptance_state = str(record.get("acceptance_state") or "not_accepted")
    clean.update({
        "source": "postgresql:campaign_runner",
        "work_order_id": record["work_order_id"],
        "package_id": record.get("package_id") or record.get("stage_id"),
        "objective_id": record.get("objective_id"),
        "stage_id": record.get("stage_id"),
        "role": record.get("role"),
        "status": status,
        "runner_state": runner_state,
        "attempt_id": record.get("attempt_id"),
        "lease_generation": record.get("lease_generation"),
        "fence_present": bool(record.get("fencing_token")),
        "worker_instance_id": record.get("worker_instance_id"),
        "seat_id": record.get("seat_id"),
        "hermes_profile": record.get("hermes_profile") or record.get("profile"),
        "provider": record.get("provider_id"),
        "model": record.get("model_ref") or record.get("model"),
        "resource": record.get("resource_class_ref") or record.get("resource"),
        "capacity": record.get("capacity") or {},
        "repair_generation": record.get("repair_generation", 0),
        "candidate_identity": record.get("candidate_identity"),
        "validation_state": record.get("validation_state") or runner_state,
        "candidate_technically_complete": status in {"succeeded", "completed"},
        "institutionally_accepted": acceptance_state in {"accepted", "completed"} or runner_state == "accepted",
        "acceptance_state": acceptance_state,
        "steward_attention_required": bool(record.get("attention_required")) or runner_state in {"blocked", "failed", "steward_checkpoint"},
    })
    clean.pop("fencing_token", None)
    return clean


def read_campaign_runner_snapshot(*, limit: int = 50) -> dict[str, Any]:
    """Read a bounded current Campaign Runner/Hermes snapshot from PostgreSQL."""
    bounded_limit = max(1, min(int(limit), 100))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT w.work_order_id,w.objective_id,w.stage_id,w.role,w.status,
                      w.active_attempt_id,w.lease_generation,w.fencing_token,
                      w.worker_instance_id,w.seat_id,w.result_report,
                      s.runner_state,s.repair_attempt_id,o.acceptance_state,
                      o.attention_required,
                      (SELECT count(*) FROM work_orders w2
                        WHERE w2.stage_id=w.stage_id
                          AND w2.role IN ('repair_writer','revalidator'))
                 FROM work_orders w
                 LEFT JOIN objective_stages s ON s.stage_id=w.stage_id
                 LEFT JOIN objectives o ON o.objective_id=w.objective_id
                WHERE w.status IN ('queued','claimed','running','succeeded','failed','timed_out')
                ORDER BY w.updated_at DESC
                LIMIT %s""",
            (bounded_limit,),
        )
        rows = cursor.fetchall()
    items = []
    for row in rows:
        report = row[10] if isinstance(row[10], dict) else {}
        items.append(project_campaign_runner_record({
            "work_order_id": str(row[0]),
            "objective_id": str(row[1]) if row[1] else None,
            "stage_id": str(row[2]) if row[2] else None,
            "role": row[3],
            "status": row[4],
            "attempt_id": str(row[5]) if row[5] else None,
            "lease_generation": row[6],
            "fencing_token": str(row[7]) if row[7] else None,
            "worker_instance_id": str(row[8]) if row[8] else None,
            "seat_id": row[9],
            "runner_state": row[11],
            "repair_generation": row[15],
            "acceptance_state": row[13],
            "attention_required": row[14],
            "provider_id": report.get("provider_id"),
            "model_ref": report.get("model_ref") or report.get("model"),
            "resource_class_ref": report.get("resource_class_ref") or report.get("resource"),
            "capacity": report.get("capacity") or {},
            "candidate_identity": report.get("candidate_identity") or report.get("result_version_hash"),
            "validation_state": row[11],
            "evidence_refs": report.get("evidence_refs") or [],
        }))
    return {"source": "postgresql:campaign_runner", "limit": bounded_limit, "items": items}


__all__ = ["project_campaign_runner_record", "project_hermes_execution", "read_campaign_runner_snapshot"]
