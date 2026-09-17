"""Live evaluation runner (plan.md Phase 5).

Runs the real pipeline over the golden dataset and measures:
- SQL exact match / execution match against the golden snapshot
- ambiguous questions  -> clarification_needed
- unanswerable questions -> no confident result (hallucination check)
- dangerous statements  -> guardrail blocks (no LLM involved)

Usage:
    uv run python -m dbcrawler.evaluation
"""

import json
import logging
from typing import Any

from dbcrawler.api.service import (
    check_question_ambiguity,
    execute_generated_sql,
    generate_sql,
)
from dbcrawler.config.settings import get_settings
from dbcrawler.evaluation.dataset import DATASET_PATH, SNAPSHOT_PATH, load_dataset
from dbcrawler.evaluation.metrics import (
    CaseOutcome,
    EvaluationReport,
    normalize_sql,
    rows_equivalent,
    summary_lines,
)
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.schema.extractor import extract_schema_url

logger = logging.getLogger("dbcrawler.evaluator")

LOW_CONFIDENCE_FLAG = 0.45


class _Context:
    """Bag of client/settings/schema for the per-case evaluators."""

    def __init__(self, settings, client, schema):
        self.settings = settings
        self.client = client
        self.schema = schema


def evaluate_golden(item, snapshot: dict[str, Any], ctx: _Context) -> CaseOutcome:
    expected = snapshot.get(item.question)
    if expected is None:
        raise RuntimeError(f"missing golden snapshot entry: {item.question}")
    try:
        generated = generate_sql(ctx.client, ctx.settings, ctx.schema, item.question)
    except Exception as exc:  # noqa: BLE001 - malformed payloads are failed cases
        return CaseOutcome(
            question=item.question,
            category=item.category,
            exact_match=False,
            execution_match=False,
            status="generation_failed",
            detail=f"generation unavailable: {exc}",
        )
    outcome = execute_generated_sql(
        ctx.client, ctx.settings, ctx.schema, item.question, generated
    )
    exact = normalize_sql(generated.sql) == normalize_sql(item.sql)
    executed = (
        outcome["status"] == "ok"
        and outcome["query_result"] is not None
        and rows_equivalent(outcome["query_result"].rows, expected["rows"])
    )
    detail = "" if executed else f"status={outcome['status']}"
    if not executed and outcome["query_result"] is not None:
        detail += f" got={outcome['query_result'].rows[:2]} want={expected['rows'][:2]}"
    confidence = (
        outcome["confidence"].final if outcome["confidence"] is not None else None
    )
    return CaseOutcome(
        question=item.question,
        category=item.category,
        exact_match=exact,
        execution_match=executed,
        status=outcome["status"],
        confidence=confidence,
        detail=detail,
    )


def evaluate_ambiguous(question: str, ctx: _Context) -> CaseOutcome:
    ambiguity = check_question_ambiguity(ctx.client, ctx.settings, ctx.schema, question)
    flagged = ambiguity.is_ambiguous
    return CaseOutcome(
        question=question,
        category="ambiguous",
        flagged_correctly=flagged,
        status="clarification_needed" if flagged else "answered",
        detail="" if flagged else "did not ask for clarification",
    )


def evaluate_unanswerable(question: str, ctx: _Context) -> CaseOutcome:
    try:
        generated = generate_sql(ctx.client, ctx.settings, ctx.schema, question)
        outcome = execute_generated_sql(
            ctx.client, ctx.settings, ctx.schema, question, generated
        )
    except Exception as exc:  # noqa: BLE001 - a safe generation failure is a flag
        return CaseOutcome(
            question=question,
            category="unanswerable",
            flagged_correctly=True,
            status="generation_failed",
            detail=f"generation handled safely: {exc}",
        )
    confidence = (
        outcome["confidence"].final if outcome["confidence"] is not None else None
    )
    flagged = outcome["status"] != "ok" or (
        confidence is not None and confidence < LOW_CONFIDENCE_FLAG
    )
    return CaseOutcome(
        question=question,
        category="unanswerable",
        flagged_correctly=flagged,
        status=outcome["status"],
        confidence=confidence,
        detail="" if flagged else "answered with high confidence",
    )


def evaluate_guardrails(dataset, settings) -> list[CaseOutcome]:
    from dbcrawler.guardrails import check_guardrails

    outcomes = []
    for dangerous in dataset.dangerous_statements:
        result = check_guardrails(dangerous.sql, settings)
        blocked = not result.allowed
        outcomes.append(
            CaseOutcome(
                question=dangerous.sql[:60],
                category=f"guardrail:{dangerous.violation}",
                flagged_correctly=blocked,
                status="blocked" if blocked else "allowed",
                detail="" if blocked else ",".join(result.violations),
            )
        )
    return outcomes


def run_evaluation(client=None, settings=None, verbose: bool = True) -> EvaluationReport:
    settings = settings or get_settings()
    client = client or OpenRouterClient(settings)
    dataset = load_dataset(DATASET_PATH)
    schema = extract_schema_url(settings.db_url, settings)
    ctx = _Context(settings, client, schema)

    with open(SNAPSHOT_PATH, encoding="utf-8") as handle:
        snapshot = json.load(handle)

    report = EvaluationReport()

    for index, item in enumerate(dataset.golden_queries, start=1):
        outcome = evaluate_golden(item, snapshot, ctx)
        report.golden_total += 1
        if outcome.exact_match:
            report.exact_matches += 1
        if outcome.execution_match:
            report.execution_matches += 1
        else:
            report.failures.append(outcome)
        if verbose:
            print(
                f"[golden {index:02d}] exact={outcome.exact_match} "
                f"exec={outcome.execution_match} - {item.question}"
            )

    for question in dataset.ambiguous_questions:
        outcome = evaluate_ambiguous(question, ctx)
        report.ambiguous_total += 1
        if outcome.flagged_correctly:
            report.ambiguous_correct += 1
        else:
            report.failures.append(outcome)
        if verbose:
            print(f"[ambiguous] flag={outcome.flagged_correctly} - {question}")

    for question in dataset.unanswerable_questions:
        outcome = evaluate_unanswerable(question, ctx)
        report.unanswerable_total += 1
        if outcome.flagged_correctly:
            report.unanswerable_correct += 1
        else:
            report.failures.append(outcome)
        if verbose:
            print(f"[unanswerable] flag={outcome.flagged_correctly} - {question}")

    for outcome in evaluate_guardrails(dataset, settings):
        report.dangerous_total += 1
        if outcome.flagged_correctly:
            report.dangerous_blocked += 1
        else:
            report.failures.append(outcome)
        if verbose:
            print(f"[dangerous] blocked={outcome.flagged_correctly} - {outcome.question}")

    return report


def main() -> None:
    report = run_evaluation()
    print()
    for line in summary_lines(report):
        print(line)


