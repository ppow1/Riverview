"""Master-roadmap contract tests. Version: 0.8.0"""

from riverview.roadmap import load_and_validate


def test_master_roadmap_is_detailed_and_valid() -> None:
    document,digest=load_and_validate()
    assert len(document["waypoints"])>=75
    assert len(digest)==64


def test_master_roadmap_contains_required_future_domains() -> None:
    document,_=load_and_validate()
    ids={item["id"] for item in document["waypoints"]}
    assert {"RV-005","RV-007","RV-008","RV-011","RV-013","RV-014","RV-016","RV-018"}<=ids