from dbcrawler.validation.multiquery import compare_results, is_complex


def test_compare_results_agree():
    a = "SELECT 1"
    b = "SELECT 2"
    fa = _fr(a, [{"count": 3}])
    fb = _fr(b, [{"count": 3.0}])
    result = compare_results(fa, fb)
    assert result.ran
    assert result.agree


def test_compare_results_differ():
    fa = _fr("SELECT 1", [{"count": 3}])
    fb = _fr("SELECT 2", [{"count": 4}])
    result = compare_results(fa, fb)
    assert not result.agree


def _fr(sql, rows, row_count=1):
    from dbcrawler.guardrails.executor import QueryResult

    return QueryResult(sql=sql, rows=rows, row_count=row_count)


def test_is_complex_join():
    assert is_complex(
        "SELECT * FROM customers c JOIN orders o ON o.customer_id = c.customer_id"
    )
    assert not is_complex("SELECT * FROM customers WHERE country = 'Germany'")
