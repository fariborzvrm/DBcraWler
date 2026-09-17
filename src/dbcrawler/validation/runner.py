"""Phase 3 orchestration: generate -> guardrails -> execute -> verify.

All SQL (primary and alternative) passes through the same guardrail +
sandboxed execution path. No query ever bypasses validation.
"""

import logging

import sqlglot
from pydantic import BaseModel, Field
from sqlglot import exp

from dbcrawler.confidence import (
    ConfidenceBreakdown,
    compute_confidence,
    schema_coverage,
)
from dbcrawler.config.settings import Settings
from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.guardrails import check_guardrails
from dbcrawler.guardrails.executor import ExecutionBlocked, QueryResult, execute_sql
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.validation.backtranslator import IntentVerification, verify_intent
from dbcrawler.validation.multiquery import (
    MultiQueryResult,
    compare_results,
    generate_alternative,
    is_complex,
)
from dbcrawler.validation.sanity import SanityFinding, SanityResult, check_result_sanity

logger = logging.getLogger("dbcrawler.validation")


class VerifiedQuery(BaseModel):
    query_result: QueryResult | None = None
    sanity: SanityResult
    intent: IntentVerification | None = None
    multiquery: MultiQueryResult | None = None
    confidence: ConfidenceBreakdown | None = None
    warnings: list[str] = Field(default_factory=list)


def ast_table_names(sql: str) -> set[str]:
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except sqlglot.errors.ParseError:
        return set()
    return {node.name.lower() for node in parsed.find_all(exp.Table)}


def run_validation(
    client: OpenRouterClient,
    settings: Settings,
    question: str,
    generated: GeneratedSQL,
    enforced_sql: str,
    schema,
    run_multiquery: bool | None = None,
) -> VerifiedQuery:
    """Execute `enforced_sql` (guardrail-approved) and compute validation signals."""
    if run_multiquery is None:
        run_multiquery = is_complex(enforced_sql)

    warnings: list[str] = []
    try:
        query_result = execute_sql(
            enforced_sql, settings, validation={}
        )
    except ExecutionBlocked as exc:
        logger.warning("Execution blocked by scan cap: %s", exc.violations)
        sanity = SanityResult(
            findings=[
                SanityFinding(check="executed", passed=False, message=exc.violations[0])
            ]
        )
        return VerifiedQuery(sanity=sanity, warnings=exc.violations)

    sanity = check_result_sanity(query_result)

    try:
        intent = verify_intent(client, question, generated.sql)
        alignment = intent.alignment_score
    except Exception as exc:  # noqa: BLE001 - LLM failures degrade, never crash
        logger.warning("Intent verification failed: %s", exc)
        intent = None
        alignment = None
        warnings.append(f"intent verification unavailable: {exc}")

    coverage = schema_coverage(
        generated.tables,
        ast_table_names(generated.sql),
        {table.name.lower() for table in schema.tables},
    )

    multiquery: MultiQueryResult | None = None
    agreement: bool | None = None
    if run_multiquery:
        try:
            alt = generate_alternative(client, question, enforced_sql)
            alt_checked = check_guardrails(alt["sql"], settings)
            if alt_checked.allowed:
                alt_result = execute_sql(alt_checked.enforced_sql, settings)
                multiquery = compare_results(query_result, alt_result)
                agreement = multiquery.agree
            else:
                warnings.append(f"alternative query rejected: {alt_checked.violations}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"multi-query validation failed: {exc}")

    confidence = compute_confidence(
        generated,
        sanity,
        intent_alignment=alignment,
        coverage=coverage,
        multiquery_agreement=agreement,
    )
    return VerifiedQuery(
        query_result=query_result,
        sanity=sanity,
        intent=intent,
        multiquery=multiquery if multiquery is not None and multiquery.ran else None,
        confidence=confidence,
        warnings=warnings,
    )
