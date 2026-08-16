"""Software-discoverable Riverview service topology and startup contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServiceNode:
    service_id: str
    host: str
    port: int | None
    dependencies: tuple[str, ...]
    startup: str
    health: str
    data_owner: str
    config_owner: str


def validate_topology(nodes: tuple[ServiceNode, ...]) -> tuple[ServiceNode, ...]:
    """Reject duplicate ports, owners, missing dependencies, and invalid bounds."""

    ids = {node.service_id for node in nodes}
    if len(ids) != len(nodes):
        raise ValueError("RIV-INF-0001: service identity collision.")
    ports: dict[tuple[str, int], str] = {}
    for node in nodes:
        if not node.service_id.strip() or not node.host.strip() or not node.startup.strip() or not node.health.strip():
            raise ValueError("RIV-INF-0001: service topology fields are required.")
        if node.port is not None:
            if not 1024 <= node.port <= 65535:
                raise ValueError("RIV-INF-0001: service port is outside the bounded range.")
            key = (node.host, node.port)
            if key in ports:
                raise ValueError("RIV-INF-0001: service port collision.")
            ports[key] = node.service_id
        if any(dependency not in ids for dependency in node.dependencies):
            raise ValueError("RIV-INF-0001: service dependency is not in the topology.")
    return nodes
