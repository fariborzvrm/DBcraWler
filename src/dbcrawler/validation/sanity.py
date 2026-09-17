"""Result sanity checking (plan.md Phase 3 §2).

Deterministic, schema-free heuristics over executed rows. No LLM calls:
these are fast local checks that run on every execution.
"""

import math
from typing import Any

from pydantic import BaseModel, Field

from dbcrawler.guardrails.executor import QueryResult


class SanityFinding(BaseModel):
    check: str
    passed: bool = True
    message: str = ""


class SanityResult(BaseModel):
    findings: list[SanityFinding] = Field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.findings:
            return 1.0
        return sum(f.passed for f in self.findings) / len(self.findings)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_result_sanity(query_result: QueryResult) -> SanityResult:
    findings: list[SanityFinding] = []

    if query_result.row_count == 0:
        findings.append(
            SanityFinding(
                check="has_rows",
                passed=False,
                message="query returned no rows",
            )
        )

    if query_result.rows:
        columns = list(query_result.rows[0].keys())
        for column in columns:
            values = [row.get(column) for row in query_result.rows]
            present = [v for v in values if v is not None]
            if present and len(present) < len(values) / 2:
                findings.append(
                    SanityFinding(
                        check="null_heavy",
                        passed=False,
                        message=(
                            f"column `{column}` is more than 50% NULL "
                            "which may indicate a bad JOIN"
                        ),
                    )
                )
            elif present == [] and len(values) > 0:
                findings.append(
                    SanityFinding(
                        check="null_heavy",
                        passed=False,
                        message=f"column `{column}` is entirely NULL",
                    )
                )

            _magnitude_findings(column, values, findings)

    return SanityResult(findings=findings)


def _magnitude_findings(
    column: str, values: list[Any], findings: list[SanityFinding]
) -> None:
    """Flag impossible-looking magnitudes in count-like and revenue-like columns."""
    name = column.lower()
    numeric = [float(v) for v in values if _is_number(v) and math.isfinite(float(v))]
    if not numeric:
        return
    if any(h in name for h in ("count", "n_")):
        negative = min(numeric) < 0
        fractional = any(v != int(v) for v in numeric)
        if negative or fractional:
            findings.append(
                SanityFinding(
                    check="magnitude",
                    passed=False,
                    message=f"count-like column `{column}` has negative/fractional values",
                )
            )
    if any(h in name for h in ("revenue", "sales", "total", "amount", "price")) and (
        max(abs(v) for v in numeric) > 1e15
    ):
        findings.append(
            SanityFinding(
                check="magnitude",
                passed=False,
                message=f"monetary column `{column}` has implausible magnitude",
            )
        )
