"""Explicit bounded extension manifest and registry contracts."""

from .contracts import MODULE_CONTRACT_VERSION, ModuleManifest
from .registry import ModuleRegistry

__all__ = ["MODULE_CONTRACT_VERSION", "ModuleManifest", "ModuleRegistry"]
