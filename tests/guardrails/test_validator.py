from dbcrawler.guardrails.validator import validate_sql


def test_empty_sql():
    result = validate_sql("")
    assert not result.is_valid
    assert "empty" in result.errors[0].lower()


def test_syntax_error_is_reported_not_raised():
    result = validate_sql("SELECT FROM WHERE ;;;")
    assert not result.is_valid
    assert result.errors


def test_valid_sql_roundtrip():
    result = validate_sql(
        "SELECT c.name FROM customers c WHERE c.country = 'Germany' LIMIT 5",
        dialect="postgres",
    )
    assert result.is_valid
    assert result.statements == [
        "SELECT c.name FROM customers AS c WHERE c.country = 'Germany' LIMIT 5"
    ]


def test_multistatement_parsed_with_count():
    result = validate_sql("SELECT 1; SELECT 2")
    assert result.is_valid
    assert len(result.statements) == 2
