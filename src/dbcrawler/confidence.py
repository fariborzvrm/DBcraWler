"""Confidence scoring (plan.md Phase 3 §4).

Combines validation signals into one score with a transparent breakdown.
Never claims confidence without validation signals (AGENTS.md): the LLM's
self-reported confidence is only one of several inputs.
"""

from pydantic import BaseModel

from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.validation.sanity import SanityResult

_UNAVAILABLE_ALIGNMENT = 0.5  # neutral when a signal could not be computed


class ConfidenceBreakdown(BaseModel):
    final: float
    llm_self_report: float
    intent_alignment: float | None = None
    sanity_pass_rate: float | None = None
    schema_coverage: float | None = None
    multiquery_agreement: bool | None = None


def schema_coverage(
    sql_tables: list[str],
    ast_tables: set[str],
    schema_tables: set[str],
) -> float:
    """Coverage of the tables the LLM claimed it used.

    A claimed table that does not exist in the schema is hallucination
    and fails coverage outright.
    """
    claimed = {t.lower() for t in sql_tables}
    if not claimed:
        return 1.0
    if claimed - {t.lower() for t in schema_tables}:
        return 0.0
    actual = {t.lower() for t in ast_tables}
    return len(claimed & actual) / len(claimed)


def compute_confidence(
    generated: GeneratedSQL,
    sanity: SanityResult,
    intent_alignment: float | None = None,
    coverage: float | None = None,
    multiquery_agreement: float | None = None,
) -> ConfidenceBreakdown:
    alignment = (
        intent_alignment if intent_alignment is not None else _UNAVAILABLE_ALIGNMENT
    )
    if coverage is None:
        coverage = 1.0

    weights = {
        "llm_self_report": 0.20,
        "intent_alignment": 0.35,
        "sanity_pass_rate": 0.25,
        "schema_coverage": 0.10,
        "multiquery_agreement": 0.10,
    }
    signals = {
        "llm_self_report": generated.confidence,
        "intent_alignment": alignment,
        "sanity_pass_rate": sanity.pass_rate,
        "schema_coverage": coverage,
        "multiquery_agreement": multiquery_agreement,
    }
    if multiquery_agreement is None:
        weights.pop("multiquery_agreement")
    else:
        # A contradicting second query is a strong negative signal.
        if not multiquery_agreement:
            weights["llm_self_report"] = 0.0

    weight_sum = sum(weights.values()) or 1.0
    score = sum((weights[k] * signals[k]) for k in weights) / weight_sum
    return ConfidenceBreakdown(
        final=round(score, 3),
        llm_self_report=generated.confidence,
        intent_alignment=intent_alignment,
        sanity_pass_rate=round(sanity.pass_rate, 3) if sanity.findings else None,
        schema_coverage=round(coverage, 3),
        multiquery_agreement=multiquery_agreement,
    )
