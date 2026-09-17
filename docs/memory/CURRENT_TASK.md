# Current Task

## Objective

Phase 4 — Query Interface (FastAPI + Streamlit), per plan.md Day 9–11.
API core complete; remaining: optional polish, then Phase 5.

## Context

Phases 1-3 complete and verified. Phase 4 adds a shared service layer
(api/service.py) used by the CLI and the API, an in-memory history store
with user feedback, a FastAPI app and a Streamlit frontend.

## Current Files

Phases 1-3 files plus:
- src/dbcrawler/api/{app,service,history}.py
- src/dbcrawler/ui/streamlit_app.py (optional-dependency group `ui`)
- tests/api/{test_api,test_history}.py

## Completed

- API: POST /v1/query (statuses: ok, blocked, clarification_needed,
  execution_error, generation_failed), GET /v1/schema,
  GET /v1/history, POST /v1/feedback/{id}.
- In-memory bounded history (200 entries) records every round-trip.
- LLM generation failures degrade to `generation_failed`, never 500.
- Streamlit UI: question input, SQL, result table, confidence breakdown,
  sanity/intent/multiquery panels, history + correct/incorrect feedback.
- Verified live: guardrails -> execution -> confidence (Andrew Fuller
  report question: 4 rows, final confidence 0.996, multiquery agree).

## Current Problem

None blocking. openrouter/free sometimes returns refusal prose
("User Safety: safe") even after the client's JSON retry; API handles
it as generation_failed (known issue, also in PROJECT_STATE).

## Next Step

Phase 5 — Evaluation suite (golden dataset, regression run). Optionally
persist history and wire feedback into fewer-shot examples first.

## Constraints

- Never execute generated SQL before guardrails.
- app_readonly grants must never be weakened.
- Guardrail rules configurable but defaults fail closed.

## Verification

pytest: 57 passed
ruff: clean
Live: uv run uvicorn dbcrawler.api.app:create_app --factory --port 8000
UI:   uv run --extra ui streamlit run src/dbcrawler/ui/streamlit_app.py
