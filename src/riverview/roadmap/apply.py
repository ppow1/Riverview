"""Validate and transactionally apply the versioned Riverview master roadmap.

Version: 0.8.0
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from riverview.database import connect

ROADMAP_PATH = Path("docs/operations/roadmap/RIVERVIEW_MASTER_ROADMAP.json")


def load_and_validate(path: Path = ROADMAP_PATH) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    document: dict[str, Any] = json.loads(raw.decode("utf-8-sig"))
    items = document.get("waypoints")
    if not isinstance(items, list) or not items:
        raise RuntimeError("RIV-RDM-0001: Master roadmap has no waypoints.")
    ids = [item.get("id") for item in items]
    if len(ids) != len(set(ids)) or any(not isinstance(item_id, str) for item_id in ids):
        raise RuntimeError("RIV-RDM-0002: Waypoint identifiers are missing or duplicated.")
    known = set(ids)
    allowed = {"pending", "active", "blocked", "completed", "cancelled"}
    for item in items:
        if item.get("parent") is not None and item["parent"] not in known:
            raise RuntimeError(f"RIV-RDM-0003: Orphan waypoint: {item['id']}")
        missing = [dependency for dependency in item.get("depends", []) if dependency not in known]
        if missing:
            raise RuntimeError(f"RIV-RDM-0004: Unknown dependencies for {item['id']}: {missing}")
        if item.get("status") not in allowed or not item.get("accept") or not item.get("boundary"):
            raise RuntimeError(f"RIV-RDM-0005: Incomplete execution contract: {item['id']}")
    return document, hashlib.sha256(raw).hexdigest()


def apply_master_roadmap(path: Path = ROADMAP_PATH) -> dict[str, Any]:
    document, digest = load_and_validate(path)
    revision = document["roadmap_revision"]
    refs = document["governing_refs"]
    with connect() as connection, connection.cursor() as cursor:
        for item in document["waypoints"]:
            cursor.execute(
                """INSERT INTO roadmap_items(waypoint_id,parent_waypoint_id,sort_order,title,description,status,steward_checkpoint,acceptance_criteria,depends_on,governing_refs,scope_boundary,roadmap_revision,completed_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,CASE WHEN %s='completed' THEN COALESCE((SELECT completed_at FROM roadmap_items WHERE waypoint_id=%s),now()) END)
                   ON CONFLICT(waypoint_id) DO UPDATE SET parent_waypoint_id=EXCLUDED.parent_waypoint_id,sort_order=EXCLUDED.sort_order,title=EXCLUDED.title,description=EXCLUDED.description,status=EXCLUDED.status,steward_checkpoint=EXCLUDED.steward_checkpoint,acceptance_criteria=EXCLUDED.acceptance_criteria,depends_on=EXCLUDED.depends_on,governing_refs=EXCLUDED.governing_refs,scope_boundary=EXCLUDED.scope_boundary,roadmap_revision=EXCLUDED.roadmap_revision,completed_at=EXCLUDED.completed_at,updated_at=now()""",
                (item["id"],item["parent"],item["order"],item["title"],item["description"],item["status"],item["steward"],json.dumps(item["accept"]),json.dumps(item["depends"]),json.dumps(refs),item["boundary"],revision,item["status"],item["id"]),
            )
        cursor.execute("INSERT INTO roadmap_revisions(revision_id,content_sha256,waypoint_count,source_path)VALUES(%s,%s,%s,%s) ON CONFLICT(revision_id)DO UPDATE SET content_sha256=EXCLUDED.content_sha256,waypoint_count=EXCLUDED.waypoint_count,source_path=EXCLUDED.source_path,applied_at=now()",(revision,digest,len(document["waypoints"]),str(path)))
    return {"revision":revision,"sha256":digest,"waypoints":len(document["waypoints"])}