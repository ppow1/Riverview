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
    """Reject collisions, invalid bounds, missing dependencies, and cycles."""

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

    dependency_counts: dict[str, int] = {}
    dependents = {service_id: [] for service_id in ids}
    for node in nodes:
        unique_dependencies = set(node.dependencies)
        dependency_counts[node.service_id] = len(unique_dependencies)
        for dependency in unique_dependencies:
            dependents[dependency].append(node.service_id)

    ready = [service_id for service_id, count in dependency_counts.items() if count == 0]
    validated = 0
    while ready:
        service_id = ready.pop()
        validated += 1
        for dependent in dependents[service_id]:
            dependency_counts[dependent] -= 1
            if dependency_counts[dependent] == 0:
                ready.append(dependent)
    if validated != len(nodes):
        raise ValueError("RIV-INF-0001: service dependency cycle.")
    return nodes
