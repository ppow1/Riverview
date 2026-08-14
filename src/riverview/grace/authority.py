"""PostgreSQL-backed Grace authority contract.

Version: 0.1.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect


@dataclass(frozen=True)
class AuthorityDecision:
    capability: str
    requested_scope: str
    decision: str
    reason: str
    requires_steward: bool


class GraceAuthority:
    """Evaluate bounded Grace capabilities from authoritative PostgreSQL rules."""

    grace_id = "grace"

    def identity(self) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT grace_id,display_name,role,authority_version,enabled
                FROM grace_identities
                WHERE grace_id=%s
                """,
                (self.grace_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-GRC-0001: Grace identity is missing.")
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))

    def evaluate(
        self,
        capability: str,
        requested_scope: str,
        *,
        correlation_id: UUID | None = None,
        evidence_refs: list[str] | None = None,
        persist: bool = False,
    ) -> AuthorityDecision:
        if not capability or not requested_scope:
            raise ValueError("RIV-GRC-0001: capability and requested_scope are required.")

        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT effect,scope,requires_steward,reason
                FROM grace_authority_rules
                WHERE grace_id=%s AND capability=%s
                """,
                (self.grace_id, capability),
            )
            row = cursor.fetchone()

            if row is None:
                decision = AuthorityDecision(
                    capability=capability,
                    requested_scope=requested_scope,
                    decision="escalate",
                    reason="No explicit Grace authority rule exists for this capability.",
                    requires_steward=True,
                )
            else:
                effect, allowed_scope, requires_steward, reason = row
                if effect == "allow" and allowed_scope not in {"all", requested_scope}:
                    decision = AuthorityDecision(
                        capability=capability,
                        requested_scope=requested_scope,
                        decision="escalate",
                        reason=(
                            f"Capability is allowed only for scope {allowed_scope!r}; "
                            f"requested scope was {requested_scope!r}."
                        ),
                        requires_steward=True,
                    )
                else:
                    decision = AuthorityDecision(
                        capability=capability,
                        requested_scope=requested_scope,
                        decision=effect,
                        reason=reason,
                        requires_steward=requires_steward or effect != "allow",
                    )

            if persist:
                cursor.execute(
                    """
                    INSERT INTO grace_authority_decisions(
                        decision_id,grace_id,capability,requested_scope,decision,
                        reason,evidence_refs,correlation_id
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                    """,
                    (
                        uuid4(),
                        self.grace_id,
                        capability,
                        requested_scope,
                        decision.decision,
                        decision.reason,
                        json.dumps(evidence_refs or []),
                        correlation_id,
                    ),
                )

            return decision