"""Riverview Comms5: self-describing, bounded, multi-client protocol.

Comms5 is a projection and governed ingress over the existing seed, River,
objective, CME, Relay, and execution stores.  It deliberately contains no
second workflow state machine and returns metadata rather than protected
payloads.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.autonomy.runtime import CMEStatusStore
from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore
from riverview.grace.seeds import MAX_SEED_BYTES, SeedLifecycleError, StewardSeedStore
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

CONTRACT_VERSION = "riverview-comms-contract:5.0"
MAX_SPECIFICATION_BYTES = 4 * 1024 * 1024
MAX_SUMMARY_BYTES = 2_000
MAX_PAGE_SIZE = 50
ALLOWED_CLASSIFICATIONS = frozenset(("river", "internal"))


class Comms5Error(ValueError):
    """Stable, bounded protocol error."""

    def __init__(self, code: str, reason: str, operation: str, *, retry_safe: bool, steward_action_required: bool = False, checkpoint: str | None = None) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.operation = operation
        self.retry_safe = retry_safe
        self.steward_action_required = steward_action_required
        self.checkpoint = checkpoint

    def as_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "reason": self.reason,
                "operation": self.operation,
                "retry_safe": self.retry_safe,
                "steward_action_required": self.steward_action_required,
                "checkpoint": self.checkpoint,
            }
        }


@dataclass(frozen=True)
class ClientContext:
    client_id: str
    client_type: str
    client_name: str
    client_version: str | None
    protocol_version: str
    authenticated_principal: str
    correlation_id: UUID
    classification: str

    @classmethod
    def from_request(cls, request: dict[str, Any]) -> ClientContext:
        required = ("client_id", "client_type", "client_name", "authenticated_principal")
        missing = [key for key in required if not str(request.get(key, "")).strip()]
        if missing:
            raise Comms5Error("RIV-COMMS5-0002", f"missing client fields: {missing}", "context", retry_safe=False, checkpoint="RIV-COMMS5-0002")
        classification = str(request.get("classification", "river"))
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise Comms5Error("RIV-SEC-0001", "classification is unsupported", "context", retry_safe=False, checkpoint="RIV-COMMS5-0010")
        try:
            correlation = UUID(str(request.get("correlation_id") or uuid4()))
        except ValueError as exc:
            raise Comms5Error("RIV-COMMS5-0002", "correlation_id is not a UUID", "context", retry_safe=False, checkpoint="RIV-COMMS5-0002") from exc
        protocol = str(request.get("protocol_version", CONTRACT_VERSION))
        if protocol != CONTRACT_VERSION:
            raise Comms5Error("RIV-COMMS5-0001", "unsupported protocol version", "context", retry_safe=False, checkpoint="RIV-COMMS5-0001")
        return cls(str(request["client_id"]), str(request["client_type"]), str(request["client_name"]), str(request.get("client_version")) if request.get("client_version") else None, protocol, str(request["authenticated_principal"]), correlation, classification)


def _json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _rows(cursor: Any) -> list[dict[str, Any]]:
    names = [column.name for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _row(cursor: Any) -> dict[str, Any] | None:
    value = cursor.fetchone()
    if value is None:
        return None
    names = [column.name for column in cursor.description]
    return dict(zip(names, value, strict=True))


def _bounded_limit(value: int) -> int:
    try:
        return max(1, min(int(value), MAX_PAGE_SIZE))
    except (TypeError, ValueError) as exc:
        raise Comms5Error("RIV-COMMS5-0003", "limit is invalid", "bounded_read", retry_safe=False) from exc


OPERATIONS: dict[str, dict[str, Any]] = {
    "contract_info": {"authorization": "READ_ONLY", "required": [], "description": "Return the Comms5 contract identity and compatibility policy."},
    "help": {"authorization": "READ_ONLY", "required": [], "description": "Return machine-readable discovery, limits, errors, examples, and do-not guidance."},
    "capabilities": {"authorization": "READ_ONLY", "required": [], "description": "List supported Comms5 operations and their authorization classes."},
    "describe_operation": {"authorization": "READ_ONLY", "required": ["operation"], "description": "Describe one public operation."},
    "examples": {"authorization": "READ_ONLY", "required": [], "description": "Return one bounded example for every public operation."},
    "submit_steward_seed": {"authorization": "DRAFT_WRITE", "required": ["seed_text", "idempotency_key", "client context"], "description": "Create a bounded draft only; no objective or work is created."},
    "store_specification": {"authorization": "DRAFT_WRITE", "required": ["content", "summary", "idempotency_key", "client context"], "description": "Store a bounded authoritative large specification reference."},
    "seed_status": {"authorization": "READ_ONLY", "required": ["seed_id"], "description": "Return bounded authoritative seed metadata."},
    "seed_lineage": {"authorization": "READ_ONLY", "required": ["seed_id"], "description": "Return bounded seed-to-result lineage across existing stores."},
    "objective_status": {"authorization": "READ_ONLY", "required": ["objective_id"], "description": "Return bounded objective, stages, CME, work, and checkpoint state."},
    "cme_status": {"authorization": "READ_ONLY", "required": [], "description": "Return the authoritative CME runtime projection."},
    "recent_steward_submissions": {"authorization": "READ_ONLY", "required": [], "description": "Rediscover recent bounded governed submissions."},
    "confirm_and_promote_seed": {"authorization": "STEWARD-GATED_WRITE", "required": ["seed_id", "explicit_steward_confirmation", "idempotency_key"], "description": "Use the canonical Steward promotion mechanism; AI identity is not authority. Cancelled and superseded seeds are ineligible."},
    "cancel_draft": {"authorization": "STEWARD-GATED_WRITE", "required": ["seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client context"], "description": "Append-only cancellation of a draft; it never cancels an objective or work order."},
    "supersede_seed": {"authorization": "STEWARD-GATED_WRITE", "required": ["seed_id", "replacement_seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client context"], "description": "Append an old-draft-to-new-draft replacement relation; active objectives cannot be superseded."},
}


class Comms5Service:
    """Bounded Comms5 protocol over Riverview's authoritative stores."""

    def contract_info(self) -> dict[str, Any]:
        return {"contract": CONTRACT_VERSION, "surface": "Riverview_Comms_5", "backward_compatible_with": "Riverview_Comms_4", "breaking_change_policy": "major version only", "authority": "projection_and_governed_ingress"}

    def capabilities(self) -> dict[str, Any]:
        return {"contract": CONTRACT_VERSION, "operations": [{"name": name, **meta} for name, meta in OPERATIONS.items()], "classifications": sorted(ALLOWED_CLASSIFICATIONS), "limits": {"max_seed_bytes": MAX_SEED_BYTES, "max_specification_bytes": MAX_SPECIFICATION_BYTES, "max_summary_bytes": MAX_SUMMARY_BYTES, "max_page_size": MAX_PAGE_SIZE}}

    def describe_operation(self, operation: str) -> dict[str, Any]:
        if operation not in OPERATIONS:
            raise Comms5Error("RIV-COMMS5-0004", "operation is unknown", "describe_operation", retry_safe=False, checkpoint="RIV-COMMS5-0001")
        return {"contract": CONTRACT_VERSION, "operation": operation, **OPERATIONS[operation], "response": "bounded JSON metadata; protected payloads are omitted", "idempotency": "mutations require a stable idempotency_key; retrying with the same key is safe, changing it blindly is not"}

    def examples(self) -> dict[str, Any]:
        context = {"client_id": "example-agent", "client_type": "local_ai", "client_name": "Example Agent", "client_version": "1.0", "protocol_version": CONTRACT_VERSION, "authenticated_principal": "authorized-ai-session", "correlation_id": "00000000-0000-4000-8000-000000000001", "classification": "river"}
        draft = {**context, "seed_text": "Bounded intent; see specification_id for full acceptance criteria.", "idempotency_key": "example-seed-1"}
        return {"submit_steward_seed": draft, "store_specification": {**context, "summary": "Bounded specification summary", "content": "Full authoritative specification content", "idempotency_key": "example-spec-1"}, "seed_status": {"seed_id": "00000000-0000-4000-8000-000000000002"}, "seed_lineage": {"seed_id": "00000000-0000-4000-8000-000000000002"}, "objective_status": {"objective_id": "00000000-0000-4000-8000-000000000003"}, "confirm_and_promote_seed": {**context, "seed_id": "00000000-0000-4000-8000-000000000002", "idempotency_key": "example-promotion-1", "explicit_steward_confirmation": True, "authenticated_principal": "steward"}, "cancel_draft": {**context, "seed_id": "00000000-0000-4000-8000-000000000002", "reason": "Replaced by a reviewed draft", "idempotency_key": "example-cancel-1", "explicit_steward_confirmation": True, "authenticated_principal": "steward"}, "supersede_seed": {**context, "seed_id": "00000000-0000-4000-8000-000000000002", "replacement_seed_id": "00000000-0000-4000-8000-000000000004", "reason": "Reviewed replacement draft", "idempotency_key": "example-supersede-1", "explicit_steward_confirmation": True, "authenticated_principal": "steward"}, "steward_attention": {"operation": "seed_lineage", "field": "steward_attention_required", "meaning": "true means do not self-promote or bypass the checkpoint"}}

    def help(self) -> dict[str, Any]:
        return {"contract": self.contract_info(), "capabilities": self.capabilities(), "operations": {name: self.describe_operation(name) for name in OPERATIONS}, "examples": self.examples(), "errors": ["RIV-COMMS5-0001", "RIV-COMMS5-0002", "RIV-COMMS5-0003", "RIV-COMMS5-0004", "RIV-COMMS5-0005", "RIV-COMMS5-0006", "RIV-COMMS5-0007", "RIV-COMMS5-0009", "RIV-COMMS5-0014", "RIV-COMMS5-0015", "RIV-SEC-0001"], "do_not": ["directly mutate PostgreSQL", "bypass Steward confirmation", "treat client identity as authority", "invent objective/work state", "retry mutations with a new idempotency key blindly", "expose protected payloads", "treat provider completion as global completion", "cancel objectives or work through draft lifecycle operations", "modify Comms/MCP authorization through ordinary ingress"]}

    def store_specification(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = "store_specification"
        context = ClientContext.from_request(request)
        content = request.get("content")
        summary = str(request.get("summary", "")).strip()
        key = str(request.get("idempotency_key", "")).strip()
        if not isinstance(content, str) or not content.strip() or len(content.encode()) > MAX_SPECIFICATION_BYTES or not summary or len(summary.encode()) > MAX_SUMMARY_BYTES or not key:
            raise Comms5Error("RIV-COMMS5-0005", "specification is missing or exceeds its bounded limit", operation, retry_safe=False, checkpoint="RIV-COMMS5-0007")
        digest = hashlib.sha256(content.encode()).hexdigest()
        specification_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO comms5_specifications(specification_id,version,summary,content,content_bytes,content_sha256,classification,lifecycle_state,client_id,client_type,client_name,client_version,protocol_version,authenticated_principal,correlation_id,idempotency_key) VALUES(%s,1,%s,%s,%s,%s,%s,'stored',%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(idempotency_key) DO NOTHING""", (specification_id, summary, content, len(content.encode()), digest, context.classification, context.client_id, context.client_type, context.client_name, context.client_version, context.protocol_version, context.authenticated_principal, context.correlation_id, key))
            cursor.execute("SELECT specification_id,version,content_sha256,classification,lifecycle_state,created_at FROM comms5_specifications WHERE idempotency_key=%s", (key,))
            row = _row(cursor)
        if row is None:
            raise Comms5Error("RIV-COMMS5-0007", "specification could not be stored", operation, retry_safe=True, checkpoint="RIV-COMMS5-0007")
        if row["content_sha256"] != digest or row["classification"] != context.classification:
            raise Comms5Error("RIV-COMMS5-0015", "idempotency key conflicts with an existing specification", operation, retry_safe=False, checkpoint="RIV-COMMS5-0015")
        EventStore().append(RiverEvent(event_type="comms5.specification.stored", aggregate_type="specification", aggregate_id=row["specification_id"], correlation_id=context.correlation_id, idempotency_key=f"comms5.specification.stored:{row['specification_id']}", classification=Classification(context.classification), payload={"specification_id": str(row["specification_id"]), "version": row["version"], "content_sha256": row["content_sha256"], "client_id": context.client_id}))
        return {"specification": _json(row), "reference": f"riverview://specification/{row['specification_id']}@v{row['version']}", "content_returned": False}

    def submit_steward_seed(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = "submit_steward_seed"
        context = ClientContext.from_request(request)
        text = str(request.get("seed_text", ""))
        key = str(request.get("idempotency_key", "")).strip()
        if not key or not text.strip() or len(text.encode()) > MAX_SEED_BYTES:
            raise Comms5Error("RIV-COMMS5-0005", "seed_text is empty, missing idempotency_key, or exceeds the bounded seed limit", operation, retry_safe=False, checkpoint="RIV-COMMS5-0008")
        specification_id = request.get("specification_id")
        spec_version = None
        parsed_spec = None
        if specification_id:
            try:
                parsed_spec = UUID(str(specification_id))
            except ValueError as exc:
                raise Comms5Error("RIV-COMMS5-0006", "specification reference is invalid", operation, retry_safe=False, checkpoint="RIV-COMMS5-0007") from exc
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT version,classification,lifecycle_state FROM comms5_specifications WHERE specification_id=%s", (parsed_spec,))
                spec = cursor.fetchone()
            if spec is None or spec[1] != context.classification or spec[2] not in {"stored", "referenced"}:
                raise Comms5Error("RIV-COMMS5-0006", "specification reference is unavailable for this classification", operation, retry_safe=False, checkpoint="RIV-COMMS5-0007")
            spec_version = spec[0]
        try:
            seed_id = StewardSeedStore().submit(text, correlation_id=context.correlation_id, idempotency_key=key, causation_id=UUID(str(request["causation_id"])) if request.get("causation_id") else None, classification=context.classification, client_id=context.client_id, client_type=context.client_type, client_name=context.client_name, client_version=context.client_version, protocol_version=context.protocol_version, authenticated_principal=context.authenticated_principal, specification_id=parsed_spec, specification_version=spec_version)
        except SeedLifecycleError as exc:
            raise Comms5Error(exc.code, exc.reason, operation, retry_safe=False, checkpoint="RIV-COMMS5-0015") from exc
        if parsed_spec:
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("UPDATE comms5_specifications SET lifecycle_state='referenced',updated_at=now() WHERE specification_id=%s", (parsed_spec,))
        return {"seed_id": str(seed_id), "status": "draft", "objective_id": None, "steward_action_required": True, "specification_id": str(parsed_spec) if parsed_spec else None, "correlation_id": str(context.correlation_id), "client_id": context.client_id}

    def seed_status(self, seed_id: str) -> dict[str, Any]:
        try: seed_uuid = UUID(seed_id)
        except ValueError as exc: raise Comms5Error("RIV-COMMS5-0006", "seed_id is invalid", "seed_status", retry_safe=False, checkpoint="RIV-COMMS5-0008") from exc
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT seed_id,correlation_id,classification,status,objective_id,evidence_refs,idempotency_key,created_at,confirmed_at,promoted_at,client_id,client_type,client_name,client_version,protocol_version,specification_id,specification_version,cancelled_at,cancellation_reason,cancelled_by,superseded_at,replacement_seed_id,supersedes_seed_id FROM steward_seed_drafts WHERE seed_id=%s", (seed_uuid,))
            row = _row(cursor)
        if row is None: raise Comms5Error("RIV-COMMS5-0006", "seed was not found", "seed_status", retry_safe=False, checkpoint="RIV-COMMS5-0008")
        row["steward_action_required"] = row["status"] == "draft"
        row["payload_returned"] = False
        return _json(row)

    def _lineage(self, seed_uuid: UUID) -> dict[str, Any]:
        seed = self.seed_status(str(seed_uuid))
        objective_id = seed.get("objective_id")
        objective = None
        evaluations: list[dict[str, Any]] = []
        checkpoints: list[dict[str, Any]] = []
        work: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT lifecycle_event_id,transition,replacement_seed_id,actor,reason,classification,correlation_id,created_at FROM steward_seed_lifecycle_events WHERE seed_id=%s ORDER BY created_at", (seed_uuid,))
            lifecycle_events = _rows(cursor)
        if objective_id:
            objective = _json(ObjectiveStore().load(f"seed:{seed_uuid}"))
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT evaluation_id,decision,reason,next_action,created_at FROM grace_transition_evaluations WHERE objective_id=%s ORDER BY created_at DESC LIMIT 10", (UUID(str(objective_id)),)); evaluations = _rows(cursor)
                cursor.execute("SELECT checkpoint_code,state,reason,required_action,created_at FROM grace_checkpoints WHERE subject_id=%s ORDER BY created_at DESC LIMIT 10", (UUID(str(objective_id)),)); checkpoints = _rows(cursor)
                cursor.execute("SELECT work_order_id,action_type,status,requested_by,correlation_id,error_checkpoint,created_at,started_at,finished_at FROM work_orders WHERE correlation_id=%s ORDER BY created_at LIMIT 20", (objective["correlation_id"],)); work = _rows(cursor)
            events = _json(EventStore().read_aggregate("objective", UUID(str(objective_id))))[-20:]
        cme = CMEStatusStore().read()
        return {"seed": seed, "promotion": {"status": "not_created" if not objective_id else "promoted", "objective_id": objective_id}, "lifecycle_events": _json(lifecycle_events), "objective": objective or {"status": "not_created"}, "grace_evaluations": _json(evaluations), "checkpoints": _json(checkpoints), "work_orders": _json(work), "river_events": events, "cme": cme or {"status": "not_observed"}, "steward_attention_required": bool(seed["steward_action_required"] or checkpoints), "protected_payloads_returned": False}

    def seed_lineage(self, seed_id: str) -> dict[str, Any]:
        try: seed_uuid = UUID(seed_id)
        except ValueError as exc: raise Comms5Error("RIV-COMMS5-0006", "seed_id is invalid", "seed_lineage", retry_safe=False, checkpoint="RIV-COMMS5-0008") from exc
        return _json(self._lineage(seed_uuid))

    def objective_status(self, objective_id: str) -> dict[str, Any]:
        try: objective_uuid = UUID(objective_id)
        except ValueError as exc: raise Comms5Error("RIV-COMMS5-0006", "objective_id is invalid", "objective_status", retry_safe=False) from exc
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT objective_key FROM objectives WHERE objective_id=%s", (objective_uuid,)); row = cursor.fetchone()
        if row is None: raise Comms5Error("RIV-COMMS5-0006", "objective was not found", "objective_status", retry_safe=False)
        status = _json(ObjectiveStore().load(row[0]))
        cme = CMEStatusStore().read()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT work_order_id,action_type,status,correlation_id,error_checkpoint,created_at,started_at,finished_at FROM work_orders WHERE correlation_id=%s ORDER BY created_at LIMIT 20", (status["correlation_id"],)); work = _rows(cursor)
        return {"objective": status, "cme": cme, "work_orders": _json(work), "steward_attention_required": any(stage.get("steward_checkpoint") for stage in status["stages"])}

    def cme_status(self) -> dict[str, Any] | None:
        return CMEStatusStore().read()

    def recent_steward_submissions(self, limit: int = 20) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT seed_id,created_at,client_id,client_type,client_name,status,objective_id,correlation_id,replacement_seed_id,supersedes_seed_id,cancelled_at,superseded_at FROM steward_seed_drafts ORDER BY created_at DESC LIMIT %s", (_bounded_limit(limit),)); rows = _rows(cursor)
        for row in rows: row["steward_action_required"] = row["status"] == "draft"
        return {"items": _json(rows), "limit": _bounded_limit(limit), "payloads_returned": False}

    def _append_lifecycle_event(self, result: dict[str, Any], event_type: str) -> None:
        EventStore().append(RiverEvent(event_type=event_type, aggregate_type="steward_seed", aggregate_id=UUID(str(result["seed_id"])), correlation_id=UUID(str(result["correlation_id"])), idempotency_key=f"steward.seed.lifecycle:{result['lifecycle_event_id']}", classification=Classification(str(result["classification"])), payload={key: str(value) for key, value in result.items() if key in {"seed_id", "replacement_seed_id", "transition", "actor", "reason"} and value is not None}))

    def _lifecycle_context(self, request: dict[str, Any], operation: str) -> ClientContext:
        try:
            return ClientContext.from_request(request)
        except Comms5Error as exc:
            raise Comms5Error(exc.code, exc.reason, operation, retry_safe=False, steward_action_required=True, checkpoint=exc.checkpoint) from exc

    def cancel_draft(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = "cancel_draft"
        context = self._lifecycle_context(request, operation)
        if request.get("explicit_steward_confirmation") is not True:
            raise Comms5Error("RIV-COMMS5-0009", "explicit Steward authorization is required", operation, retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0009")
        try:
            seed_id = UUID(str(request["seed_id"]))
        except (KeyError, ValueError) as exc:
            raise Comms5Error("RIV-COMMS5-0006", "seed_id is invalid", operation, retry_safe=False, checkpoint="RIV-COMMS5-0014") from exc
        key = str(request.get("idempotency_key", "")).strip()
        if not key:
            raise Comms5Error("RIV-COMMS5-0003", "idempotency_key is required", operation, retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0015")
        try:
            result = StewardSeedStore().cancel_draft(seed_id, actor=context.authenticated_principal, explicit_steward_confirmation=True, reason=str(request.get("reason", "")), classification=context.classification, correlation_id=context.correlation_id, idempotency_key=key)
        except SeedLifecycleError as exc:
            detail = f"; objective_id={exc.objective_id}" if exc.objective_id else ""
            raise Comms5Error(exc.code, exc.reason + detail, operation, retry_safe=exc.code == "RIV-COMMS5-0015", steward_action_required=exc.code == "RIV-COMMS5-0009", checkpoint="RIV-COMMS5-0014") from exc
        self._append_lifecycle_event(result, "steward.seed.cancelled")
        return _json({**result, "status": "cancelled", "objective_id": None, "steward_action_required": False})

    def supersede_seed(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = "supersede_seed"
        context = self._lifecycle_context(request, operation)
        if request.get("explicit_steward_confirmation") is not True:
            raise Comms5Error("RIV-COMMS5-0009", "explicit Steward authorization is required", operation, retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0009")
        try:
            seed_id = UUID(str(request["seed_id"]))
            replacement_seed_id = UUID(str(request["replacement_seed_id"]))
        except (KeyError, ValueError) as exc:
            raise Comms5Error("RIV-COMMS5-0006", "seed_id or replacement_seed_id is invalid", operation, retry_safe=False, checkpoint="RIV-COMMS5-0014") from exc
        key = str(request.get("idempotency_key", "")).strip()
        if not key:
            raise Comms5Error("RIV-COMMS5-0003", "idempotency_key is required", operation, retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0015")
        try:
            result = StewardSeedStore().supersede_seed(seed_id, replacement_seed_id, actor=context.authenticated_principal, explicit_steward_confirmation=True, reason=str(request.get("reason", "")), classification=context.classification, correlation_id=context.correlation_id, idempotency_key=key)
        except SeedLifecycleError as exc:
            detail = f"; objective_id={exc.objective_id}" if exc.objective_id else ""
            raise Comms5Error(exc.code, exc.reason + detail, operation, retry_safe=exc.code == "RIV-COMMS5-0015", steward_action_required=exc.code == "RIV-COMMS5-0009", checkpoint="RIV-COMMS5-0014") from exc
        self._append_lifecycle_event(result, "steward.seed.superseded")
        return _json({**result, "status": "superseded", "steward_action_required": False})

    def confirm_and_promote_seed(self, request: dict[str, Any]) -> dict[str, Any]:
        if not str(request.get("idempotency_key", "")).strip():
            raise Comms5Error("RIV-COMMS5-0003", "idempotency_key is required for promotion retry safety", "confirm_and_promote_seed", retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0009")
        if request.get("authenticated_principal") != "steward" or request.get("explicit_steward_confirmation") is not True:
            raise Comms5Error("RIV-COMMS5-0009", "explicit Steward authorization is required; client identity is not authority", "confirm_and_promote_seed", retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0009")
        try: seed_id = UUID(str(request["seed_id"]))
        except (KeyError, ValueError) as exc: raise Comms5Error("RIV-COMMS5-0006", "seed_id is invalid", "confirm_and_promote_seed", retry_safe=False) from exc
        try:
            objective_id = StewardSeedStore().confirm_and_promote(seed_id, confirmer="steward", idempotency_key=str(request["idempotency_key"]).strip())
        except SeedLifecycleError as exc:
            detail = f"; objective_id={exc.objective_id}" if exc.objective_id else ""
            raise Comms5Error(exc.code, exc.reason + detail, "confirm_and_promote_seed", retry_safe=False, steward_action_required=True, checkpoint="RIV-COMMS5-0014") from exc
        return {"seed_id": str(seed_id), "objective_id": str(objective_id), "status": "promoted", "canonical_store": "StewardSeedStore.confirm_and_promote"}
