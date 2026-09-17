from dbcrawler.guardrails.guardrails import (
    _max_nested_select_depth,
    check_guardrails,
)
from dbcrawler.guardrails.validator import validate_sql


def test_validate_sql_syntax_error():
    result = validate_sql("SELEC * FROM customers WHERE ;")
    assert not result.is_valid
    assert result.errors


def test_validate_sql_empty():
    assert not validate_sql("   ").is_valid


def test_validate_sql_valid_and_parsed():
    result = validate_sql("SELECT name FROM customers WHERE country = 'Germany'")
    assert result.is_valid
    assert not result.errors
    assert len(result.parsed) == 1


def test_dml_write_blocked():
    result = check_guardrails("DELETE FROM customers WHERE id = 1")
    assert not result.allowed
    assert any("DML" in v for v in result.violations)
    assert result.enforced_sql == ""


def test_ddl_blocked():
    result = check_guardrails("DROP TABLE customers")
    assert not result.allowed
    assert any("DDL" in v for v in result.violations)


def test_multi_statement_blocked():
    result = check_guardrails("SELECT 1; DROP TABLE customers")
    assert not result.allowed
    assert any("single statement" in v for v in result.violations)


def test_unknown_command_fail_closed():
    result = check_guardrails("VACUUM customers")
    assert not result.allowed


def test_no_limit_injected():
    result = check_guardrails("SELECT name FROM customers")
    assert result.allowed
    assert result.enforced_sql.lower().endswith("limit 1000")


def test_large_limit_clamped():
    result = check_guardrails("SELECT name FROM customers LIMIT 99999999")
    assert result.allowed
    assert result.enforced_sql.lower().endswith("limit 1000")


def test_subquery_depth_ok():
    sql = (
        "SELECT * FROM ("
        "SELECT * FROM ("
        "SELECT * FROM customers LIMIT 1"
        ") a LIMIT 10"
        ") b LIMIT 10"
    )
    result = check_guardrails(sql)
    assert result.allowed


def test_subquery_depth_too_deep():
    base = "SELECT * FROM customers"
    levels = [f"SELECT * FROM ({base}) s LIMIT 10"]
    levels.append(f"SELECT * FROM ({levels[-1]}) s LIMIT 10")
    levels.append(f"SELECT * FROM ({levels[-1]}) s LIMIT 10")
    levels.append(f"SELECT * FROM ({levels[-1]}) s LIMIT 10")
    sql = f"SELECT * FROM ({levels[-1]}) s LIMIT 10"
    result = check_guardrails(sql)
    assert not result.allowed
    assert any("depth" in v for v in result.violations)


def test_max_nested_select_depth_counts_cte():
    sql = "WITH a AS (SELECT 1) SELECT * FROM a"
    depth = _max_nested_select_depth(validate_sql(sql).parsed[0])
    assert depth == 1
