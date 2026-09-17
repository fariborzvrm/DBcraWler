"""Guardrail middleware (Phase 2).

Runs strictly before any execution. Fail-closed by default: anything we
cannot positively identify as a single, read-only SELECT statement in a
safe shape is blocked. Database permissions (app_readonly, ADR-001) are
the second layer of defense; these application rules are first.
"""

import logging

from pydantic import BaseModel, Field
from sqlglot import exp

from dbcrawler.config.settings import Settings
from dbcrawler.guardrails.validator import validate_sql

logger = logging.getLogger("dbcrawler.guardrails")

_WRITE_DML = (exp.Insert, exp.Update, exp.Delete, exp.Merge)
_DDL = (exp.Create, exp.Drop, exp.Alter, exp.TruncateTable)
_ANY_SELECT = (exp.Select, exp.Union, exp.Except, exp.Intersect)


class GuardrailResult(BaseModel):
    allowed: bool = False
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    enforced_sql: str = ""


def _max_nested_select_depth(root: exp.Expression) -> int:
    """Depth of SELECTs nested below the top-level statement (CTEs count)."""
    best = 0

    def _visit(node: exp.Expression, depth: int) -> None:
        nonlocal best
        for child in node.iter_expressions():
            if isinstance(child, exp.Select):
                best = max(best, depth + 1)
                _visit(child, depth + 1)
            else:
                _visit(child, depth)

    _visit(root, 0)
    return best


def _classify(node: exp.Expression) -> str:
    if isinstance(node, _WRITE_DML):
        return "dml_write"
    if isinstance(node, _DDL):
        return "ddl"
    if isinstance(node, _ANY_SELECT):
        return "select"
    if isinstance(node, exp.Command):
        return "raw_command"
    return "unknown"


def check_guardrails(sql: str, settings: Settings | None = None) -> GuardrailResult:
    settings = settings or Settings()
    violations: list[str] = []
    warnings: list[str] = []

    validation = validate_sql(sql)
    if not validation.is_valid:
        for message in validation.errors:
            violations.append(f"validation: {message}")
        blocked = GuardrailResult(
            allowed=False, violations=violations, warnings=warnings
        )
        _log_blocked(sql, blocked)
        return blocked

    if len(validation.statements) != 1 or len(validation.parsed) != 1:
        violations.append(
            f"validation: expected a single statement, got {len(validation.statements)}"
        )
        blocked = GuardrailResult(allowed=False, violations=violations)
        _log_blocked(sql, blocked)
        return blocked

    parsed = validation.parsed[0]
    kind = _classify(parsed)
    if kind == "ddl" and settings.guardrail_block_ddl:
        violations.append("blocked: DDL statements are not allowed")
    elif kind == "dml_write" and settings.guardrail_block_dml:
        violations.append("blocked: DML writes are not allowed (SELECT-only)")
    elif kind != "select":
        violations.append(
            f"blocked: unrecognized/non-SELECT statement type `{kind}` (fail-closed)"
        )
    else:
        depth = _max_nested_select_depth(parsed)
        if depth > settings.guardrail_max_subquery_depth:
            violations.append(
                "blocked: subquery nesting depth "
                f"{depth} exceeds limit {settings.guardrail_max_subquery_depth}"
            )
        else:
            try:
                limited = parsed.limit(settings.guardrail_max_limit_rows)
                enforced_sql = limited.sql(dialect="postgres")
            except Exception as exc:  # noqa: BLE001 - fail closed on any rewrite failure
                violations.append(f"blocked: could not enforce row limit ({exc})")

    result = GuardrailResult(
        allowed=not violations,
        violations=violations,
        warnings=warnings,
        enforced_sql=enforced_sql if not violations else "",
    )
    if result.allowed:
        logger.info("Guardrails allowed SQL (%d chars)", len(sql))
    else:
        _log_blocked(sql, result)
    return result


def _log_blocked(sql: str, result: GuardrailResult) -> None:
    logger.warning("GUARDRAIL BLOCK: %s | reasons=%s", sql, result.violations)
