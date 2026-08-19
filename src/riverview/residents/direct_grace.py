"""Typed direct-Grace approval bridge into the canonical governed path."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from riverview.database import connect
from riverview.grace.seeds import StewardSeedStore
from riverview.intake.authority import StewardAuthorityStore
from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Service


class DirectGraceApprovalError(ValueError):
    """Fail-closed direct-Grace approval or materialization failure."""


_PROPOSAL_PATTERN = re.compile(
    r"<RIVERVIEW_SPECIFICATION_V1>\s*(?P<body>\{.*\})\s*</RIVERVIEW_SPECIFICATION_V1>",
    re.DOTALL,
)


def extract_typed_proposal(summary: str) -> dict[str, Any] | None:
    """Extract only Grace's explicit bounded specification envelope."""
    match = _PROPOSAL_PATTERN.search(summary)
    if match is None:
        return None
    if len(match.group("body")) > 12_000:
        raise DirectGraceApprovalError("RIV-GRC-0010: Grace specification envelope exceeds the bounded size.")
    try:
        value = json.loads(match.group("body"))
    except json.JSONDecodeError as exc:
        raise DirectGraceApprovalError("RIV-GRC-0010: Grace specification envelope is not valid JSON.") from exc
    if not isinstance(value, dict) or set(value) - {"content", "summary", "formation_contract", "seed_text", "classification"}:
        raise DirectGraceApprovalError("RIV-GRC-0010: Grace specification envelope contains unknown fields.")
    required = {"content", "summary", "formation_contract", "seed_text"}
    if not required <= set(value):
        raise DirectGraceApprovalError("RIV-GRC-0010: Grace specification envelope is incomplete.")
    if not all(isinstance(value[key], str) and value[key].strip() for key in ("content", "summary", "seed_text")):
        raise DirectGraceApprovalError("RIV-GRC-0010: Grace specification text is bounded and required.")
    if value.get("classification", "river") not in {"river", "internal"}:
        raise DirectGraceApprovalError("RIV-SEC-0001: Grace specification classification is unsupported.")
    try:
        StewardAuthorityStore.validate_formation_contract(value["formation_contract"])
    except Exception as exc:
        raise DirectGraceApprovalError(str(exc)) from exc
    return value


@dataclass(frozen=True, slots=True)
class DirectGraceApproval:
    """Exact approved specification and bounded formation context.

    This envelope is the authority-bearing boundary. Conversation text is
    never parsed into these fields.
    """

    content: str
    summary: str
    formation_contract: dict[str, Any]
    seed_text: str
    idempotency_key: str
    approval_operation_id: UUID
    correlation_id: UUID
    authenticated_principal: str
    explicit_steward_confirmation: bool
    specification_id: UUID | None = None
    specification_version: int | None = None
    specification_sha256: str | None = None
    classification: str = "river"

    @classmethod
    def from_payload(cls, value: Any, *, correlation_id: UUID) -> DirectGraceApproval:
        if not isinstance(value, dict):
            raise DirectGraceApprovalError("RIV-GRC-0010: direct Grace approval must be a typed object.")
        try:
            approval = cls(
                content=str(value["content"]),
                summary=str(value["summary"]),
                formation_contract=value["formation_contract"],
                seed_text=str(value["seed_text"]),
                idempotency_key=str(value["idempotency_key"]),
                approval_operation_id=UUID(str(value["approval_operation_id"])),
                correlation_id=correlation_id,
                authenticated_principal=str(value["authenticated_principal"]),
                explicit_steward_confirmation=value["explicit_steward_confirmation"],
                specification_id=UUID(str(value["specification_id"])) if value.get("specification_id") else None,
                specification_version=int(value["specification_version"]) if value.get("specification_version") is not None else None,
                specification_sha256=str(value["specification_sha256"]) if value.get("specification_sha256") else None,
                classification=str(value.get("classification", "river")),
            )
        except KeyError as exc:
            raise DirectGraceApprovalError(f"RIV-GRC-0010: direct Grace approval envelope is missing {exc.args[0]}.") from exc
        except (TypeError, ValueError) as exc:
            raise DirectGraceApprovalError("RIV-GRC-0010: direct Grace approval envelope is incomplete.") from exc
        if approval.authenticated_principal != "steward":
            raise DirectGraceApprovalError("RIV-GRC-0010: only the authenticated Steward may approve direct Grace work.")
        if approval.explicit_steward_confirmation is not True:
            raise DirectGraceApprovalError("RIV-GRC-0009: explicit Steward confirmation is required.")
        if approval.classification not in {"river", "internal"}:
            raise DirectGraceApprovalError("RIV-SEC-0001: direct Grace classification is unsupported.")
        if not approval.content.strip() or not approval.summary.strip() or not approval.seed_text.strip() or not approval.idempotency_key.strip():
            raise DirectGraceApprovalError("RIV-GRC-0010: approved specification fields are bounded and required.")
        try:
            StewardAuthorityStore.validate_formation_contract(approval.formation_contract)
        except Exception as exc:
            raise DirectGraceApprovalError(str(exc)) from exc
        return approval


