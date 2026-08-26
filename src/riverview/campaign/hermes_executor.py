"""Campaign Runner role execution through an authorized Hermes provider.

This adapter translates one fenced Campaign Runner work item into the existing
Riverview ReasoningRequest envelope.  Campaign Runner remains authoritative for
claims, attempts, leases, repairs, validation, and acceptance.  Hermes returns
only role evidence; it cannot self-accept a candidate.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Protocol

from riverview.relay.store import ClaimedWork

from riverview.reasoning.contracts import ReasoningRequest

CAMPAIGN_HERMES_VERSION = "campaign-hermes-role-v1"


class HermesCampaignProvider(Protocol):
    provider_id: str
    resource_class_ref: str

    def generate(self, request: ReasoningRequest): ...


class HermesCampaignExecutionError(RuntimeError):
    """A bounded Campaign Runner/Hermes translation or output failure."""


class HermesCampaignRoleExecutor:
    """Execute one already-fenced Campaign Runner role through Hermes."""

    def __init__(self, provider: HermesCampaignProvider) -> None:
        self.provider = provider

    def execute(self, work: ClaimedWork) -> dict[str, Any]:
        if not isinstance(work, ClaimedWork):
            raise HermesCampaignExecutionError("RIV-CAM-HERMES-0001: claimed work is required.")
        if work.correlation_id is None:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0002: canonical Campaign Runner correlation is missing."
            )
        request = self._request(work)
        response = self.provider.generate(request)
        if response.request_id != request.request_id or response.correlation_id != request.correlation_id:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0003: Hermes response correspondence failed."
            )
        if response.provider_id != self.provider.provider_id:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0004: Hermes provider identity changed in response."
            )
        result: dict[str, Any] = {
            "status": "succeeded",
            "schema_version": CAMPAIGN_HERMES_VERSION,
            "work_order_id": str(work.work_order_id),
            "correlation_id": str(work.correlation_id),
            "attempt_id": str(work.attempt_id) if work.attempt_id else None,
            "lease_generation": work.lease_generation,
            "fencing_token": str(work.fencing_token) if work.fencing_token else None,
            "worker_instance_id": str(work.worker_instance_id) if work.worker_instance_id else None,
            "role": work.role,
            "provider_id": response.provider_id,
            "resource_class_ref": self.provider.resource_class_ref,
            "response_id": str(response.response_id),
            "evidence_refs": list(response.evidence_refs),
            "summary": response.summary[:8_000],
        }
        for key in ("candidate_identity", "validation_basis_hash"):
            if key in work.parameters:
                result[key] = work.parameters[key]
        if work.role in {"validator", "revalidator"}:
            result.update(self._validation_payload(response.summary, work))
        else:
            result["validator_action_type"] = self._validator_action(work)
        return result

    @staticmethod
    def _request(work: ClaimedWork) -> ReasoningRequest:
        raw = work.parameters.get("hermes_request")
        if not isinstance(raw, Mapping):
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0005: hermes_request parameters are required."
            )
        try:
            request = ReasoningRequest(
                request_id=_uuid(raw["request_id"], "request_id"),
                correlation_id=work.correlation_id,
                request_type=raw["request_type"],
                instruction=raw["instruction"],
                context_refs=tuple(raw.get("context_refs", ())),
                classification=raw["classification"],
                required_output_schema=raw["required_output_schema"],
                evidence_requirements=tuple(raw.get("evidence_requirements", ())),
                expires_at=datetime.fromisoformat(str(raw["expires_at"])),
                allowed_authority=tuple(raw["allowed_authority"]),
                causation_id=_optional_uuid(raw.get("causation_id")),
                objective_id=_optional_uuid(raw.get("objective_id")),
                stage_id=_optional_uuid(raw.get("stage_id")),
                response_format=raw.get("response_format"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0006: hermes_request is malformed or expired."
            ) from exc
        return request

    @staticmethod
    def _validator_action(work: ClaimedWork) -> str:
        value = work.parameters.get("validator_action_type", "relay.noop")
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0007: validator action type is invalid."
            )
        return value.strip()

    @staticmethod
    def _validation_payload(summary: str, work: ClaimedWork) -> dict[str, Any]:
        try:
            value = json.loads(summary)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0008: validator output is not structured JSON."
            ) from exc
        if not isinstance(value, dict):
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0009: validator output is not an object."
            )
        required = (
            "verdict", "basis_hash", "result_version_hash", "evidence_refs",
            "findings_summary", "implementation_ref", "defects",
        )
        if any(key not in value for key in required):
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0010: validator output is incomplete."
            )
        if value["verdict"] not in {"PASS", "FAIL"}:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0011: validator verdict is unsupported."
            )
        if not isinstance(value["evidence_refs"], list) or not value["evidence_refs"]:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0012: validator evidence is missing."
            )
        if not isinstance(value["defects"], list):
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0013: validator defects are malformed."
            )
        expected_basis = work.parameters.get("validation_basis_hash")
        if expected_basis is not None and value["basis_hash"] != expected_basis:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0014: validator basis correspondence failed."
            )
        expected_candidate = work.parameters.get("candidate_identity")
        if expected_candidate is not None and value["result_version_hash"] != expected_candidate:
            raise HermesCampaignExecutionError(
                "RIV-CAM-HERMES-0015: validator candidate correspondence failed."
            )
        return {key: value[key] for key in required}


def _uuid(value: Any, name: str):
    from uuid import UUID

    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} is invalid") from exc


def _optional_uuid(value: Any):
    return None if value is None else _uuid(value, "optional UUID")


__all__ = ["CAMPAIGN_HERMES_VERSION", "HermesCampaignExecutionError", "HermesCampaignRoleExecutor"]
