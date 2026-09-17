from dbcrawler.api.history import InMemoryHistory, build_history_entry
from dbcrawler.confidence import ConfidenceBreakdown
from dbcrawler.guardrails.executor import QueryResult


def test_record_list_order_and_limit():
    store = InMemoryHistory(max_entries=3)
    for i in range(5):
        store.record(
            build_history_entry(
                f"id{i}",
                timestamp=i,
                question=f"q{i}",
                status="ok",
                generated=None,
                results={},
                confidence=None,
                warnings=[],
            )
        )
    listed = store.list()
    assert [e.id for e in listed] == ["id4", "id3", "id2"]
    assert store.get("id0") is None
    assert store.get("id4").question == "q4"


def test_set_feedback_missing():
    store = InMemoryHistory()
    assert store.set_feedback("nope", True) is None


def test_build_entry_includes_disagreement_warning():
    from types import SimpleNamespace

    multiquery = SimpleNamespace(agree=False, detail="row mismatch")
    query_result = QueryResult(sql="SELECT 1", rows=[], row_count=0)
    entry = build_history_entry(
        "x",
        0.0,
        "question",
        "ok",
        generated=SimpleNamespace(sql="SELECT 1", explanation="e"),
        results={"query_result": query_result, "multiquery": multiquery},
        confidence=ConfidenceBreakdown(final=0.5, llm_self_report=0.5),
        warnings=["w1"],
    )
    assert entry.warnings == ["w1", "multi-query disagreement: row mismatch"]
    assert entry.row_count == 0
