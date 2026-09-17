"""Read-only sandboxed execution layer (Phase 2).

Only ever called with `enforced_sql` from an allowed GuardrailResult.
Defense layers: application guardrails run before this; the connection
uses the SELECT-only app_readonly user (ADR-001) and every execution
runs in a transaction that is explicitly rolled back.
"""

import logging
import time
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from dbcrawler.config.settings import Settings

logger = logging.getLogger("dbcrawler.guardrails.executor")


class ExecutionBlocked(Exception):
    """Raised when the EXPLAIN scan-row cap rejects the query."""

    def __init__(self, violations: list[str]):
        super().__init__("; ".join(violations))
        self.violations = violations


class QueryResult(BaseModel):
    sql: str
    rows: list[dict] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    execution_time_ms: float = 0.0
    explain_plan: str = ""
    validation: dict | None = None


def _walk_plan(plan: dict[str, Any]) -> list[str]:
    nodes: list[str] = []

    def visit(node: dict[str, Any]) -> None:
        node_type = node.get("Node Type", "?")
        relation = node.get("Relation Name")
        nodes.append(
            f"{node_type}"
            + (f" on {relation}" if relation else "")
            + f" (rows~{node.get('Plan Rows', '?')})"
        )
        for child in node.get("Plans", []):
            visit(child)

    visit(plan)
    return nodes


def _parse_explain_json(rows: Any) -> dict[str, Any]:
    # psycopg returns the FORMAT JSON payload as a list of dicts with key "Plan".
    import json

    payload = rows or []
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict) and "Plan" in first:
            return first["Plan"]
        if isinstance(first, str):
            return json.loads(first)
    if isinstance(payload, str):
        return json.loads(payload)
    return {}


def estimated_scan_rows(engine: Any, sql: str) -> tuple[int, str]:
    """Return (estimated scanned rows, plan description) via EXPLAIN (FORMAT JSON)."""
    with engine.connect() as conn:
        raw = conn.execute(text(f"EXPLAIN (FORMAT JSON) {sql}")).scalar()
    plan = _parse_explain_json(raw)

    estimated = 0

    def visit(node: dict[str, Any]) -> None:
        nonlocal estimated
        if (
            node.get("Node Type", "").endswith("Scan")
            or node.get("Node Type") == "Function Scan"
        ):
            estimated += int(node.get("Plan Rows") or 0)
        for child in node.get("Plans", []):
            visit(child)

    visit(plan)
    return estimated, "\n".join(_walk_plan(plan))


def execute_sql(
    sql: str,
    settings: Settings | None = None,
    validation: dict | None = None,
) -> QueryResult:
    """Execute guardrail-approved SQL in a rollback transaction.

    Raises ExecutionBlocked when the EXPLAIN row-scan cap rejects the plan.
    """
    settings = settings or Settings()
    engine = create_engine(settings.db_url, future=True)
    try:
        estimated, plan_desc = estimated_scan_rows(engine, sql)
        if (
            settings.guardrail_enable_scan_cap
            and estimated > settings.guardrail_max_scan_rows
        ):
            violations = [
                (
                    "blocked: EXPLAIN estimates "
                    f"{estimated} scanned rows, cap is {settings.guardrail_max_scan_rows}"
                )
            ]
            logger.warning("GUARDRAIL BLOCK (scan cap): %s | %s", sql, violations)
            raise ExecutionBlocked(violations)

        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                start = time.perf_counter()
                cursor = conn.execute(text(sql))
                columns = list(cursor.keys())
                fetch_count = settings.guardrail_max_limit_rows + 1
                fetched = cursor.fetchmany(fetch_count)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
            finally:
                transaction.rollback()

        truncated = len(fetched) > settings.guardrail_max_limit_rows
        rows = [
            dict(zip(columns, row))
            for row in fetched[: settings.guardrail_max_limit_rows]
        ]
        result = QueryResult(
            sql=sql,
            rows=rows,
            row_count=len(fetched) - (1 if truncated else 0),
            truncated=truncated,
            execution_time_ms=round(elapsed_ms, 2),
            explain_plan=plan_desc,
            validation=validation,
        )
        logger.info(
            "Executed SQL: rows=%s truncated=%s time=%.2fms",
            result.row_count,
            truncated,
            result.execution_time_ms,
        )
        return result
    finally:
        engine.dispose()
