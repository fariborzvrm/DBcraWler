"""Golden evaluation dataset (plan.md Phase 5).

The dataset version-tracks `data/evaluation/golden_queries.json`:
- natural-language questions with verified correct SQL (categories:
  lookup, join, aggregation, date_range, top_n)
- ambiguous questions (should produce clarification_needed)
- unanswerable questions (should NOT produce a confident answer)
- dangerous SQL statements (guardrails must block)

Write evaluation for this directory after modifying the dataset; the
expected-results snapshot refreshes with `python -m dbcrawler.evaluation.write_golden_snapshot`
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

DATASET_PATH = Path("data/evaluation/golden_queries.json")
SNAPSHOT_PATH = Path("data/evaluation/golden_results.json")

Category = Literal["lookup", "join", "aggregation", "date_range", "top_n"]


class GoldenQuery(BaseModel):
    question: str
    sql: str
    category: Category


class DangerousStatement(BaseModel):
    sql: str
    violation: Literal["dml", "ddl", "multi_statement"]


class EvaluationDataset(BaseModel):
    golden_queries: list[GoldenQuery]
    ambiguous_questions: list[str]
    unanswerable_questions: list[str]
    dangerous_statements: list[DangerousStatement]


@lru_cache
def load_dataset(path: Path | None = None) -> EvaluationDataset:
    import json

    path = path or DATASET_PATH
    with open(path, encoding="utf-8-sig") as handle:
        return EvaluationDataset.model_validate(json.load(handle))
