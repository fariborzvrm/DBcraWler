# Current Task

## Objective

Continue Phase 2 — wrap up remaining polish, then move to Phase 3
(hallucination detection), per plan.md Day 6–9.

## Context

Phase 2 core is implemented and verified end-to-end:
extraction -> filtering -> ambiguity -> structured generation (GeneratedSQL
model) -> guardrails -> optional read-only sandboxed execution.
Demo `--execute` flag runs the full guarded path and prints rows, timing,
plan. Ambiguity path unchanged.

## Current Files

Phase 1 files (see PROJECT_STATE.md) plus:
- src/dbcrawler/generated_sql.py (GeneratedSQL contract)
- src/dbcrawler/guardrails/{validator,guardrails,executor}.py
- tests/guardrails/, tests/generated_sql/
- src/dbcrawler/demo.py (--execute flag)

## Completed

- Phase 1 fully implemented (see PROJECT_STATE.md checklist).
- Phase 2 step 1: GeneratedSQL contract locked (CONTRACTS.md) + pydantic
  validation via from_llm.
- Phase 2 step 2: sqlglot validator (postgres dialect; ADR-011).
- Phase 2 step 3: guardrail middleware — DDL/DML block, fail-closed on
  unknown statements, single-statement-only, subquery depth cap,
  LIMIT injection/clamping, configurable Settings rules, logged blocks.
- Phase 2 step 4: read-only execution layer — rollback transaction,
  app_readonly user, EXPLAIN (FORMAT JSON) plan capture, EXPLAIN
  scan-row cap, rows/row_count/truncated/execution_time_ms.

## Current Problem

None blocking.

## Next Step

Phase 3 order of work:
1. SQL-to-question back-translation verification.
2. Result sanity checks (magnitude, NULL ratios).
3. Multi-query validation for complex questions.
4. Combined confidence score across all signals.

## Constraints

- Never execute generated SQL before guardrails.
- app_readonly grants must never be weakened.
- Guardrail rules configurable but defaults fail closed.

## Verification

pytest: 33 passed
ruff: clean

Last commands:

uv run pytest -q
uv run ruff check .
