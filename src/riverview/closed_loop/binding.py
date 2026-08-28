"""Root-scoped governance binding for closed-loop execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from riverview.database import connect
from riverview.river import Classification, EventStore, RiverEvent


class BindingState(StrEnum):
    UNBOUND = "UNBOUND"
    PREPARED = "PREPARED"
    AWAITING_AUTHORITY = "AWAITING_AUTHORITY"
    BOUND = "BOUND"
    EXECUTABLE = "EXECUTABLE"
    RUNNING = "RUNNING"
    RESULT_AVAILABLE = "RESULT_AVAILABLE"
    COMPLETED = "COMPLETED"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class GovernanceBinding:
    root_task_id: UUID
    correlation_id: UUID
    specification_id: UUID | None = None
    engineering_intent_id: UUID | None = None
    objective_id: UUID | None = None
    stage_id: UUID | None = None
    authority_id: UUID | None = None
    work_order_id: UUID | None = None
    attempt_id: UUID | None = None
    lease_generation: int | None = None
    fencing_token: UUID | None = None
    worker_id: str | None = None
    resource_claim_id: UUID | None = None
    state: BindingState = BindingState.UNBOUND

    def validate(self) -> None:
        if self.state in {BindingState.BOUND, BindingState.EXECUTABLE, BindingState.RUNNING, BindingState.RESULT_AVAILABLE, BindingState.COMPLETED}:
            if any(value is None for value in (self.objective_id, self.stage_id, self.authority_id, self.work_order_id)):
                raise ValueError("RIV-LOOP-BIND-0001: executable binding lacks objective, stage, authority, or work order.")
        if self.state is BindingState.RUNNING and any(value is None for value in (self.attempt_id, self.lease_generation, self.fencing_token)):
            raise ValueError("RIV-LOOP-BIND-0002: running binding lacks exact attempt fence.")


class GovernanceBindingStore:
    def __init__(self, *, memory: bool = False) -> None:
        self._memory = memory
        self._items: dict[UUID, GovernanceBinding] = {}
        self._events: list[dict[str, Any]] = []

    @classmethod
    def memory(cls) -> "GovernanceBindingStore":
        return cls(memory=True)

    @staticmethod
    def _payload(binding: GovernanceBinding) -> dict[str, Any]:
        return {"root_task_id": str(binding.root_task_id), "correlation_id": str(binding.correlation_id), "binding_state": binding.state.value, "specification_id": str(binding.specification_id) if binding.specification_id else None, "engineering_intent_id": str(binding.engineering_intent_id) if binding.engineering_intent_id else None, "objective_id": str(binding.objective_id) if binding.objective_id else None, "stage_id": str(binding.stage_id) if binding.stage_id else None, "authority_id": str(binding.authority_id) if binding.authority_id else None, "work_order_id": str(binding.work_order_id) if binding.work_order_id else None, "attempt_id": str(binding.attempt_id) if binding.attempt_id else None, "resource_claim_id": str(binding.resource_claim_id) if binding.resource_claim_id else None}

    def save(self, binding: GovernanceBinding) -> GovernanceBinding:
        binding.validate()
        payload = self._payload(binding)
        if self._memory:
            self._items[binding.root_task_id] = binding
            self._events.append({"event_type": "root.binding.updated", **payload})
            return binding
        with connect() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO autonomous_governance_bindings(root_task_id,correlation_id,specification_id,engineering_intent_id,objective_id,stage_id,authority_id,work_order_id,attempt_id,lease_generation,fencing_token,worker_id,resource_claim_id,state) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(root_task_id) DO UPDATE SET correlation_id=EXCLUDED.correlation_id,specification_id=EXCLUDED.specification_id,engineering_intent_id=EXCLUDED.engineering_intent_id,objective_id=EXCLUDED.objective_id,stage_id=EXCLUDED.stage_id,authority_id=EXCLUDED.authority_id,work_order_id=EXCLUDED.work_order_id,attempt_id=EXCLUDED.attempt_id,lease_generation=EXCLUDED.lease_generation,fencing_token=EXCLUDED.fencing_token,worker_id=EXCLUDED.worker_id,resource_claim_id=EXCLUDED.resource_claim_id,state=EXCLUDED.state,updated_at=now()""", tuple(getattr(binding, key) for key in ("root_task_id", "correlation_id", "specification_id", "engineering_intent_id", "objective_id", "stage_id", "authority_id", "work_order_id", "attempt_id", "lease_generation", "fencing_token", "worker_id", "resource_claim_id", "state")))
        EventStore().append(RiverEvent(event_type="root.binding.updated", aggregate_type="autonomous_root_task", aggregate_id=binding.root_task_id, correlation_id=binding.correlation_id, idempotency_key=f"root.binding.updated:{binding.root_task_id}:{binding.state.value}:{binding.work_order_id or 'none'}", classification=Classification.INTERNAL, payload=payload))
        return binding

    def read(self, root_task_id: UUID) -> GovernanceBinding:
        if self._memory:
            return self._items.get(root_task_id, GovernanceBinding(root_task_id, UUID(int=0), state=BindingState.UNBOUND))
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT root_task_id,correlation_id,specification_id,engineering_intent_id,objective_id,stage_id,authority_id,work_order_id,attempt_id,lease_generation,fencing_token,worker_id,resource_claim_id,state FROM autonomous_governance_bindings WHERE root_task_id=%s", (root_task_id,))
            row = cur.fetchone()
            if not row: return GovernanceBinding(root_task_id, UUID(int=0), state=BindingState.UNBOUND)
            values = dict(zip(("root_task_id", "correlation_id", "specification_id", "engineering_intent_id", "objective_id", "stage_id", "authority_id", "work_order_id", "attempt_id", "lease_generation", "fencing_token", "worker_id", "resource_claim_id", "state"), row, strict=True))
            values["state"] = BindingState(values["state"])
            return GovernanceBinding(**values)

    def bind_work(self, root_task_id: UUID, correlation_id: UUID, work_order_id: UUID) -> GovernanceBinding:
        binding = self.read(root_task_id)
        if binding.correlation_id != UUID(int=0) and binding.correlation_id != correlation_id:
            raise ValueError("RIV-LOOP-BIND-0003: correlation does not match root binding.")
        if binding.work_order_id is not None and binding.work_order_id != work_order_id:
            raise ValueError("RIV-LOOP-BIND-0004: work order does not match root binding.")
        if binding.objective_id is None or binding.stage_id is None or binding.authority_id is None:
            raise PermissionError("RIV-LOOP-BIND-0005: objective, stage, and authority lineage are required.")
        values = {field: getattr(binding, field) for field in binding.__dataclass_fields__}
        values.update(correlation_id=correlation_id, work_order_id=work_order_id, state=BindingState.EXECUTABLE)
        return self.save(GovernanceBinding(**values))

    def require_executable(self, root_task_id: UUID) -> GovernanceBinding:
        binding = self.read(root_task_id)
        if binding.state is not BindingState.EXECUTABLE:
            raise PermissionError(f"RIV-LOOP-BIND-0006: root is not executable ({binding.state}).")
        binding.validate()
        return binding

    def joined_projection(self, root_task_id: UUID) -> dict[str, Any]:
        binding = self.read(root_task_id)
        if binding.correlation_id == UUID(int=0) and root_task_id not in self._items:
            raise LookupError(f"RIV-LOOP-BIND-0007: unknown root {root_task_id}")
        return {"root_task_id": str(binding.root_task_id), "correlation_id": str(binding.correlation_id), "binding_state": binding.state.value, "execution_eligible": binding.state is BindingState.EXECUTABLE, "specification_id": str(binding.specification_id) if binding.specification_id else None, "engineering_intent_id": str(binding.engineering_intent_id) if binding.engineering_intent_id else None, "objective_id": str(binding.objective_id) if binding.objective_id else None, "stage_id": str(binding.stage_id) if binding.stage_id else None, "authority_id": str(binding.authority_id) if binding.authority_id else None, "work_order_id": str(binding.work_order_id) if binding.work_order_id else None, "attempt_id": str(binding.attempt_id) if binding.attempt_id else None, "lease_generation": binding.lease_generation, "fencing_token": str(binding.fencing_token) if binding.fencing_token else None, "worker_id": binding.worker_id, "resource_claim_id": str(binding.resource_claim_id) if binding.resource_claim_id else None}
