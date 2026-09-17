"""Offline evaluation-suite tests: no DB or LLM needed."""

import sqlglot

from dbcrawler.evaluation.dataset import DATASET_PATH, load_dataset
from dbcrawler.evaluation.metrics import (
    CaseOutcome,
    EvaluationReport,
    normalize_sql,
    rows_equivalent,
    summary_lines,
)
from dbcrawler.guardrails import check_guardrails


class FakeSettings:
    guardrail_block_ddl = True
    guardrail_block_dml = True
    guardrail_max_subquery_depth = 3
    guardrail_max_limit_rows = 1000


FAKE_SETTINGS = FakeSettings()


class FakeSettings:
    guardrail_block_ddl = True
    guardrail_block_dml = True
    guardrail_max_subquery_depth = 3
    guardrail_max_limit_rows = 1000


def test_dataset_counts_at_least_50_questions():
    dataset = load_dataset(DATASET_PATH)
    natural = len(dataset.golden_queries) + len(dataset.ambiguous_questions) + len(
        dataset.unanswerable_questions
    )
    assert natural >= 50
    assert len(dataset.golden_queries) >= 40


def test_dataset_categories_covered():
    dataset = load_dataset(DATASET_PATH)
    categories = {item.category for item in dataset.golden_queries}
    assert {"lookup", "join", "aggregation", "date_range", "top_n"} <= categories


def test_golden_sql_is_parsable_single_select():
    dataset = load_dataset(DATASET_PATH)
    for item in dataset.golden_queries:
        parsed = sqlglot.parse(sql=item.sql, dialect="postgres")
        assert len(parsed) == 1, item.sql
        assert parsed[0].find(sqlglot.exp.Select) is not None, item.sql


def test_dangerous_statements_are_blocked():
    dataset = load_dataset(DATASET_PATH)
    for dangerous in dataset.dangerous_statements:
        result = check_guardrails(dangerous.sql, settings=FAKE_SETTINGS)
        assert not result.allowed, dangerous.sql


def test_every_golden_has_snapshot():
    import json

    dataset = load_dataset(DATASET_PATH)
    with open("data/evaluation/golden_results.json", encoding="utf-8") as handle:
        snapshot = json.load(handle)
    for item in dataset.golden_queries:
        assert item.question in snapshot, item.question


def test_snapshot_rows_non_empty():
    import json

    with open("data/evaluation/golden_results.json", encoding="utf-8") as handle:
        snapshot = json.load(handle)
    empty = [q for q, v in snapshot.items() if not v["rows"]]
    assert empty == [], empty


def test_normalize_sql_ignores_spacing_and_case():
    left = "SELECT count(*) FROM Customers;"
    right = "SELECT COUNT(*) FROM customers"
    assert normalize_sql(left) == normalize_sql(right)
    assert normalize_sql("select a ,b") == normalize_sql("SELECT a,b")


def test_rows_equivalent_detects_match_and_mismatch():
    match = rows_equivalent([{"n": 2}, {"x": 1}], [{"count": "2"}, {"total": 1}])
    assert match
    assert not rows_equivalent([{"n": 3}], [{"n": 2}])
    assert rows_equivalent([{"a": 1, "b": 2}], [{"c": 1, "d": 2}])
    assert not rows_equivalent([{"a": 1}, {"a": 2}], [{"a": 1}])


def test_report_rates_safe_defaults():
    report = EvaluationReport()
    assert report.execution_accuracy is None
    assert report.hallucination_detection_rate is None
    report.golden_total = 10
    report.execution_matches = 8
    report.exact_matches = 4
    assert report.execution_accuracy == 0.8
    assert report.exact_match_rate == 0.4


def test_summary_lines_include_failures():
    report = EvaluationReport(
        golden_total=1,
        execution_matches=0,
        exact_matches=0,
        dangerous_total=1,
        dangerous_blocked=1,
        failures=[
            CaseOutcome(
                question="q",
                category="join",
                execution_match=False,
                detail="status=blocked",
            )
        ],
    )
    lines = summary_lines(report)
    assert any("execution accuracy" in line for line in lines)
    assert any("FAIL q" in line for line in lines)
