"""Root-scoped governance binding for closed-loop execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from riverview.database import connect


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
            required = (self.objective_id, self.stage_id, self.authority_id, self.work_order_id)
            if any(value is None for value in required):
                raise ValueError("RIV-LOOP-BIND-0001: executable binding lacks objective, stage, authority, or work order.")
        if self.state is BindingState.RUNNING and any(value is None for value in (self.attempt_id, self.lease_generation, self.fencing_token)):
            raise ValueError("RIV-LOOP-BIND-0002: running binding lacks exact attempt fence.")


class GovernanceBindingStore:
    def __init__(self, *, memory: bool = False) -> None:
        self._memory = memory
        self._items: dict[UUID, GovernanceBinding] = {}

    @classmethod
    def memory(cls) -> "GovernanceBindingStore":
        return cls(memory=True)

    def save(self, binding: GovernanceBinding) -> GovernanceBinding:
        binding.validate()
        if self._memory:
            self._items[binding.root_task_id] = binding
            return binding
        with connect() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO autonomous_governance_bindings(root_task_id,correlation_id,specification_id,engineering_intent_id,objective_id,stage_id,authority_id,work_order_id,attempt_id,lease_generation,fencing_token,worker_id,resource_claim_id,state) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(root_task_id) DO UPDATE SET correlation_id=EXCLUDED.correlation_id,specification_id=EXCLUDED.specification_id,engineering_intent_id=EXCLUDED.engineering_intent_id,objective_id=EXCLUDED.objective_id,stage_id=EXCLUDED.stage_id,authority_id=EXCLUDED.authority_id,work_order_id=EXCLUDED.work_order_id,attempt_id=EXCLUDED.attempt_id,lease_generation=EXCLUDED.lease_generation,fencing_token=EXCLUDED.fencing_token,worker_id=EXCLUDED.worker_id,resource_claim_id=EXCLUDED.resource_claim_id,state=EXCLUDED.state,updated_at=now()""", tuple(getattr(binding, key) for key in ("root_task_id","correlation_id","specification_id","engineering_intent_id","objective_id","stage_id","authority_id","work_order_id","attempt_id","lease_generation","fencing_token","worker_id","resource_claim_id","state")))
        return binding

    def read(self, root_task_id: UUID) -> GovernanceBinding:
        if self._memory:
            return self._items.get(root_task_id, GovernanceBinding(root_task_id, UUID(int=0), state=BindingState.UNBOUND))
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT root_task_id,correlation_id,specification_id,engineering_intent_id,objective_id,stage_id,authority_id,work_order_id,attempt_id,lease_generation,fencing_token,worker_id,resource_claim_id,state FROM autonomous_governance_bindings WHERE root_task_id=%s", (root_task_id,)); row = cur.fetchone()
            if not row: return GovernanceBinding(root_task_id, UUID(int=0), state=BindingState.UNBOUND)
            values = dict(zip(("root_task_id","correlation_id","specification_id","engineering_intent_id","objective_id","stage_id","authority_id","work_order_id","attempt_id","lease_generation","fencing_token","worker_id","resource_claim_id","state"), row, strict=True))
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
        updated = GovernanceBinding(**{**{field: getattr(binding, field) for field in binding.__dataclass_fields__}, "correlation_id": correlation_id, "work_order_id": work_order_id, "state": BindingState.EXECUTABLE})
        return self.save(updated)

    def require_executable(self, root_task_id: UUID) -> GovernanceBinding:
        binding = self.read(root_task_id)
        if binding.state is not BindingState.EXECUTABLE:
            raise PermissionError(f"RIV-LOOP-BIND-0006: root is not executable ({binding.state}).")
        binding.validate()
        return binding
