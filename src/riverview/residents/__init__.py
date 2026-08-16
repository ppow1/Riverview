"""Reference-only resident identity and role boundaries."""

from .gateway import ResidentConversationGateway, ResidentProfile, ResidentSession
from .registry import ResidentRecord, ResidentRegistry

__all__ = ["ResidentConversationGateway", "ResidentProfile", "ResidentRecord", "ResidentRegistry", "ResidentSession"]
