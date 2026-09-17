"""Runner integration test — requires local seeded Postgres (docker compose up)."""

import pytest
from sqlalchemy import create_engine

from dbcrawler.config.settings import Settings
from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.schema.models import SchemaTable
from dbcrawler.validation.runner import run_validation

FAXED = {"question": "How many customers are registered in Germany?", "score": 1.0}


class FakeClient:
    def generate_structured(self, system_prompt, user_prompt, schema, name):
        if name == "backtranslation":
            return {"question": FAXED["question"]}
        if name == "alignment":
            return {"score": FAXED["score"], "explanation": "same intent"}
        if name == "alt_sql":
            return {
                "sql": "SELECT country FROM customers LIMIT 3",
                "explanation": "alt",
            }
        raise AssertionError(f"unexpected call {name}")


def _db_available() -> bool:
    try:
        create_engine(Settings().db_url).connect().close()
    except Exception:  # noqa: BLE001
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="Postgres not reachable (docker compose up)"
)


def test_run_validation_simple_query():
    generated = GeneratedSQL(
        sql="SELECT COUNT(*) AS n FROM customers",
        explanation="counts customers",
        confidence=0.9,
        tables=["customers"],
        columns=["n"],
    )
    verified = run_validation(
        FakeClient(),
        Settings(),
        "How many customers are registered in Germany?",
        generated,
        enforced_sql="SELECT COUNT(*) AS n FROM customers LIMIT 1000",
        schema=type("S", (), {"tables": [SchemaTable(name="customers")]})(),
        run_multiquery=False,
    )
    assert verified.query_result is not None
    assert verified.query_result.row_count == 1
    assert verified.intent.alignment_score == 1.0
    assert verified.confidence.final > 0.8
