"""Write the golden-results snapshot for the evaluation dataset.

Executes every golden SQL through the guarded read-only executor and
stores the expected rows. The live evaluation runner compares generated
results against this snapshot so the dataset ships with expected
results (plan.md Phase 5).

    uv run python -m dbcrawler.evaluation.write_golden_snapshot
"""

import json

from dbcrawler.config.settings import get_settings
from dbcrawler.evaluation.dataset import DATASET_PATH, SNAPSHOT_PATH, load_dataset
from dbcrawler.guardrails import check_guardrails
from dbcrawler.guardrails.executor import execute_sql


def build_snapshot(settings) -> dict:
    dataset = load_dataset(DATASET_PATH)
    snapshot = {}
    for item in dataset.golden_queries:
        guardrail = check_guardrails(item.sql, settings)
        if not guardrail.allowed:
            raise RuntimeError(
                f"golden SQL is not allowed by guardrails ({item.question}): "
                f"{guardrail.violations}"
            )
        result = execute_sql(guardrail.enforced_sql, settings, validation={})
        snapshot[item.question] = {"sql": item.sql, "rows": result.rows}
    return snapshot


def write_snapshot(path=None, settings=None) -> dict:
    path = path or SNAPSHOT_PATH
    settings = settings or get_settings()
    snapshot = build_snapshot(settings)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=1, default=str)
    return snapshot
