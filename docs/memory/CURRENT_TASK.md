# Current Task

## Objective

Phase 5 — Evaluation suite (golden dataset + live runner), per plan.md
Day 11-13. Infrastructure complete and offline-verified; live full run
blocked on OpenRouter free-tier daily quota.

## Context

Phases 1-4 complete and committed. Phase 5 adds the golden dataset
(42 verified SQL questions incl. lookup/join/aggregation/date_range/top_n,
5 ambiguous, 6 unanswerable, 8 dangerous statements), a snapshot of
expected results, evaluation metrics and a live runner.

## Current Files

Phases 1-4 files plus:
- data/evaluation/golden_queries.json, golden_results.json (snapshot)
- src/dbcrawler/evaluation/{dataset,metrics,runner,snapshot,__main__,
  write_golden_snapshot}.py
- tests/evaluation/test_dataset.py

## Completed

- 52 natural-language evaluation questions (+ 8 guardrail cases);
  all golden SQL verified to run against seeded DB, zero empty results.
- Execution match compares result VALUES (multiset, alias-insensitive).
- Dangerous-statement guardrail cases verified offline (8/8 blocked).
- Live runner: `uv run python -m dbcrawler.evaluation` (exact match,
  execution accuracy, ambiguous/unanswerable detection, guardrail rate,
  failure details in summary).
- README.md created at repo root (public-GitHub/resume oriented):
  badges, "why different" table, mermaid + ASCII pipeline diagram,
  key engineering decisions, architecture tree, quick start, API table,
  testing, roadmap, security principles. Only in-repo facts; no invented
  evaluation numbers. docs/, AGENTS.md, plan.md, structure.md added to
  .gitignore (none were ever committed, no git rm --cached needed).

## Current Problem

OpenRouter free tier exhausted daily quota during the first live run
(429 free-models-per-day); every LLM-backed case degraded to
generation_failed safely. Re-run when quota resets (or with credits).

## Next Step

Re-run `uv run python -m dbcrawler.evaluation` and record real numbers
in PROJECT_STATE.md (execution accuracy, hallucination detection rate,
guardrail blocks across 92 tests). Then Phase 6 containerization/docs.

## Constraints

- Never execute generated SQL before guardrails.
- Golden results snapshot must be regenerated via
  `uv run python -m dbcrawler.evaluation.write_golden_snapshot`
  whenever seed data or dataset changes.

## Verification

pytest: 67 passed
ruff: clean

Last commands:

uv run pytest -q
uv run ruff check .
uv run python -m dbcrawler.evaluation.write_golden_snapshot
uv run python -m dbcrawler.evaluation
