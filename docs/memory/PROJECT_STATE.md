# Project — DBcraWler

## Project Goal

Production-oriented Text-to-SQL system with:

- schema-aware generation
- SQL safety guardrails
- hallucination/intent validation
- result sanity checking
- confidence scoring
- evaluation
- observability

## Current Phase

Phase 4 — Query Interface (API + Streamlit core complete, verified live)

## Overall Progress

Phase 1: 🟢
Phase 2: 🟢
Phase 3: 🟢
Phase 4: 🟡 (API + UI done; feedback not yet wired into evaluation)
Phase 5: 🔴
Phase 6: 🔴
Phase 7: 🔴

## Completed

- [x] Memory layer bootstrapped
- [x] Phase 1 ADRs recorded (ADR-001..010)
- [x] PostgreSQL configured via docker-compose (seeded, app_readonly SELECT-only verified)
- [x] SQLAlchemy schema extraction (tables, columns, types, PK incl. composite, FK incl. composite)
- [x] Schema representation contract (SchemaRepresentation)
- [x] Sample value extraction
- [x] Schema filtering (nemotron embeddings, FK-neighbor expansion, empty-selection fallback)
- [x] Prompt construction (glossary + few-shot from data/few_shot/northwind.json)
- [x] Ambiguity detection (schema-grounded; dialect false positives eliminated)
- [x] LLM client (OpenRouter chat + embeddings via httpx, retry + JSON fallback)
- [x] GeneratedSQL pydantic contract (from_llm validation, confidence 0..1)
- [x] sqlglot validator (postgres dialect, per-statement errors, ADR-011)
- [x] Guardrail middleware (DDL/DML block, fail-closed unknown/single-statement,
      subquery depth cap, LIMIT inject/clamp, configurable rules, logged blocks)
- [x] Read-only execution layer (rollback tx, EXPLAIN plan + scan-row cap,
      rows/timing/truncation capture)
- [x] Demo --execute flag runs full guarded execute path
- [x] Intent back-translation + LLM alignment judge (IntentVerification)
- [x] Deterministic result sanity checks (has_rows, null_heavy, magnitude)
- [x] Multi-query validation: alternative SQL via LLM, same guardrail/execute
      path, row-signature comparison
- [x] Multi-signal confidence scoring with transparent breakdown (ADR-012)
- [x] validation/runner orchestration wired into demo (--execute)
- [x] Git initialized; phases 1-2 committed (326592a)
- [x] FastAPI service (POST /v1/query, GET /v1/schema, /v1/history,
      POST /v1/feedback/{id}); statuses ok/blocked/clarification_needed/
      execution_error/generation_failed; LLM failure never 500s
- [x] In-memory bounded history store (200) + correct/incorrect feedback
- [x] Shared pipeline service layer (api/service.py) reused by CLI pattern
- [x] Streamlit frontend (result table, confidence breakdown, history,
      feedback); optional dependency group `ui`
- [x] Live verification: real query end-to-end through API, conf 0.996

## Current Implementation

Full pipeline: extraction -> filtering -> ambiguity -> generated SQL ->
guardrails -> sandboxed read-only execution -> intent back-translation ->
sanity checks -> multi-query agreement (complex queries) -> confidence
breakdown. Execution only happens after guardrails pass; app_readonly user
(ADR-001) is the second defense layer.

## Next Milestone

Phase 5: Evaluation suite (golden query dataset + regression runner).
Optionally wire user feedback (correct/incorrect) into few-shot examples
and golden dataset first.

## Important Constraints

- Never execute generated SQL before guardrails.
- Database execution user must be read-only.
- Application guardrails are defense-in-depth, not the only protection.
- Generated SQL must be validated before execution.
- Do not claim confidence without validation signals.
- OpenRouter model IDs come from config, never hard-coded.

## Known Problems

- Some questions score below the 0.3 embedding threshold and fall back to
  the full schema (used 100 customers / 8 tables; acceptable at this size,
  matters in Phase 2+ if the dataset grows).
- openrouter/free endpoint occasionally returns 200 with upstream error
  bodies; handled by in-body error retry logic in llm/client.py.
- openrouter/free occasionally returns refusal prose ("User Safety: safe")
  even after JSON retry; API degrades to `generation_failed`.

## Last Verified State

2026-09-17: pytest 57 passed; ruff clean. Phase 4 verified live: uvicorn
service answered "Which employees report to Andrew Fuller?" with status
ok, correct 4-row result, confidence 0.996 (multiquery agreement true);
history + feedback round-tripped.
