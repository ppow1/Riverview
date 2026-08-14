"""Master-roadmap database acceptance. Version: 0.8.0"""

from __future__ import annotations

import json

from riverview.database import connect
from riverview.roadmap import apply_master_roadmap


def acceptance() -> dict[str, object]:
    applied=apply_master_roadmap()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM roadmap_items WHERE roadmap_revision=%s",(applied["revision"],))
        count=cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM roadmap_items r WHERE r.parent_waypoint_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM roadmap_items p WHERE p.waypoint_id=r.parent_waypoint_id)")
        orphans=cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM roadmap_items WHERE roadmap_revision=%s AND(jsonb_array_length(acceptance_criteria)=0 OR scope_boundary='')",(applied["revision"],))
        incomplete=cursor.fetchone()[0]
        cursor.execute("SELECT waypoint_count,content_sha256 FROM roadmap_revisions WHERE revision_id=%s",(applied["revision"],))
        revision=cursor.fetchone()
    if count!=applied["waypoints"] or orphans or incomplete or not revision or revision[0]!=count or revision[1]!=applied["sha256"]:
        raise RuntimeError("RIV-RDM-0006: Database roadmap acceptance failed.")
    return {"status":"healthy","revision":applied["revision"],"waypoints":count,"orphans":0,"incomplete_contracts":0,"hash_verified":True}


if __name__=="__main__":
    print(json.dumps(acceptance(),indent=2,sort_keys=True))