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
    if state["snail_state"] not in {"READY", "VALIDATING", "RECOVERING"}:
        return Validation(False, "STATE_REJECTED", "controller is not executable")
    if action.get("language", "").lower() == "powershell" and ELSE_TOKEN.search(action["command"]):
        return Validation(False, "VALIDATION_REJECTED_NO_ELSE_POLICY", "PowerShell else token prohibited")
    if action["state_changing"] and not action["evidence_ids"]:
        return Validation(False, "EVIDENCE_REQUIRED", "state change needs evidence")
    if action["operation_id"] in state.get("verified_operation_ids", []):
        return Validation(False, "DUPLICATE_OPERATION_REJECTED", "operation already verified")
    if action.get("destructive") and not state.get("steward_authorization"):
        return Validation(False, "STEWARD_GATE_REQUIRED", "destructive operation lacks authority")
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
