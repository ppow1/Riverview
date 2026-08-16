from riverview.infrastructure.observability import project_observability

PRIVATE_KEYS = {"payload", "content", "transcript", "artifact", "secret", "token"}


def _mapping_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key
            for nested in value.values()
            for key in _mapping_keys(nested)
        }
    if isinstance(value, (list, tuple)):
        return {key for nested in value for key in _mapping_keys(nested)}
    return set()


def test_private_keys_are_removed_from_nested_mappings_and_sequences() -> None:
    view = project_observability(
        services=(
            {
                "service": "river",
                "status": {
                    "state": "healthy",
                    "checks": [
                        {"name": "queue", "payload": "private", "latency_ms": 4},
                        ({"content": "private", "result": "ok"},),
                    ],
                    "transcript": "private",
                },
                "artifact": {"secret": "private"},
            },
        ),
        providers=({"provider": "local", "details": [{"token": "private", "ready": True}]},),
        diagnostics=({"diagnostic": "bounded", "context": {"secret": "private", "code": 17}},),
    )

    assert PRIVATE_KEYS.isdisjoint(_mapping_keys(view))
    assert view["services"][0] == {
        "service": "river",
        "status": {
            "state": "healthy",
            "checks": [
                {"name": "queue", "latency_ms": 4},
                ({"result": "ok"},),
            ],
        },
    }
    assert view["providers"][0] == {"provider": "local", "details": [{"ready": True}]}
    assert view["diagnostics"][0] == {"diagnostic": "bounded", "context": {"code": 17}}
    assert view["private_payloads_excluded"] is True


def test_private_key_matching_is_case_insensitive_at_any_depth() -> None:
    view = project_observability(
        services=({"service": "river", "metadata": [{"TOKEN": "private", "Payload": "private", "uptime": 12}]},),
        providers=(),
        diagnostics=(),
    )

    assert view["services"][0] == {"service": "river", "metadata": [{"uptime": 12}]}
