"""Typed, PostgreSQL-authoritative MCP mailbox."""

from .store import MailboxMessage, MailboxResponse, MailboxStore

__all__ = ["MailboxMessage", "MailboxResponse", "MailboxStore"]
