import pytest

from riverview.knowledge.search import KnowledgeSearch


def test_search_rejects_unknown_classification() -> None:
    with pytest.raises(ValueError, match="classification"):
        KnowledgeSearch().search("handoff", classification="undercurrent")
