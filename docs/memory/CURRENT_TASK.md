# Current Task

## Objective

Start Phase 4 — Query Interface (FastAPI + frontend), per plan.md
Day 9–11.

## Context

Phases 1-3 complete and verified end-to-end. Phase 3 added validation
runner: intent back-translation, sanity checks, multi-query agreement
for complex queries, multi-signal confidence (ADR-012).

## Current Files

Phases 1-2 files (see PROJECT_STATE.md) plus:
- src/dbcrawler/validation/{backtranslator,sanity,multiquery,runner}.py
- src/dbcrawler/confidence.py
- src/dbcrawler/demo.py (--execute runs full validated pipeline)
- tests/validation/, tests/confidence/

## Completed

- Phase 3: IntentVerification, SanityResult, multi-query
  agreements, ConfidenceBreakdown; contracts locked in CONTRACTS.md.

## Current Problem

None blocking. Phase 4 API will need a session/history store
(currently nothing persists queries).

## Next Step

Phase 4 order of work:
1. FastAPI service: POST /v1/query, GET /v1/schema, GET /v1/history.
2. Session query history store (in-memory first).
3. Frontend (Streamlit first): question input, SQL, result table,
   confidence + breakdown.

## Constraints

- Never execute generated SQL before guardrails.
- app_readonly grants must never be weakened.
- Guardrail rules configurable but defaults fail closed.

## Verification

pytest: 47 passed
ruff: clean

Last commands:

uv run pytest -q
uv run ruff check .
