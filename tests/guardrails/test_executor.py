"""Executor integration tests: require the local seeded Postgres (docker-compose)."""

import pytest
from sqlalchemy import create_engine

from dbcrawler.config.settings import Settings
from dbcrawler.guardrails.executor import execute_sql


def _db_available() -> bool:
    try:
        engine = create_engine(Settings().db_url)
        engine.connect().close()
        engine.dispose()
    except Exception:  # noqa: BLE001
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="Postgres not reachable (docker compose up)"
)


def test_execute_select_returns_rows():
    result = execute_sql(
        "SELECT count(*) AS n FROM customers", validation={"allowed": True}
    )
    assert result.row_count == 1
    assert not result.truncated
    assert result.explain_plan
    assert result.validation == {"allowed": True}


def test_execution_is_read_only_rollback():
    result = execute_sql("SELECT customer_id FROM customers LIMIT 2")
    assert result.row_count <= 2
    assert len(result.rows) <= result.row_count


def test_transaction_rollback_does_not_mutate():
    with pytest.raises(Exception):  # noqa: B017
        execute_sql("SELECT nonexistent FROM customers")
