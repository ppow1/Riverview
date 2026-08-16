# RIV-RES-0002 — Resident room/session boundary

Resident room turns require an authoritative in-process room, admitted resident
IDs, bounded classification, automatically initialized resident sessions, an
eligible provider, and one preserved correlation ID. Diagnostics contain only
bounded IDs/types and never resident payloads or credentials.

Recovery: validate the room and participant set, select the configured local
provider, initialize sessions through the resident gateway, run one ordered
round, and preserve the room snapshot. A failed provider turn must not transfer
authority or create recursive resident work.
