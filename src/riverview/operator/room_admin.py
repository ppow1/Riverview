"""Durable, room-scoped membership and administration projection."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect


class RoomAdministration:
    """Owns room membership/admin state, never resident continuity or global authority."""

    def __init__(self) -> None:
        self.available = True
        self.memberships: dict[UUID, list[dict[str, Any]]] = {}
        self.administrators: dict[UUID, list[dict[str, Any]]] = {}
        try:
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM operator_room_memberships LIMIT 1")
        except (RuntimeError, OSError, ValueError):
            self.available = False

    def initialize(self, room_id: UUID, participants: list[str] | tuple[str, ...], *, actor: str = "steward", correlation_id: UUID | None = None) -> None:
        correlation = correlation_id or uuid4()
        if not self.available:
            rows = self.memberships.setdefault(room_id, [])
            for resident_id in participants:
                if not any(row["resident_id"] == resident_id and row["state"] == "active" for row in rows):
                    rows.append({"membership_id": str(uuid4()), "room_id": str(room_id), "resident_id": resident_id, "state": "active", "added_by": actor, "context_window": "from_this_point", "source_conversation_id": "", "correlation_id": str(correlation)})
            admins = self.administrators.setdefault(room_id, [])
            if not any(row["administrator_id"] == actor and row["active"] for row in admins):
                admins.append({"administration_id": str(uuid4()), "room_id": str(room_id), "administrator_id": actor, "active": True, "primary_administrator": True, "granted_by": actor, "correlation_id": str(correlation)})
            return
        with connect() as connection, connection.cursor() as cursor:
            for resident_id in participants:
                cursor.execute("""INSERT INTO operator_room_memberships(membership_id,room_id,resident_id,state,added_by,context_window,correlation_id)
                                 SELECT %s,%s,%s,'active',%s,'from_this_point',%s
                                 WHERE NOT EXISTS (SELECT 1 FROM operator_room_memberships WHERE room_id=%s AND resident_id=%s AND state='active')""", (uuid4(), room_id, resident_id, actor, correlation, room_id, resident_id))
            cursor.execute("""INSERT INTO operator_room_administrators(administration_id,room_id,administrator_id,primary_administrator,granted_by,correlation_id)
                             SELECT %s,%s,%s,true,%s,%s WHERE NOT EXISTS (SELECT 1 FROM operator_room_administrators WHERE room_id=%s AND administrator_id=%s AND active)""", (uuid4(), room_id, actor, actor, correlation, room_id, actor))

    def snapshot(self, room_id: UUID) -> dict[str, Any]:
        if not self.available:
            memberships = self.memberships.get(room_id, [])
            admins = self.administrators.get(room_id, [])
            return {"memberships": memberships, "participants": [row["resident_id"] for row in memberships if row["state"] == "active"], "administrators": [row for row in admins if row["active"]]}
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT membership_id,room_id,resident_id,state,added_by,added_at,removed_by,removed_at,context_window,source_conversation_id,correlation_id FROM operator_room_memberships WHERE room_id=%s ORDER BY added_at", (room_id,))
            memberships = [self._membership(row) for row in cursor.fetchall()]
            cursor.execute("SELECT administration_id,room_id,administrator_id,active,primary_administrator,granted_by,granted_at,revoked_by,revoked_at,correlation_id FROM operator_room_administrators WHERE room_id=%s ORDER BY granted_at", (room_id,))
            admins = [self._admin(row) for row in cursor.fetchall()]
            return {"memberships": memberships, "participants": [row["resident_id"] for row in memberships if row["state"] == "active"], "administrators": [row for row in admins if row["active"]]}

    @staticmethod
    def _membership(row: tuple[Any, ...]) -> dict[str, Any]:
        keys = ("membership_id", "room_id", "resident_id", "state", "added_by", "added_at", "removed_by", "removed_at", "context_window", "source_conversation_id", "correlation_id")
        result = dict(zip(keys, row, strict=True))
        return {key: (str(value) if key.endswith("_id") or key == "correlation_id" else value) for key, value in result.items()}

    @staticmethod
    def _admin(row: tuple[Any, ...]) -> dict[str, Any]:
        keys = ("administration_id", "room_id", "administrator_id", "active", "primary_administrator", "granted_by", "granted_at", "revoked_by", "revoked_at", "correlation_id")
        result = dict(zip(keys, row, strict=True))
        return {key: (str(value) if key.endswith("_id") or key == "correlation_id" else value) for key, value in result.items()}

    def add(self, room_id: UUID, resident_id: str, *, actor: str, context_window: str, source_conversation_id: UUID | None = None, correlation_id: UUID | None = None) -> dict[str, Any]:
        correlation = correlation_id or uuid4()
        current = self.snapshot(room_id)
        if resident_id in current["participants"]:
            raise ValueError("resident is already an active room participant")
        if not self.available:
            row = {"membership_id": str(uuid4()), "room_id": str(room_id), "resident_id": resident_id, "state": "active", "added_by": actor, "context_window": context_window, "source_conversation_id": str(source_conversation_id or ""), "correlation_id": str(correlation)}
            self.memberships.setdefault(room_id, []).append(row)
            return row
        with connect() as connection, connection.cursor() as cursor:
            membership_id = uuid4()
            cursor.execute("INSERT INTO operator_room_memberships(membership_id,room_id,resident_id,state,added_by,context_window,source_conversation_id,correlation_id) VALUES(%s,%s,%s,'active',%s,%s,%s,%s)", (membership_id, room_id, resident_id, actor, context_window, source_conversation_id, correlation))
        return {"membership_id": str(membership_id), "room_id": str(room_id), "resident_id": resident_id, "state": "active", "added_by": actor, "context_window": context_window, "source_conversation_id": str(source_conversation_id or ""), "correlation_id": str(correlation)}

    def remove(self, room_id: UUID, resident_id: str, *, actor: str, correlation_id: UUID | None = None) -> dict[str, Any]:
        if resident_id == "steward":
            raise PermissionError("the Steward cannot be removed by a resident")
        current = self.snapshot(room_id)
        if resident_id not in current["participants"]:
            raise LookupError("resident is not an active room participant")
        correlation = correlation_id or uuid4()
        if not self.available:
            row = next(row for row in self.memberships[room_id] if row["resident_id"] == resident_id and row["state"] == "active")
            row.update(state="removed", removed_by=actor, removed_at="now", correlation_id=str(correlation))
            for admin in self.administrators.get(room_id, []):
                if admin["administrator_id"] == resident_id and admin["active"]:
                    admin.update(active=False, revoked_by=actor, revoked_at="now", correlation_id=str(correlation))
            return row
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE operator_room_administrators SET active=false,revoked_by=%s,revoked_at=now(),correlation_id=%s WHERE room_id=%s AND administrator_id=%s AND active", (actor, correlation, room_id, resident_id))
            cursor.execute("UPDATE operator_room_memberships SET state='removed',removed_by=%s,removed_at=now(),correlation_id=%s WHERE room_id=%s AND resident_id=%s AND state='active' RETURNING membership_id,room_id,resident_id,state,added_by,added_at,removed_by,removed_at,context_window,source_conversation_id,correlation_id", (actor, correlation, room_id, resident_id))
            row = cursor.fetchone()
            if row is None:
                raise LookupError("resident is not an active room participant")
        return self._membership(row)

    def grant_admin(self, room_id: UUID, administrator_id: str, *, actor: str, primary: bool = False, correlation_id: UUID | None = None) -> dict[str, Any]:
        if administrator_id != "steward" and administrator_id not in self.snapshot(room_id)["participants"]:
            raise ValueError("administrator must be an active room participant")
        correlation = correlation_id or uuid4()
        if not self.available:
            row = {"administration_id": str(uuid4()), "room_id": str(room_id), "administrator_id": administrator_id, "active": True, "primary_administrator": primary, "granted_by": actor, "correlation_id": str(correlation)}
            self.administrators.setdefault(room_id, []).append(row)
            return row
        with connect() as connection, connection.cursor() as cursor:
            if primary:
                cursor.execute("UPDATE operator_room_administrators SET primary_administrator=false WHERE room_id=%s AND active", (room_id,))
            cursor.execute("UPDATE operator_room_administrators SET active=true,revoked_by=NULL,revoked_at=NULL,primary_administrator=%s WHERE room_id=%s AND administrator_id=%s RETURNING administration_id,room_id,administrator_id,active,primary_administrator,granted_by,granted_at,revoked_by,revoked_at,correlation_id", (primary, room_id, administrator_id))
            row = cursor.fetchone()
            if row is None:
                administration_id = uuid4()
                cursor.execute("INSERT INTO operator_room_administrators(administration_id,room_id,administrator_id,primary_administrator,granted_by,correlation_id) VALUES(%s,%s,%s,%s,%s,%s) RETURNING administration_id,room_id,administrator_id,active,primary_administrator,granted_by,granted_at,revoked_by,revoked_at,correlation_id", (administration_id, room_id, administrator_id, primary, actor, correlation))
                row = cursor.fetchone()
        return self._admin(row)

    def revoke_admin(self, room_id: UUID, administrator_id: str, *, actor: str, correlation_id: UUID | None = None) -> dict[str, Any]:
        current = self.snapshot(room_id)
        active = [row for row in current["administrators"] if row["active"]]
        if administrator_id not in {row["administrator_id"] for row in active}:
            raise LookupError("administrator is not active")
        if len(active) <= 1:
            raise ValueError("last room administrator requires successor or room closure")
        correlation = correlation_id or uuid4()
        if not self.available:
            row = next(row for row in self.administrators[room_id] if row["administrator_id"] == administrator_id and row["active"])
            row.update(active=False, revoked_by=actor, revoked_at="now", correlation_id=str(correlation))
            return row
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE operator_room_administrators SET active=false,revoked_by=%s,revoked_at=now(),correlation_id=%s WHERE room_id=%s AND administrator_id=%s AND active RETURNING administration_id,room_id,administrator_id,active,primary_administrator,granted_by,granted_at,revoked_by,revoked_at,correlation_id", (actor, correlation, room_id, administrator_id))
            row = cursor.fetchone()
        return self._admin(row)

    def leave(self, room_id: UUID, *, actor: str = "steward", correlation_id: UUID | None = None) -> dict[str, Any]:
        """Explicitly leave room administration while preventing administratorless rooms."""
        return self.revoke_admin(room_id, actor, actor=actor, correlation_id=correlation_id)
