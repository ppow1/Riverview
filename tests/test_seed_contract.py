"""Pure contract checks for the bounded Steward seed surface."""

from riverview.grace.seeds import MAX_SEED_BYTES


def test_seed_bound_is_finite() -> None:
    assert MAX_SEED_BYTES == 8_000
