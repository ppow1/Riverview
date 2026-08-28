"""First bounded Grace -> Hermes -> result -> Grace tracer spine."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.river import Classification, EventStore, RiverEvent

SCHEMA_VERSION = "rv-loop-tracer-v1"
SUMMARY = "Bounded Hermes tracer completed."
CHECKPOINTS = (
    ("request-formed", "Request formed", "local request artifact exists"),
    ("hermes-execution", "Hermes execution", "one claimed run returns"),
    ("result-returned", "Result returned to Grace", "authoritative result exists"),
    ("result-consumed", "Result acknowledged/consumed", "Grace projection readback exists"),
)


def _now() -> datetime:
    return datetime.now(UTC)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)
    return hashlib.sha256(encoded.encode()).hexdigest()


@dataclass
class _MemRequest:
    request_id: str
    root_task_id: str
    correlation_id: str
    run_id: str | None = None
    result_id: str | None = None
    state: str = "queued"


class TracerStore:
    """Authoritative tracer store; memory mode is strictly a test seam."""

    def __init__(self, *, artifact_root: Path | None = None, memory: bool = False) -> None:
        self.artifact_root = Path(artifact_root or Path("runtime/closed_loop"))
        self._memory = memory
        self._roots: dict[str, dict[str, Any]] = {}
        self._requests: dict[str, _MemRequest] = {}
        self._results: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    @classmethod
    def memory(cls, *, artifact_root: Path) -> "TracerStore":
        return cls(artifact_root=artifact_root, memory=True)

    def _event(self, root_id: str, correlation_id: str, event_type: str, payload: dict[str, Any]) -> None:
        item = {"event_type": event_type, "root_task_id": root_id, "correlation_id": correlation_id, "payload": payload}
        if self._memory:
            if not any(x["event_type"] == event_type and x["root_task_id"] == root_id for x in self._events):
                self._events.append(item)
            return
        EventStore().append(RiverEvent(event_type=event_type, aggregate_type="autonomous_root_task", aggregate_id=UUID(root_id), correlation_id=UUID(correlation_id), idempotency_key=f"loop:{root_id}:{event_type}", classification=Classification.INTERNAL, payload=payload))

    def create(self, objective: str, resident: str = "grace") -> dict[str, Any]:
        root_id, correlation = uuid4(), uuid4()
        if self._memory:
            self._roots[str(root_id)] = {"root_task_id": str(root_id), "correlation_id": str(correlation), "objective": objective, "state": "queued", "originating_resident": resident, "attention_state": "none", "current_checkpoint_id": "request-formed"}
            self._requests[str(uuid4())] = _MemRequest("", str(root_id), str(correlation))
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_root_tasks(root_task_id,correlation_id,objective,state,originating_resident,current_checkpoint_id) VALUES(%s,%s,%s,'queued',%s,'request-formed')", (root_id, correlation, objective, resident))
                for seq, (cid, title, condition) in enumerate(CHECKPOINTS, 1):
                    cur.execute("INSERT INTO autonomous_checkpoints(checkpoint_id,root_task_id,roadmap_version,sequence,title,acceptance_condition,status,actor) VALUES(%s,%s,1,%s,%s,%s,'PLANNED','grace')", (cid, root_id, seq, title, condition))
        self._event(str(root_id), str(correlation), "root_task.created", {"objective": objective, "originating_resident": resident})
        self._event(str(root_id), str(correlation), "roadmap.created", {"version": 1, "checkpoints": [x[0] for x in CHECKPOINTS]})
        return {"root_task_id": str(root_id), "correlation_id": str(correlation), "objective": objective, "state": "queued"}

    def claim(self, request_id: str, owner: str) -> dict[str, Any]:
        if self._memory:
            request = next((x for x in self._requests.values() if x.request_id == request_id), None)
            if request is None:
                # test convenience: only one request is created in the tracer
                request = next(iter(self._requests.values()))
            if request.run_id is None:
                request.run_id = str(uuid4()); request.state = "claimed"
            return {"request_id": request.request_id or request_id, "root_task_id": request.root_task_id, "run_id": request.run_id, "owner": owner}
        with connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE autonomous_tracer_requests SET state='claimed',claim_owner=%s,lease_expires_at=now()+interval '15 minutes',run_id=COALESCE(run_id,gen_random_uuid()),updated_at=now() WHERE request_id=%s AND state IN ('queued','claimed') RETURNING request_id,root_task_id,run_id,correlation_id", (owner, UUID(request_id)))
            row = cur.fetchone()
            if not row: raise RuntimeError("RIV-LOOP-0002: request unavailable or already claimed")
            return {"request_id": str(row[0]), "root_task_id": str(row[1]), "run_id": str(row[2]), "correlation_id": str(row[3]), "owner": owner}

    def events_for(self, root_id: str) -> list[dict[str, Any]]:
        if self._memory: return [x for x in self._events if x["root_task_id"] == root_id]
        return EventStore().read_aggregate("autonomous_root_task", UUID(root_id))

    def read_projection(self, root_id: str) -> dict[str, Any]:
        """Return the bounded authoritative result projection for Grace."""
        if self._memory:
            result = next((item for item in self._results.values() if item["root_task_id"] == root_id), None)
            if result is None:
                raise RuntimeError("RIV-LOOP-0003: result projection is unavailable")
            request_id = result["request_id"]
            request = next(item for item in self._requests.values() if item.request_id == request_id)
            return {"root_task_id": root_id, "correlation_id": result["correlation_id"], "request_id": request_id, "result_id": result["result_id"], "run_id": result["run_id"], "current_checkpoint_id": "result-consumed", "semantic_outcome": result["semantic_outcome"], "summary": result["summary"], "evidence": result["evidence"], "adapter_id": result["adapter_id"]}
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT r.root_task_id,r.correlation_id,r.request_id,r.result_id,x.run_id,t.current_checkpoint_id,x.semantic_outcome,x.summary,x.evidence,x.result_digest FROM autonomous_tracer_results x JOIN autonomous_tracer_requests r ON r.request_id=x.request_id JOIN autonomous_root_tasks t ON t.root_task_id=x.root_task_id WHERE x.root_task_id=%s", (UUID(root_id),))
            row = cur.fetchone()
            if not row:
                raise RuntimeError("RIV-LOOP-0003: result projection is unavailable")
            return {"root_task_id": str(row[0]), "correlation_id": str(row[1]), "request_id": str(row[2]), "result_id": str(row[3]), "run_id": str(row[4]), "current_checkpoint_id": row[5], "semantic_outcome": row[6], "summary": row[7], "evidence": row[8], "result_digest": row[9], "adapter_id": "hermes.tracer.no_mutation.v1"}


class HermesTracerExecutor:
    """Safe bounded execution adapter used by the first tracer bullet."""

    adapter_id = "hermes.tracer.no_mutation.v1"

    def execute(self, request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
        return {"adapter_id": self.adapter_id, "run_id": run_id, "summary": SUMMARY, "evidence": ["bounded-local-tracer"], "semantic_outcome": "COMPLETED_NO_ATTENTION"}


def _atomic_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
    return hashlib.sha256(text.encode()).hexdigest()


def run_tracer(store: TracerStore, *, objective: str, executor: HermesTracerExecutor | None = None) -> dict[str, Any]:
    root = store.create(objective)
    root_id, correlation = root["root_task_id"], root["correlation_id"]
    request_id = str(uuid4())
    request = {"schema_version": SCHEMA_VERSION, "request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "checkpoint_id": "hermes-execution", "originating_resident": "grace", "objective": objective, "instruction": "Return one bounded evidence summary; do not mutate files."}
    request_digest = _atomic_json(store.artifact_root / "requests" / root_id / "envelope.json", request)
    _atomic_text(store.artifact_root / "requests" / root_id / "request.md", f"# {objective}\n\nBounded Hermes tracer request.\n")
    if not store._memory:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO autonomous_tracer_requests(request_id,root_task_id,correlation_id,checkpoint_id,originating_resident,objective,state,request_digest) VALUES(%s,%s,%s,%s,%s,%s,'queued',%s)", (UUID(request_id), UUID(root_id), UUID(correlation), "hermes-execution", "grace", objective, request_digest))
    store._event(root_id, correlation, "request.formed", {"request_id": request_id, "request_digest": request_digest})
    store._event(root_id, correlation, "request.queued", {"request_id": request_id})
    claimed = store.claim(request_id, "hermes-tracer")
    store._event(root_id, correlation, "hermes.claimed", claimed)
    store._event(root_id, correlation, "hermes.started", {"run_id": claimed["run_id"]})
    execution = (executor or HermesTracerExecutor()).execute(request, run_id=claimed["run_id"])
    result_id = str(uuid4())
    outcome = {"schema_version": SCHEMA_VERSION, "result_id": result_id, "request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "run_id": claimed["run_id"], "semantic_outcome": execution["semantic_outcome"], "summary": execution["summary"], "evidence": execution["evidence"], "adapter_id": execution["adapter_id"], "resulting_sha": None}
    result_digest = _atomic_json(store.artifact_root / "results" / root_id / "outcome.json", outcome)
    _atomic_text(store.artifact_root / "results" / root_id / "result.md", f"# {execution['summary']}\n\nEvidence: {', '.join(execution['evidence'])}\n")
    if store._memory:
        store._results[result_id] = outcome
    else:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO autonomous_tracer_results(result_id,request_id,root_task_id,correlation_id,run_id,semantic_outcome,summary,evidence,result_digest) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)", (UUID(result_id), UUID(request_id), UUID(root_id), UUID(correlation), UUID(claimed["run_id"]), outcome["semantic_outcome"], SUMMARY, json.dumps(outcome["evidence"]), result_digest))
            cur.execute("UPDATE autonomous_tracer_requests SET state='consumed',result_id=%s,updated_at=now() WHERE request_id=%s", (UUID(result_id), UUID(request_id)))
            cur.execute("UPDATE autonomous_root_tasks SET state='completed',current_checkpoint_id='result-consumed',updated_at=now() WHERE root_task_id=%s", (UUID(root_id),))
            cur.execute("UPDATE autonomous_checkpoints SET status='COMPLETED',completed_at=now(),evidence=%s::jsonb WHERE root_task_id=%s AND checkpoint_id IN ('request-formed','hermes-execution','result-returned','result-consumed')", (json.dumps([result_id, request_id]), UUID(root_id)))
    for event in ("hermes.result.persisted", "grace.result.available", "grace.result.consumed"):
        store._event(root_id, correlation, event, {"result_id": result_id, "request_id": request_id})
    if store._memory:
        store._requests[next(iter(store._requests))].request_id = request_id
    projection = store.read_projection(root_id)
    return {"state": "consumed", **projection, "projection": projection, "artifacts": {"request": str(store.artifact_root / "requests" / root_id / "envelope.json"), "result": str(store.artifact_root / "results" / root_id / "outcome.json")}, "request_digest": request_digest, "result_digest": result_digest, "events": [x["event_type"] for x in store.events_for(root_id)]}
