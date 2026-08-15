"""Authoritative ChatGPT application/conversation binding and rollover registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from riverview.database import connect

CHECKPOINT = "RIV-COMMS-0004"
DESIGNATED_ROLE = "designated_reasoning"
DESIGNATED_CONSUMER = "chatgpt:riverview_001"
CONTRACT_VERSION = "riverview-comms-contract-1"
ALLOWED_ROLES = frozenset({DESIGNATED_ROLE, "steward_intake", "notification_reporting"})
ALLOWED_STATUSES = frozenset({"candidate", "initialized", "active", "retired"})


@dataclass(frozen=True, slots=True)
class BindingCandidate:
    binding_id: UUID
    role: str
    application_ref: str
    contract_version: str
    conversation_id: UUID
    conversation_ref: str
    consumer_id: str


class BindingRegistry:
    """Manage only named, verified, and explicitly activated Comms bindings."""

    def register_candidate(
        self,
        *,
        role: str,
        application_ref: str,
        contract_version: str,
        conversation_id: UUID,
        conversation_ref: str,
        consumer_id: str,
        reason: str,
    ) -> UUID:
        self._validate(role, application_ref, contract_version, conversation_id, conversation_ref, consumer_id, reason)
        binding_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO comms_bindings(
                    binding_id,role,application_ref,contract_version,conversation_id,
                    conversation_ref,consumer_id,status,verification_state,reason
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,'candidate','unverified',%s)
                ON CONFLICT(role,conversation_id,contract_version) DO NOTHING""",
                (binding_id, role, application_ref, contract_version, conversation_id, conversation_ref, consumer_id, reason),
            )
            cursor.execute(
                """SELECT binding_id FROM comms_bindings
                   WHERE role=%s AND conversation_id=%s AND contract_version=%s""",
                (role, conversation_id, contract_version),
            )
            return cursor.fetchone()[0]

    def verify(self, binding_id: UUID, evidence_refs: list[str]) -> None:
        refs = self._refs(evidence_refs)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE comms_bindings
                   SET status=CASE WHEN status='candidate' THEN 'initialized' ELSE status END,
                       verification_state='verified',verification_evidence=%s::jsonb,updated_at=now()
                 WHERE binding_id=%s AND status IN ('candidate','initialized')""",
                (json.dumps(refs), binding_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"{CHECKPOINT}: binding is missing or not verifiable")

    def activate(self, binding_id: UUID, *, confirmer: str) -> dict[str, object]:
        if confirmer != "steward":
            raise PermissionError(f"{CHECKPOINT}: only the Steward can activate a binding")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT binding_id,role,verification_state,status,conversation_id,consumer_id
                   FROM comms_bindings WHERE binding_id=%s FOR UPDATE""",
                (binding_id,),
            )
            row = cursor.fetchone()
            if row is None or row[2] != "verified" or row[3] not in {"initialized", "active"}:
                raise RuntimeError(f"{CHECKPOINT}: binding lacks verified activation evidence")
            if row[3] == "active":
                return self._active_row(cursor, row[1])
            cursor.execute(
                """SELECT binding_id FROM comms_bindings
                   WHERE role=%s AND status='active' AND binding_id<>%s FOR UPDATE""",
                (row[1], binding_id),
            )
            previous = cursor.fetchone()
            if previous:
                cursor.execute("UPDATE comms_bindings SET status='retired',retired_at=now(),updated_at=now() WHERE binding_id=%s", (previous[0],))
            cursor.execute(
                """UPDATE comms_bindings SET status='active',activated_at=COALESCE(activated_at,now()),updated_at=now(),replaced_binding_id=%s WHERE binding_id=%s""",
                (previous[0] if previous else None, binding_id),
            )
            return self._active_row(cursor, row[1])

    def resolve_active(self, role: str = DESIGNATED_ROLE) -> dict[str, object]:
        if role not in ALLOWED_ROLES:
            raise ValueError(f"{CHECKPOINT}: unsupported binding role")
        with connect() as connection, connection.cursor() as cursor:
            return self._active_row(cursor, role)

    def continuity_package(self, role: str = DESIGNATED_ROLE) -> dict[str, object]:
        binding = self.resolve_active(role)
        return {
            "project": "Riverview",
            "repository": "ppow1/Riverview",
            "role": binding["role"],
            "consumer_id": binding["consumer_id"],
            "application_ref": binding["application_ref"],
            "contract_version": binding["contract_version"],
            "conversation_id": str(binding["conversation_id"]),
            "conversation_ref": binding["conversation_ref"],
            "authority": {"postgresql": "operational state", "github": "source/history", "playwright": "wake only", "mcp": "typed data"},
            "required_reads": ["AI_HINTS.md", "Charter", "current roadmap", "Engineering Interaction Contract"],
        }

    @staticmethod
    def _validate(role: str, application_ref: str, contract_version: str, conversation_id: UUID, conversation_ref: str, consumer_id: str, reason: str) -> None:
        if role not in ALLOWED_ROLES or not application_ref.strip() or not contract_version.strip() or not consumer_id.strip() or not reason.strip():
            raise ValueError(f"{CHECKPOINT}: binding fields are invalid")
        if not str(conversation_id) in conversation_ref or not conversation_ref.startswith("https://chatgpt.com/"):
            raise ValueError(f"{CHECKPOINT}: conversation reference does not match its exact ID")

    @staticmethod
    def _refs(refs: list[str]) -> list[str]:
        if not refs or len(refs) > 8 or any(not item.strip() or len(item) > 240 for item in refs):
            raise ValueError(f"{CHECKPOINT}: verification evidence is outside bounds")
        return list(dict.fromkeys(refs))

    @staticmethod
    def _active_row(cursor, role: str) -> dict[str, object]:
        cursor.execute(
            """SELECT binding_id,role,application_ref,contract_version,conversation_id,
                      conversation_ref,consumer_id,status,verification_state,verification_evidence,
                      activated_at,replaced_binding_id
               FROM comms_bindings WHERE role=%s AND status='active' AND verification_state='verified'""",
            (role,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"{CHECKPOINT}: no verified active binding for role {role!r}")
        names = [item.name for item in cursor.description]
        return dict(zip(names, row, strict=True))
