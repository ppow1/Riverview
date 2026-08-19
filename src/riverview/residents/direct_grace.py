"""Typed direct-Grace approval bridge into the canonical governed path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from riverview.grace.seeds import StewardSeedStore
from riverview.intake.authority import StewardAuthorityStore
from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Service


class DirectGraceApprovalError(ValueError):
    """Fail-closed direct-Grace approval or materialization failure."""


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
        specification = Comms5Service().store_specification({
            **context,
            "content": approval.content,
            "summary": approval.summary,
            "idempotency_key": f"direct-grace:specification:{approval.idempotency_key}",
            "formation_contract": approval.formation_contract,
        })
        specification_id = UUID(str(specification["specification"]["specification_id"]))
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
            "specification_version": specification["specification"]["version"],
            "specification_sha256": specification["specification"]["content_sha256"],
            "seed_id": str(seed_id),
            "objective_id": str(objective_id),
            "authority_id": str(authority["authority_id"]),
            "replay_safe": True,
        }
