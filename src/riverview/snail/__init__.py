"""SNAIL: durable, evidence-driven engineering campaign runtime."""

from .runtime import SnailRuntime
from .snapshot_anchors import install_snapshot_anchor_wrapper

install_snapshot_anchor_wrapper(SnailRuntime)

__all__ = ["SnailRuntime"]
