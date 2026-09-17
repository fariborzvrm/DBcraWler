# Session Log

## Session 1 — 2026-09-17

- Read plan.md and structure.md.
- Clarified decisions: PostgreSQL (Docker), uv, OpenRouter for all LLM
  calls, free nemotron embedding model, native JSON schema structured
  output, committed SQL seed data, .env secrets.
- Bootstrapped memory layer.

## Session 1 (continued) — 2026-09-17

- Implemented Phase 1 end-to-end: extraction, filtering, prompts,
  ambiguity, structured generation demo.
- Fixed seed issues (identity columns, apostrophe escaping).
- Fixed chat model: nemotron free endpoint overloaded -> switched to
  openrouter/free (ADR-009). Embedding model corrected to ...:free suffix.
- Added JSON fallback parsing + retry for router models (ADR-010).
- Grounded ambiguity check in schema; removed dialect false positives.
- Added empty-selection fallback (full schema) in filtering.
- Verified: pytest 11 passed, ruff clean, 3 live E2E demos correct.
