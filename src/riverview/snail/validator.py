from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Validation:
    accepted: bool
    code: str
    reason: str


ELSE_TOKEN = re.compile(r"(?im)(?<![\w-])else(?![\w-])")


def validate_action(action: dict[str, Any], state: dict[str, Any], config: dict[str, Any]) -> Validation:
    required = {"operation_id", "operation_type", "target", "command", "evidence_ids", "state_changing"}
    missing = sorted(required - action.keys())
    if missing:
        return Validation(False, "MALFORMED_ACTION", f"missing: {', '.join(missing)}")
    if action["target"] != config["target"]:
        return Validation(False, "TARGET_REJECTED", "target outside campaign")
    if action["operation_type"] not in config["allowed_operations"]:
        return Validation(False, "OPERATION_REJECTED", "operation is not allowlisted")
    if action["operation_type"] in config.get("prohibited_operations", []):
        return Validation(False, "DESTRUCTIVE_OPERATION_REJECTED", "operation is prohibited")
    if not isinstance(action["command"], str) or not action["command"].strip():
        return Validation(False, "SYNTAX_REJECTED", "command must be non-empty text")
    if state["snail_state"] not in {"READY", "VALIDATING", "RECOVERING"}:
        return Validation(False, "STATE_REJECTED", "controller is not executable")
    if action.get("language", "").lower() == "powershell" and ELSE_TOKEN.search(action["command"]):
        return Validation(False, "VALIDATION_REJECTED_NO_ELSE_POLICY", "PowerShell else token prohibited")
    if action["state_changing"] and not action["evidence_ids"]:
        return Validation(False, "EVIDENCE_REQUIRED", "state change needs evidence")
    unknown_evidence = set(action["evidence_ids"]) - set(state.get("evidence_refs", []))
    if unknown_evidence:
        return Validation(False, "EVIDENCE_UNKNOWN", "operation cites evidence outside durable state")
    if action["operation_id"] in state.get("verified_operation_ids", []):
        return Validation(False, "DUPLICATE_OPERATION_REJECTED", "operation already verified")
    operation_type = action["operation_type"]
    if operation_type in config.get("steward_gated_operations", []):
        if not state.get("steward_authorization"):
            return Validation(False, "STEWARD_GATE_REQUIRED", "operation requires the specific Steward decision defined by the campaign contract")
    if action.get("destructive"):
        standing = config.get("campaign_go_authorized", False) and operation_type in config.get("standing_authorization_operations", [])
        if not standing and not state.get("steward_authorization"):
            return Validation(False, "STEWARD_GATE_REQUIRED", "operation is outside standing campaign authority")
    return Validation(True, "ACCEPTED", "deterministic validation passed")


REASONING_FIELDS = {
    "interpretation", "evidence_used", "hypothesis", "proposed_action", "expected_result",
    "pass_condition", "fail_condition", "timeout", "confidence", "escalation_required",
}


def validate_reasoning(value: Any) -> Validation:
    if not isinstance(value, dict):
        return Validation(False, "MALFORMED_REASONING", "response must be an object")
    missing = sorted(REASONING_FIELDS - value.keys())
    if missing:
        return Validation(False, "MALFORMED_REASONING", f"missing: {', '.join(missing)}")
    if not isinstance(value["evidence_used"], list) or not isinstance(value["confidence"], (int, float)):
        return Validation(False, "MALFORMED_REASONING", "field types invalid")
    if not 0 <= value["confidence"] <= 1:
        return Validation(False, "MALFORMED_REASONING", "confidence outside 0..1")
    return Validation(True, "ACCEPTED", "reasoning contract satisfied")
