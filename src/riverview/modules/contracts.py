from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODULE_CONTRACT_VERSION = "riverview-core-contract-1.0"


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    module_id: str
    display_name: str
    module_version: str
    required_core_contract: str
    module_type: str
    events_consumed: tuple[str, ...] = ()
    events_emitted: tuple[str, ...] = ()
    actions_requested: tuple[str, ...] = ()
    projections_read: tuple[str, ...] = ()
    capabilities_registered: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    storage_owner: str = "module"
    dependencies: tuple[str, ...] = ()
    authority: tuple[str, ...] = ()
    lifecycle: tuple[str, ...] = ("discover", "enable", "disable", "health", "upgrade")
    recovery: str = "bounded failure and diagnostic checkpoint"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModuleManifest:
        required = {"module_id", "display_name", "module_version", "required_core_contract", "module_type"}
        if not required <= data.keys():
            raise ValueError("RIV-MOD-0001: module manifest is incomplete.")
        if any("secret" in str(key).casefold() or "token" in str(key).casefold() for key in data):
            raise ValueError("RIV-MOD-0001: secrets are not valid module manifest fields.")
        kwargs = {key: tuple(data.get(key, ())) for key in ("events_consumed", "events_emitted", "actions_requested", "projections_read", "capabilities_registered", "routes", "diagnostics", "dependencies", "authority", "lifecycle")}
        return cls(**{key: data[key] for key in required}, **kwargs, storage_owner=str(data.get("storage_owner", "module")), recovery=str(data.get("recovery", "bounded failure and diagnostic checkpoint")))

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in ("module_id", "display_name", "module_version", "required_core_contract", "module_type", "events_consumed", "events_emitted", "actions_requested", "projections_read", "capabilities_registered", "routes", "diagnostics", "storage_owner", "dependencies", "authority", "lifecycle", "recovery")}
