"""First bounded Grace -> Hermes -> result -> Grace tracer spine."""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock
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
        self._states: dict[str, str] = {}
        self._claim_lock = Lock()

    @classmethod
    def memory(cls, *, artifact_root: Path) -> "TracerStore":
        return cls(artifact_root=artifact_root, memory=True)

    def _event(self, root_id: str, correlation_id: str, event_type: str, payload: dict[str, Any]) -> None:
        item = {"event_type": event_type, "root_task_id": root_id, "correlation_id": correlation_id, "payload": payload}
        if self._memory:
            self._events.append(item)
            return
        identity = payload.get("request_id") or payload.get("result_id") or payload.get("source_result_id") or event_type
        EventStore().append(RiverEvent(event_type=event_type, aggregate_type="autonomous_root_task", aggregate_id=UUID(root_id), correlation_id=UUID(correlation_id), idempotency_key=f"loop:{root_id}:{event_type}:{identity}", classification=Classification.INTERNAL, payload=payload))

    def create(self, objective: str, resident: str = "grace") -> dict[str, Any]:
        root_id, correlation = uuid4(), uuid4()
        if self._memory:
            self._roots[str(root_id)] = {"root_task_id": str(root_id), "correlation_id": str(correlation), "objective": objective, "state": "queued", "originating_resident": resident, "attention_state": "none", "current_checkpoint_id": "request-formed"}
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_root_tasks(root_task_id,correlation_id,objective,state,originating_resident,current_checkpoint_id) VALUES(%s,%s,%s,'queued',%s,'request-formed')", (root_id, correlation, objective, resident))
                for seq, (cid, title, condition) in enumerate(CHECKPOINTS, 1):
                    cur.execute("INSERT INTO autonomous_checkpoints(checkpoint_id,root_task_id,roadmap_version,sequence,title,acceptance_condition,status,actor) VALUES(%s,%s,1,%s,%s,%s,'PLANNED','grace')", (cid, root_id, seq, title, condition))
        self._event(str(root_id), str(correlation), "root_task.created", {"objective": objective, "originating_resident": resident})
        self._event(str(root_id), str(correlation), "roadmap.created", {"version": 1, "checkpoints": [x[0] for x in CHECKPOINTS]})
        return {"root_task_id": str(root_id), "correlation_id": str(correlation), "objective": objective, "state": "queued"}

    def dispatch(self, objective: str, resident: str = "grace") -> dict[str, Any]:
        """Form one queued request without executing it."""
        root = self.create(objective, resident)
        request_id = str(uuid4())
        request = {"schema_version": SCHEMA_VERSION, "request_id": request_id, "root_task_id": root["root_task_id"], "correlation_id": root["correlation_id"], "checkpoint_id": "hermes-execution", "originating_resident": resident, "objective": objective, "instruction": "Return one bounded evidence summary; do not mutate files."}
        digest = _atomic_json(self.artifact_root / "requests" / root["root_task_id"] / "envelope.json", request)
        _atomic_text(self.artifact_root / "requests" / root["root_task_id"] / "request.md", f"# {objective}\n\nBounded queued Hermes request.\n")
        if self._memory:
            self._requests[request_id] = _MemRequest(request_id, root["root_task_id"], root["correlation_id"])
            self._states[root["root_task_id"]] = "queued"
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_tracer_requests(request_id,root_task_id,correlation_id,checkpoint_id,originating_resident,objective,state,request_digest) VALUES(%s,%s,%s,%s,%s,%s,'queued',%s)", (UUID(request_id), UUID(root["root_task_id"]), UUID(root["correlation_id"]), "hermes-execution", resident, objective, digest))
        self._event(root["root_task_id"], root["correlation_id"], "request.formed", {"request_id": request_id, "request_digest": digest})
        self._event(root["root_task_id"], root["correlation_id"], "request.queued", {"request_id": request_id})
        return {**root, "request_id": request_id, "checkpoint_id": "hermes-execution", "request_digest": digest}

    def claim(self, request_id: str, owner: str) -> dict[str, Any]:
        if self._memory:
            with self._claim_lock:
                request = self._requests.get(request_id)
                if request is None:
                    raise LookupError(f"RIV-LOOP-0005: unknown request {request_id}")
                if request.run_id is None:
                    request.run_id = str(uuid4()); request.state = "claimed"
                return {"request_id": request.request_id, "root_task_id": request.root_task_id, "run_id": request.run_id, "correlation_id": request.correlation_id, "owner": owner}
        with connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE autonomous_tracer_requests SET state='claimed',claim_owner=%s,lease_expires_at=now()+interval '15 minutes',run_id=COALESCE(run_id,gen_random_uuid()),updated_at=now() WHERE request_id=%s AND state IN ('queued','claimed') RETURNING request_id,root_task_id,run_id,correlation_id", (owner, UUID(request_id)))
            row = cur.fetchone()
            if not row: raise RuntimeError("RIV-LOOP-0002: request unavailable or already claimed")
            return {"request_id": str(row[0]), "root_task_id": str(row[1]), "run_id": str(row[2]), "correlation_id": str(row[3]), "owner": owner}

    def read_state(self, root_id: str) -> dict[str, Any]:
        if self._memory:
            if root_id not in self._roots: raise LookupError(f"RIV-LOOP-0006: unknown root {root_id}")
            return {"root_task_id": root_id, "state": self._states.get(root_id, self._roots[root_id]["state"])}
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT root_task_id,state,current_checkpoint_id FROM autonomous_root_tasks WHERE root_task_id=%s", (UUID(root_id),)); row=cur.fetchone()
            if not row: raise LookupError(f"RIV-LOOP-0006: unknown root {root_id}")
            return {"root_task_id": str(row[0]), "state": row[1], "current_checkpoint_id": row[2]}

    def queued_request_ids(self) -> tuple[str, ...]:
        if self._memory:
            return tuple(item.request_id for item in self._requests.values() if item.state == "queued")
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT request_id FROM autonomous_tracer_requests WHERE state='queued' ORDER BY created_at")
            return tuple(str(row[0]) for row in cur.fetchall())

    def worker(self, *, executor: Any | None = None, max_workers: int = 3, binding_store: Any | None = None) -> "TracerWorker":
        return TracerWorker(self, executor=executor or HermesTracerExecutor(), max_workers=max_workers, binding_store=binding_store)

    def events_for(self, root_id: str) -> list[dict[str, Any]]:
        if self._memory: return [x for x in self._events if x["root_task_id"] == root_id]
        return EventStore().read_aggregate("autonomous_root_task", UUID(root_id))

    def read_projection(self, root_id: str) -> dict[str, Any]:
        """Return the bounded authoritative result projection for Grace."""
        if self._memory:
            result = next((item for item in reversed(list(self._results.values())) if item["root_task_id"] == root_id), None)
            if result is None:
                root = self._roots.get(root_id)
                if root is None: raise LookupError(f"RIV-LOOP-0003: unknown root {root_id}")
                return {"root_task_id": root_id, "correlation_id": root["correlation_id"], "request_id": None, "result_id": None, "run_id": None, "current_checkpoint_id": root.get("current_checkpoint_id"), "semantic_outcome": None, "summary": None, "evidence": [], "state": self._states.get(root_id, "queued")}
            request_id = result["request_id"]
            request = next(item for item in self._requests.values() if item.request_id == request_id)
            return {"root_task_id": root_id, "correlation_id": result["correlation_id"], "request_id": request_id, "result_id": result["result_id"], "run_id": result["run_id"], "current_checkpoint_id": "result-consumed", "semantic_outcome": result["semantic_outcome"], "summary": result["summary"], "evidence": result["evidence"], "adapter_id": result["adapter_id"]}
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT r.root_task_id,r.correlation_id,r.request_id,r.result_id,x.run_id,t.current_checkpoint_id,x.semantic_outcome,x.summary,x.evidence,x.result_digest FROM autonomous_tracer_results x JOIN autonomous_tracer_requests r ON r.request_id=x.request_id JOIN autonomous_root_tasks t ON t.root_task_id=x.root_task_id WHERE x.root_task_id=%s ORDER BY x.created_at DESC LIMIT 1", (UUID(root_id),))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT root_task_id,correlation_id,current_checkpoint_id,state FROM autonomous_root_tasks WHERE root_task_id=%s", (UUID(root_id),)); root = cur.fetchone()
                if not root: raise LookupError(f"RIV-LOOP-0003: unknown root {root_id}")
                return {"root_task_id": str(root[0]), "correlation_id": str(root[1]), "request_id": None, "result_id": None, "run_id": None, "current_checkpoint_id": root[2], "semantic_outcome": None, "summary": None, "evidence": [], "state": root[3]}
            return {"root_task_id": str(row[0]), "correlation_id": str(row[1]), "request_id": str(row[2]), "result_id": str(row[3]), "run_id": str(row[4]), "current_checkpoint_id": row[5], "semantic_outcome": row[6], "summary": row[7], "evidence": row[8], "result_digest": row[9], "adapter_id": "hermes.tracer.no_mutation.v1"}

    def continue_from_result(self, root_id: str, result_id: str, *, objective: str) -> dict[str, Any]:
        """Create and execute one same-root successor request."""
        if self._memory:
            prior = self._results.get(result_id)
            if prior is None or prior["root_task_id"] != root_id:
                raise RuntimeError("RIV-LOOP-0004: continuation source is not the same root")
            correlation = prior["correlation_id"]
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT correlation_id FROM autonomous_tracer_results WHERE result_id=%s AND root_task_id=%s", (UUID(result_id), UUID(root_id)))
                row = cur.fetchone()
                if not row: raise RuntimeError("RIV-LOOP-0004: continuation source is not the same root")
                correlation = str(row[0])
        self._event(root_id, correlation, "continuation.requested", {"source_result_id": result_id, "objective": objective})
        request_id, run_id, new_result_id = str(uuid4()), str(uuid4()), str(uuid4())
        request = {"schema_version": SCHEMA_VERSION, "request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "checkpoint_id": "hermes-execution-2", "originating_resident": "grace", "objective": objective, "instruction": "Return one bounded evidence summary; do not mutate files."}
        request_digest = _atomic_json(self.artifact_root / "requests" / root_id / f"{request_id}.json", request)
        _atomic_text(self.artifact_root / "requests" / root_id / f"{request_id}.md", f"# {objective}\n\nBounded Hermes continuation request.\n")
        if self._memory:
            self._requests[request_id] = _MemRequest(request_id, root_id, correlation)
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_tracer_requests(request_id,root_task_id,correlation_id,checkpoint_id,originating_resident,objective,state,request_digest,run_id) VALUES(%s,%s,%s,%s,%s,%s,'queued',%s,%s)", (UUID(request_id), UUID(root_id), UUID(correlation), "hermes-execution-2", "grace", objective, request_digest, UUID(run_id)))
        self._event(root_id, correlation, "request.formed", {"request_id": request_id, "request_digest": request_digest})
        self._event(root_id, correlation, "request.queued", {"request_id": request_id})
        claimed = self.claim(request_id, "hermes-tracer")
        self._event(root_id, correlation, "hermes.claimed", claimed)
        self._event(root_id, correlation, "hermes.started", {"run_id": claimed["run_id"], "request_id": request_id})
        execution = HermesTracerExecutor().execute(request, run_id=claimed["run_id"])
        outcome = {"schema_version": SCHEMA_VERSION, "result_id": new_result_id, "request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "run_id": claimed["run_id"], "semantic_outcome": execution["semantic_outcome"], "summary": execution["summary"], "evidence": execution["evidence"], "adapter_id": execution["adapter_id"], "resulting_sha": None}
        result_digest = _atomic_json(self.artifact_root / "results" / root_id / f"{new_result_id}.json", outcome)
        _atomic_text(self.artifact_root / "results" / root_id / f"{new_result_id}.md", f"# {execution['summary']}\n\nEvidence: {', '.join(execution['evidence'])}\n")
        if self._memory:
            self._results[new_result_id] = outcome
            self._requests[request_id].run_id = claimed["run_id"]; self._requests[request_id].result_id = new_result_id; self._requests[request_id].state = "consumed"
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_tracer_results(result_id,request_id,root_task_id,correlation_id,run_id,semantic_outcome,summary,evidence,result_digest) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)", (UUID(new_result_id), UUID(request_id), UUID(root_id), UUID(correlation), UUID(claimed["run_id"]), execution["semantic_outcome"], execution["summary"], json.dumps(execution["evidence"]), result_digest))
                cur.execute("UPDATE autonomous_tracer_requests SET state='consumed',result_id=%s,updated_at=now() WHERE request_id=%s", (UUID(new_result_id), UUID(request_id)))
        for event in ("hermes.result.persisted", "grace.result.available", "grace.result.consumed"):
            self._event(root_id, correlation, event, {"result_id": new_result_id, "request_id": request_id})
        projection = self.read_projection(root_id)
        return {"state": "consumed", **projection, "projection": projection, "request_id": request_id, "result_id": new_result_id, "request_digest": request_digest, "result_digest": result_digest, "events": [x["event_type"] for x in self.events_for(root_id)]}


class HermesTracerExecutor:
    """Safe bounded execution adapter used by the first tracer bullet."""

    adapter_id = "hermes.tracer.no_mutation.v1"

    def execute(self, request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
        return {"adapter_id": self.adapter_id, "run_id": run_id, "summary": SUMMARY, "evidence": ["bounded-local-tracer"], "semantic_outcome": "COMPLETED_NO_ATTENTION"}


class TracerWorker:
    """Nonblocking bounded worker for independently correlated requests."""

    def __init__(self, store: TracerStore, *, executor: Any, max_workers: int = 3, binding_store: Any | None = None) -> None:
        if max_workers < 1: raise ValueError("max_workers must be positive")
        if not store._memory and binding_store is None:
            raise PermissionError("RIV-LOOP-0010: production worker requires an authoritative governance binding store.")
        self.store, self.executor, self.binding_store = store, executor, binding_store
        self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="riverview-loop")

    def submit(self, request_id: str) -> Future:
        return self.pool.submit(self._run_one, request_id)

    def submit_next(self, limit: int = 1) -> tuple[Future, ...]:
        """Claim eligible queued requests without requiring Grace transport."""
        if limit < 1: raise ValueError("limit must be positive")
        return tuple(self.submit(request_id) for request_id in self.store.queued_request_ids()[:limit])

    def shutdown(self, *, wait: bool = True) -> None:
        self.pool.shutdown(wait=wait)

    def _run_one(self, request_id: str) -> dict[str, Any]:
        claimed = self.store.claim(request_id, "closed-loop-worker")
        root_id, correlation, run_id = claimed["root_task_id"], claimed["correlation_id"], claimed["run_id"]
        if self.binding_store is not None:
            try:
                self.binding_store.require_executable(UUID(root_id))
            except Exception as exc:
                if self.store._memory: self.store._states[root_id] = "blocked"
                self.store._event(root_id, correlation, "execution.denied", {"request_id": request_id, "reason": str(exc)[:500]})
                return {"state": "blocked", "root_task_id": root_id, "request_id": request_id, "run_id": run_id, "result_id": None, "reason": str(exc)}
        if self.store._memory: self.store._states[root_id] = "running"
        else:
            with connect() as conn, conn.cursor() as cur: cur.execute("UPDATE autonomous_root_tasks SET state='active',updated_at=now() WHERE root_task_id=%s", (UUID(root_id),))
        self.store._event(root_id, correlation, "hermes.claimed", claimed)
        self.store._event(root_id, correlation, "hermes.started", {"request_id": request_id, "run_id": run_id})
        request = {"request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "objective": self.store._roots.get(root_id, {}).get("objective", "bounded tracer")}
        try:
            execution = self.executor.execute(request, run_id=run_id)
        except Exception as exc:
            if self.store._memory: self.store._states[root_id] = "failed"
            else:
                with connect() as conn, conn.cursor() as cur: cur.execute("UPDATE autonomous_tracer_requests SET state='blocked',updated_at=now() WHERE request_id=%s", (UUID(request_id),))
            self.store._event(root_id, correlation, "hermes.failed", {"request_id": request_id, "run_id": run_id, "reason": str(exc)[:500]})
            return {"state": "failed", "root_task_id": root_id, "request_id": request_id, "run_id": run_id, "result_id": None}
        result_id = str(uuid4())
        result = {"schema_version": SCHEMA_VERSION, "result_id": result_id, "request_id": request_id, "root_task_id": root_id, "correlation_id": correlation, "run_id": run_id, "semantic_outcome": execution["semantic_outcome"], "summary": execution["summary"], "evidence": execution["evidence"], "adapter_id": execution["adapter_id"], "resulting_sha": None}
        digest = _atomic_json(self.store.artifact_root / "results" / root_id / f"{result_id}.json", result)
        _atomic_text(self.store.artifact_root / "results" / root_id / f"{result_id}.md", f"# {execution['summary']}\n\nEvidence: {', '.join(execution['evidence'])}\n")
        if self.store._memory:
            self.store._results[result_id] = result; self.store._states[root_id] = "completed"
        else:
            with connect() as conn, conn.cursor() as cur:
                cur.execute("INSERT INTO autonomous_tracer_results(result_id,request_id,root_task_id,correlation_id,run_id,semantic_outcome,summary,evidence,result_digest) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)", (UUID(result_id), UUID(request_id), UUID(root_id), UUID(correlation), UUID(run_id), result["semantic_outcome"], result["summary"], json.dumps(result["evidence"]), digest))
                cur.execute("UPDATE autonomous_tracer_requests SET state='consumed',result_id=%s,updated_at=now() WHERE request_id=%s", (UUID(result_id), UUID(request_id)))
                cur.execute("UPDATE autonomous_root_tasks SET state='completed',current_checkpoint_id='result-consumed',updated_at=now() WHERE root_task_id=%s", (UUID(root_id),))
        for event in ("hermes.result.persisted", "grace.result.available", "grace.result.consumed"):
            self.store._event(root_id, correlation, event, {"request_id": request_id, "result_id": result_id})
        projection = self.store.read_projection(root_id)
        return {"state": "completed", **projection, "result_id": result_id, "result_digest": digest}

    def read_projection(self, root_id: str) -> dict[str, Any]:
        return self.store.read_projection(root_id)

    def read_state(self, root_id: str) -> dict[str, Any]:
        return self.store.read_state(root_id)

    def continue_from_result(self, root_id: str, result_id: str, *, objective: str) -> dict[str, Any]:
        return self.store.continue_from_result(root_id, result_id, objective=objective)


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
    if store._memory:
        store._requests[request_id] = _MemRequest(request_id, root_id, correlation)
    if not store._memory:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO autonomous_tracer_requests(request_id,root_task_id,correlation_id,checkpoint_id,originating_resident,objective,state,request_digest) VALUES(%s,%s,%s,%s,%s,%s,'queued',%s)", (UUID(request_id), UUID(root_id), UUID(correlation), "hermes-execution", "grace", objective, request_digest))
    store._event(root_id, correlation, "request.formed", {"request_id": request_id, "request_digest": request_digest})
    store._event(root_id, correlation, "request.queued", {"request_id": request_id})
    claimed = store.claim(request_id, "hermes-tracer")
    store._event(root_id, correlation, "hermes.claimed", claimed)
    store._event(root_id, correlation, "hermes.started", {"run_id": claimed["run_id"], "request_id": request_id})
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
    projection = store.read_projection(root_id)
    return {"state": "consumed", **projection, "projection": projection, "artifacts": {"request": str(store.artifact_root / "requests" / root_id / "envelope.json"), "result": str(store.artifact_root / "results" / root_id / "outcome.json")}, "request_digest": request_digest, "result_digest": result_digest, "events": [x["event_type"] for x in store.events_for(root_id)]}
