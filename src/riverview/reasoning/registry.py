"""Durable provider-neutral reasoning registration."""

from __future__ import annotations

import json

from riverview.database import connect

from .contracts import ReasoningProvider


class ReasoningProviderRegistry:
    def register(self, provider: ReasoningProvider, *, provenance: dict[str, str] | None = None) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO reasoning_providers
                (participant_id,provider_id,provider_type,role,capabilities,eligible_classifications,contract_version,health,capacity,provenance)
                VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s::jsonb)
                ON CONFLICT(participant_id) DO UPDATE SET provider_id=EXCLUDED.provider_id,
                provider_type=EXCLUDED.provider_type,role=EXCLUDED.role,capabilities=EXCLUDED.capabilities,
                eligible_classifications=EXCLUDED.eligible_classifications,contract_version=EXCLUDED.contract_version,
                health=EXCLUDED.health,capacity=EXCLUDED.capacity,provenance=EXCLUDED.provenance,
                updated_at=now()""",
                (provider.participant_id, provider.provider_id, provider.provider_type, provider.role,
                 json.dumps(provider.capabilities), json.dumps(provider.eligible_classifications), provider.contract_version,
                 provider.health, provider.capacity, json.dumps(provenance or {})),
            )

    def available(self, request_classification: str) -> list[dict[str, object]]:
        if not request_classification.strip():
            raise ValueError("RIV-REASON-0001: request classification is required.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT participant_id,provider_id,provider_type,role,health,capacity,contract_version
                   FROM reasoning_providers WHERE enabled=true AND health='healthy' AND capacity > 0
                   AND eligible_classifications ? %s ORDER BY capacity DESC,participant_id""",
                (request_classification,),
            )
            return [dict(zip(("participant_id", "provider_id", "provider_type", "role", "health", "capacity", "contract_version"), row, strict=True)) for row in cursor.fetchall()]
