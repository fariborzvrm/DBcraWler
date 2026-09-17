"""Query history store (Phase 4).

In-memory first per plan.md Day 9-11. Each validated query round-trip is
recorded and can be annotated with user feedback (correct/incorrect) to
seed the Phase 5 evaluation flywheel.
"""

import time
import uuid

from pydantic import BaseModel, Field

from dbcrawler.confidence import ConfidenceBreakdown


class Feedback(BaseModel):
    correct: bool
    comment: str = ""


class HistoryEntry(BaseModel):
    id: str
    timestamp: float
    question: str
    status: str
    sql: str | None = None
    explanation: str | None = None
    results: list[dict] | None = None
    row_count: int | None = None
    truncated: bool | None = None
    execution_time_ms: float | None = None
    confidence: ConfidenceBreakdown | None = None
    warnings: list[str] = Field(default_factory=list)
    feedback: Feedback | None = None


class InMemoryHistory:
    """Bounded FIFO history; per-process, no persistence yet."""

    def __init__(self, max_entries: int = 200):
        self.max_entries = max_entries
        self._entries: dict[str, HistoryEntry] = {}

    def record(self, entry: HistoryEntry) -> None:
        self._entries[entry.id] = entry
        if len(self._entries) > self.max_entries:
            for key in sorted(self._entries, key=lambda k: self._entries[k].timestamp)[
                : len(self._entries) - self.max_entries
            ]:
                del self._entries[key]

    def new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def now(self) -> float:
        return time.time()

    def get(self, entry_id: str) -> HistoryEntry | None:
        return self._entries.get(entry_id)

    def list(self, limit: int = 50) -> list[HistoryEntry]:
        entries = sorted(self._entries.values(), key=lambda e: e.timestamp)
        return entries[-limit:][::-1]

    def set_feedback(
        self, entry_id: str, correct: bool, comment: str = ""
    ) -> HistoryEntry | None:
        entry = self._entries.get(entry_id)
        if entry is not None:
            entry.feedback = Feedback(correct=correct, comment=comment)
        return entry


def build_history_entry(
    entry_id: str,
    timestamp: float,
    question: str,
    status: str,
    *,
    generated,
    results,
    confidence,
    warnings: list[str],
) -> HistoryEntry:
    query_result = results.get("query_result")
    multiquery = results.get("multiquery")
    all_warnings = list(warnings)
    if multiquery is not None and not multiquery.agree:
        all_warnings.append(f"multi-query disagreement: {multiquery.detail}")
    return HistoryEntry(
        id=entry_id,
        timestamp=timestamp,
        question=question,
        status=status,
        sql=generated.sql if generated is not None else None,
        explanation=generated.explanation if generated is not None else None,
        results=query_result.rows if query_result is not None else None,
        row_count=query_result.row_count if query_result is not None else None,
        truncated=query_result.truncated if query_result is not None else None,
        execution_time_ms=(
            query_result.execution_time_ms if query_result is not None else None
        ),
        confidence=confidence,
        warnings=all_warnings,
    )
