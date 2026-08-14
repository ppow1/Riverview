"""Restart/resume acceptance for RV-005.2.

Version: 0.2.7
"""

from __future__ import annotations

import json
import sys

from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.river.store import EventStore

DEFAULT_KEY="acceptance.rv0052.restart"
def seed(key: str) -> dict[str,object]:
    store=ObjectiveStore()
    objective_id=store.create(
        key,
        "RV-005.2 restart acceptance",
        "Prove objective and stage state resumes from PostgreSQL after process restart.",
        [
            StageSpec(
                key="collect",
                title="Collect evidence",
                description="Persist first-stage evidence.",
                required_evidence=("acceptance:seed",),
            ),
            StageSpec(
                key="deliver",
                title="Deliver final output",
                description="Resume and finish after a separate process starts.",
                required_evidence=("acceptance:resume",),
                depends_on=("collect",),
            ),
        ],
        requested_by="acceptance",
    )
    state=store.load(key)
    if state["stages"][0]["readiness"]!="ready" or state["stages"][1]["readiness"]!="waiting":
        raise RuntimeError("RIV-GRC-0002: initial readiness is incorrect.")
    return {"status":"seeded","objective_id":str(objective_id),"first":state["stages"][0]["readiness"],"second":state["stages"][1]["readiness"]}


def read_and_finish(key: str) -> dict[str,object]:
    store=ObjectiveStore()
    state=store.load(key)
    if state["objective_key"]!=key:
        raise RuntimeError("RIV-GRC-0002: objective did not resume from PostgreSQL.")

    if state["status"]=="completed":
        stream=EventStore().read_aggregate("objective",state["objective_id"])
        return {"status":"healthy","resumed":True,"already_completed":True,"event_count":len(stream),"final_output":state["final_output"]}

    try:
        store.complete_stage(key,"collect",{"premature":True})
    except RuntimeError as exc:
        if "missing required evidence" not in str(exc):
            raise
    else:
        raise RuntimeError("RIV-GRC-0002: missing-evidence failure was not induced.")

    store.add_evidence(key,"collect","acceptance:seed")
    store.complete_stage(key,"collect",{"collected":True})

    mid=store.load(key)
    deliver=next(stage for stage in mid["stages"] if stage["stage_key"]=="deliver")
    if deliver["readiness"]!="ready":
        raise RuntimeError("RIV-GRC-0002: dependency completion did not make deliver stage ready.")

    store.add_evidence(key,"deliver","acceptance:resume")
    store.complete_stage(key,"deliver",{"delivered":True})
    store.finalize(key,{"artifact":"acceptance","result":"complete"})

    final=store.load(key)
    if final["status"]!="completed":
        raise RuntimeError("RIV-GRC-0002: final objective status is not completed.")
    if final["final_output"]!={"artifact":"acceptance","result":"complete"}:
        raise RuntimeError("RIV-GRC-0002: final output was not persisted.")

    stream=EventStore().read_aggregate("objective",final["objective_id"])
    event_types=[event["event_type"] for event in stream]
    required={"objective.created","objective.stage.evidence.accepted","objective.stage.completed","objective.completed"}
    if not required.issubset(set(event_types)):
        raise RuntimeError(f"RIV-GRC-0002: River event evidence incomplete: {event_types}")

    return {
        "status":"healthy",
        "resumed":True,
        "induced_missing_evidence_rejected":True,
        "objective_status":final["status"],
        "final_output":final["final_output"],
        "stage_states":[
            {"stage_key":stage["stage_key"],"status":stage["status"],"readiness":stage["readiness"]}
            for stage in final["stages"]
        ],
        "event_types":event_types,
    }


if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "read"
    key=sys.argv[2] if len(sys.argv)>2 else DEFAULT_KEY
    result=seed(key) if mode=="seed" else read_and_finish(key)
    print(json.dumps(result,indent=2,sort_keys=True,default=str))