class DirectGraceFormation:
    """Materialize one exact approved direct-Grace specification idempotently."""

    @staticmethod
    def materialize_proposal(proposal: dict[str, Any], *, correlation_id: UUID) -> dict[str, Any]:
        """Persist a typed proposal without granting authority."""
        content = str(proposal["content"])
        fingerprint = hashlib.sha256(json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        context = {
            "client_id": "operator-grace",
            "client_type": "resident_gateway",
            "client_name": "Grace",
            "client_version": "direct-grace-v1",
            "protocol_version": CONTRACT_VERSION,
            "authenticated_principal": "operator-session",
            "correlation_id": str(correlation_id),
            "classification": str(proposal.get("classification", "river")),
        }
        specification = Comms5Service().store_specification({
            **context,
            "content": content,
            "summary": str(proposal["summary"]),
            "idempotency_key": f"direct-grace:proposal:{fingerprint}",
            "formation_contract": proposal["formation_contract"],
        })
        stored = specification["specification"]
        specification_id = UUID(str(stored["specification_id"]))
        return {
            **proposal,
            "specification_id": str(specification_id),
            "specification_version": int(stored["version"]),
            "specification_sha256": str(stored["content_sha256"]),
            "approval_operation_id": str(uuid5(NAMESPACE_URL, f"riverview:direct-grace:approval:{specification_id}")),
            "idempotency_key": f"direct-grace:approval:{specification_id}:v{stored['version']}:{stored['content_sha256']}",
            "pending_status": "pending",
            "approval_question": "Do you approve this exact specification and authorize autonomous execution within its stated scope? Yes / No",
        }

    def authorize(self, approval: DirectGraceApproval) -> dict[str, Any]:
        context = {
            "client_id": "operator-grace",
            "client_type": "resident_gateway",
            "client_name": "Grace",
            "client_version": "direct-grace-v1",
            "protocol_version": CONTRACT_VERSION,
            "authenticated_principal": approval.authenticated_principal,
            "correlation_id": str(approval.correlation_id),
            "classification": approval.classification,
        }
        specification_id = approval.specification_id
        if specification_id is not None:
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT version,content,content_sha256,formation_contract,lifecycle_state FROM comms5_specifications WHERE specification_id=%s", (specification_id,))
                row = cursor.fetchone()
            if row is None or row[4] not in {"stored", "referenced"} or row[0] != approval.specification_version or row[2] != approval.specification_sha256 or row[1] != approval.content or row[3] != approval.formation_contract:
                raise DirectGraceApprovalError("RIV-GRC-0010: approved specification reference does not match its immutable content.")
            specification_version = row[0]
            specification_sha256 = row[2]
        else:
            specification = Comms5Service().store_specification({
                **context,
                "content": approval.content,
                "summary": approval.summary,
                "idempotency_key": f"direct-grace:specification:{approval.idempotency_key}",
                "formation_contract": approval.formation_contract,
            })
            specification_id = UUID(str(specification["specification"]["specification_id"]))
            specification_version = specification["specification"]["version"]
            specification_sha256 = specification["specification"]["content_sha256"]
        seed = Comms5Service().submit_steward_seed({
            **context,
            "seed_text": approval.seed_text,
            "idempotency_key": f"direct-grace:seed:{approval.idempotency_key}",
            "specification_id": str(specification_id),
        })
        seed_id = UUID(str(seed["seed_id"]))
        objective_id = StewardSeedStore().confirm_and_promote(
            seed_id,
            confirmer="steward",
            idempotency_key=f"direct-grace:promotion:{approval.idempotency_key}",
        )
        authority = StewardAuthorityStore().grant_for_promoted_seed(
            seed_id,
            objective_id,
            correlation_id=approval.correlation_id,
            approval_operation_id=approval.approval_operation_id,
            idempotency_key=f"steward-authority:direct-grace:promotion:{approval.idempotency_key}",
        )
        if authority is None:
            raise DirectGraceApprovalError("RIV-GRC-0010: direct Grace authority could not be materialized.")
        return {
            "specification_id": str(specification_id),
            "specification_version": specification_version,
            "specification_sha256": specification_sha256,
            "seed_id": str(seed_id),
            "objective_id": str(objective_id),
            "authority_id": str(authority["authority_id"]),
            "replay_safe": True,
        }
