"""Evaluation metrics (plan.md Phase 5).

- sql_exact_match: normalized-text equality between generated and golden SQL.
- execution_match: row-signature equality between generated results and the
  golden snapshot (structure-independent, the primary metric).
- hallucination detection: an unanswerable question is correctly flagged if
  the pipeline does NOT return a confident result (status != ok or low final
  confidence).
- guardrail effectiveness: dangerous statements must be blocked.
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from dbcrawler.validation.multiquery import _canonical  # shared row canonicalization


class CaseOutcome(BaseModel):
    question: str
    category: str
    exact_match: bool | None = None
    execution_match: bool | None = None
    flagged_correctly: bool | None = None
    status: str = ""
    confidence: float | None = None
    detail: str = ""


class EvaluationReport(BaseModel):
    golden_total: int = 0
    exact_matches: int = 0
    execution_matches: int = 0
    ambiguous_total: int = 0
    ambiguous_correct: int = 0
    unanswerable_total: int = 0
    unanswerable_correct: int = 0
    dangerous_total: int = 0
    dangerous_blocked: int = 0
    failures: list[CaseOutcome] = Field(default_factory=list)

    @property
    def execution_accuracy(self) -> float | None:
        return (
            self.execution_matches / self.golden_total if self.golden_total else None
        )

    @property
    def exact_match_rate(self) -> float | None:
        return self.exact_matches / self.golden_total if self.golden_total else None

    @property
    def hallucination_detection_rate(self) -> float | None:
        checked = self.unanswerable_total + self.ambiguous_total
        if not checked:
            return None
        detected = self.unanswerable_correct + self.ambiguous_correct
        return detected / checked

    @property
    def guardrail_effectiveness(self) -> float | None:
        return (
            self.dangerous_blocked / self.dangerous_total
            if self.dangerous_total
            else None
        )


def normalize_sql(sql: str) -> str:
    """Whitespace/keyword-insensitive comparison for exact-match scoring."""
    collapsed = re.sub(r"\s+", " ", sql.strip().rstrip(";"))
    collapsed = re.sub(r"\s*([(),=<>])\s*", r"\1", collapsed)
    return collapsed.lower()


def rows_equivalent(
    generated_rows: list[dict],
    expected_rows: list[dict],
) -> bool:
    """Row-multiset equality over cell values.

    Column names (aliases chosen by the LLM) are deliberately ignored;
    only the returned values count for execution match.
    """

    def signature(row: dict) -> tuple[str, ...]:
        return tuple(sorted(_canonical(value) for value in row.values()))

    return sorted(signature(row) for row in generated_rows) == sorted(
        signature(row) for row in expected_rows
    )


def summary_lines(report: EvaluationReport) -> list[str]:
    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value * 100:.1f}%"

    lines = [
        "=== Evaluation report ===",
        (
            f"execution accuracy      : {pct(report.execution_accuracy)}"
            f" ({report.execution_matches}/{report.golden_total})"
        ),
        (
            f"sql exact match         : {pct(report.exact_match_rate)}"
            f" ({report.exact_matches}/{report.golden_total})"
        ),
        f"ambiguous clarified     : {report.ambiguous_correct}/{report.ambiguous_total}",
        f"unanswerable flagged    : {report.unanswerable_correct}/{report.unanswerable_total}",
        f"hallucination detect    : {pct(report.hallucination_detection_rate)}",
        (
            f"guardrail blocks        : {report.dangerous_blocked}/{report.dangerous_total}"
            f" ({pct(report.guardrail_effectiveness)})"
        ),
    ]
    for failure in report.failures:
        lines.append(f"  FAIL {failure.question} | {failure.detail}")
    return lines


def rows_snapshot_compatible(snapshot: Any) -> bool:
    return isinstance(snapshot, dict) and "rows" in snapshot
