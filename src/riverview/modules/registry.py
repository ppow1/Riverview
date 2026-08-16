from __future__ import annotations

import json
from pathlib import Path

from .contracts import MODULE_CONTRACT_VERSION, ModuleManifest


class ModuleRegistry:
    def __init__(self, manifests: tuple[ModuleManifest, ...] = ()) -> None:
        self._modules: dict[str, ModuleManifest] = {}
        for manifest in manifests:
            self.register(manifest)

    def register(self, manifest: ModuleManifest) -> None:
        if manifest.module_id in self._modules:
            raise ValueError("RIV-MOD-0002: duplicate module identity.")
        if manifest.required_core_contract != MODULE_CONTRACT_VERSION:
            raise ValueError("RIV-MOD-0002: incompatible core contract; module remains disabled.")
        self._modules[manifest.module_id] = manifest

    def manifests(self) -> tuple[ModuleManifest, ...]:
        return tuple(self._modules.values())

    @classmethod
    def from_directory(cls, directory: Path) -> ModuleRegistry:
        manifests = tuple(ModuleManifest.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(directory.glob("*.json")))
        return cls(manifests)
