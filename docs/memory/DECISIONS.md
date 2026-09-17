# Architectural Decisions

## ADR-011 — SQL Validation Engine

Decision:
SQL syntax/structure validation and LIMIT rewriting use sqlglot,
parsed with the postgres dialect.

Reason:
sqlglot is already a project dependency, parses to a full AST
(needed for statement classification, subquery-depth checks and
LIMIT enforcement), and was chosen over sqlparse (planner suggestion)
because sqlparse has no AST and cannot rewrite without re-parsing.

## ADR-001 — Database

Decision:
Use PostgreSQL, running in Docker from the start.

Reason:
Production-like relational database with EXPLAIN,
permissions, transactions and realistic SQL behavior.

---

## ADR-002 — Dependency Management

Decision:
Use uv for Python dependency and environment management.

Reason:
Fast, lockfile-based, easy Docker integration.

---

## ADR-003 — LLM Provider

Decision:
All LLM calls (chat + embeddings) go through OpenRouter
using the user's API key.

Reason:
Single API for all models. Embeddings use the free
NVIDIA nemotron embedding models via OpenRouter's
/api/v1/embeddings endpoint.

---

## ADR-004 — Chat Model

Decision:
SQL generation uses nvidia/nemotron-3-super:free,
loaded from configuration (env var), never hard-coded.

Reason:
Free models on OpenRouter churn frequently; a config-only
model ID allows switching without code changes.

---

## ADR-009 — Chat Model (Supersedes ADR-004)

Decision:
Default chat model is openrouter/free (OpenRouter's
auto-router across free models), still loaded from
configuration, never hard-coded.

Reason:
The pinned nvidia/nemotron-3-super-120b-a12b:free endpoint
repeatedly returned "provider_overloaded" errors. The
auto-router picks whichever free provider is healthy and
absorbs model churn without code or config changes.

---

## ADR-010 — Structured Output Fallback (Supersedes ADR-006)

Decision:
json_schema response_format stays the primary mechanism,
but the client adds a robust fallback: parse the outermost
JSON object from prose content, and retry once with an
explicit JSON-only reminder if none is found.

Reason:
The openrouter/free auto-router routes to models that do
not always honor response_format json_schema. Native
json_schema alone was insufficient under the auto-router.

---

## ADR-005 — Embedding Model

Decision:
Schema filtering uses a free nemotron embedding model
via OpenRouter embeddings endpoint.

Reason:
Zero cost, single provider for all LLM traffic.

---

## ADR-006 — Structured LLM Output

Decision:
Use OpenRouter's native json_schema response format
(OpenAI-compatible), validated with pydantic on our side.

Reason:
Fewer dependencies than Instructor; model-agnostic.
Pydantic validation keeps downstream code deterministic.

---

## ADR-007 — Seed Data

Decision:
Northwind-style dataset committed as data/seed/*.sql,
executed by the Postgres init container.

Reason:
Fully reproducible; no external downloads at runtime.

---

## ADR-008 — Secrets

Decision:
OPENROUTER_API_KEY lives in .env (git-ignored), loaded via
pydantic-settings.

Reason:
Never commit secrets.
