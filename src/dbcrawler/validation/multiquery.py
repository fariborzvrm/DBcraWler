"""Multi-query validation (plan.md Phase 3 §3).

For complex questions (joins/aggregations), generate an independent
alternative SQL with a different join/aggregation strategy, run it
through the same guardrails+execution path, and compare results.
"""

import math
from typing import Any

import sqlglot
from pydantic import BaseModel
from sqlglot import exp

from dbcrawler.guardrails.executor import QueryResult

ALT_SQL_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "explanation": {"type": "string"},
    },
    "required": ["sql", "explanation"],
    "additionalProperties": False,
}

ALT_PROMPT = """You are a senior SQL engineer. The first SQL answer for a
question is given below. Write a second, INDEPENDENT SQL query that answers
the same question through a materially different route where possible:
different join path, different aggregation decomposition (e.g. aggregate the
detail table instead of the pre-aggregated column), different subquery shape.
Return the same dialect (PostgreSQL SELECT-only).
"""


def is_complex(sql: str) -> bool:
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except sqlglot.errors.ParseError:
        return False
    tables = {t.name.lower() for t in parsed.find_all(exp.Table)}
    return bool(parsed.find(exp.Join)) or len(tables) > 1


def generate_alternative(
    client: Any,
    question: str,
    sql: str,
    schema_text: str = "",
) -> dict:
    user_prompt = (
        f"DATABASE SCHEMA:\n{schema_text}\n\n"
        f"QUESTION: {question}\n\nFIRST SQL:\n{sql}\n\n"
        "Return the alternative SQL."
    )
    return client.generate_structured(
        ALT_PROMPT, user_prompt, ALT_SQL_SCHEMA, "alt_sql"
    )


class MultiQueryResult(BaseModel):
    ran: bool = False
    agree: bool = False
    first_sql: str = ""
    second_sql: str = ""
    detail: str = ""


def _canonical(value: Any) -> str:
    if isinstance(value, float) and math.isfinite(value):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _row_signature(row: dict) -> tuple[str, ...]:
    return tuple(sorted(f"{key}={_canonical(value)}" for key, value in row.items()))


def compare_results(first: "QueryResult", second: "QueryResult") -> MultiQueryResult:
    a = {_row_signature(row) for row in first.rows}
    b = {_row_signature(row) for row in second.rows}
    agree = a == b
    detail = (
        "row sets match"
        if agree
        else f"row sets differ: {len(a)} vs {len(b)} distinct row signatures"
    )
    return MultiQueryResult(
        ran=True,
        agree=agree,
        first_sql=first.sql,
        second_sql=second.sql,
        detail=detail,
    )
