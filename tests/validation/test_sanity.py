from dbcrawler.guardrails.executor import QueryResult
from dbcrawler.validation.sanity import check_result_sanity


def test_empty_rows_flagged():
    result = check_result_sanity(QueryResult(sql="SELECT 1"))
    checks = [f.check for f in result.findings if not f.passed]
    assert "has_rows" in checks
    assert result.pass_rate < 1.0


def test_normal_rows_no_findings():
    rows = [{"name": "A", "count": 3}, {"name": "B", "count": 0}]
    result = check_result_sanity(QueryResult(sql="SELECT", rows=rows, row_count=2))
    assert all(f.passed for f in result.findings)
    assert result.pass_rate == 1.0


def test_null_heavy_column_flagged():
    rows = [{"email": None}, {"email": None}, {"email": "x@y.z"}]
    result = check_result_sanity(QueryResult(sql="SELECT", rows=rows, row_count=3))
    checks = [f.check for f in result.findings if not f.passed]
    assert "null_heavy" in checks


def test_fractional_count_flagged():
    rows = [{"n_orders": 2.5}, {"n_orders": 3.1}]
    result = check_result_sanity(QueryResult(sql="SELECT", rows=rows, row_count=2))
    checks = [f.check for f in result.findings if not f.passed]
    assert "magnitude" in checks


def test_plausible_revenue_not_flagged():
    rows = [{"revenue": 12345.67}]
    result = check_result_sanity(QueryResult(sql="SELECT", rows=rows, row_count=1))
    assert all(f.passed for f in result.findings)
