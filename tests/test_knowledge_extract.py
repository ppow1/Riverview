from riverview.knowledge import extract_candidates


def test_extraction_preserves_explicit_and_ambiguous_states() -> None:
    rows=extract_candidates([{"text":"Use bounded retrieval","kind":"source_explicit_decision","source_ref":"turn:1","timestamp":"2026-08-15","confidence":"1"},{"text":"Maybe add voice","kind":"idea","source_ref":"turn:2","timestamp":"2026-08-15","confidence":"0.4","ambiguity":"requires scope"}],project="CueMastery")
    assert [x.kind for x in rows] == ["source_explicit_decision","idea"]
    assert rows[1].ambiguity == "requires scope"
