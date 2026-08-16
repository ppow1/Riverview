import pytest

from riverview.infrastructure.topology import ServiceNode, validate_topology


def service(service_id: str, dependencies: tuple[str, ...] = ()) -> ServiceNode:
    return ServiceNode(
        service_id,
        "127.0.0.1",
        None,
        dependencies,
        "process",
        "/health",
        service_id,
        "config",
    )


@pytest.mark.parametrize(
    "nodes",
    [
        (service("river", ("relay",)), service("relay", ("river",))),
        (service("river", ("river",)),),
        (
            service("river", ("relay",)),
            service("relay", ("grace",)),
            service("grace", ("river",)),
        ),
    ],
)
def test_dependency_cycles_fail_closed_with_stable_diagnostic(
    nodes: tuple[ServiceNode, ...],
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^RIV-INF-0001: service dependency cycle\.$",
    ):
        validate_topology(nodes)


def test_acyclic_dependency_graph_is_returned_unchanged() -> None:
    nodes = (
        service("river"),
        service("relay", ("river",)),
        service("grace", ("river", "relay")),
    )

    assert validate_topology(nodes) is nodes


def test_missing_dependency_validation_precedes_cycle_detection() -> None:
    nodes = (
        service("river", ("relay",)),
        service("relay", ("river", "missing")),
    )

    with pytest.raises(
        ValueError,
        match=r"^RIV-INF-0001: service dependency is not in the topology\.$",
    ):
        validate_topology(nodes)
