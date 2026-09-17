DBcraWler-v2 project structure/
│
├── AGENTS.md
│
├── docs/
│   └── memory/
│       ├── CURRENT_TASK.md
│       ├── PROJECT_STATE.md
│       ├── DECISIONS.md
│       ├── CONTRACTS.md
│       ├── EVALUATION.md
│       └── SESSION_LOG.md
│
├── src/
├── tests/
├── data/
└── docker-compose.yml


The important distinction

For this project:

AGENTS.md → how the agent should behave
PROJECT_STATE.md → where the project currently is
CURRENT_TASK.md → what we're doing right now
DECISIONS.md → why we made important decisions
CONTRACTS.md → interfaces/API/schema contracts that must not accidentally change
EVALUATION.md → measured performance
SESSION_LOG.md → optional historical record

---------------

1. PROJECT_STATE.md

This should be the single source of truth for project progress.

example of how file should look like:

# Project  — DBcraWler

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

Phase 1 — Schema-Aware Prompt Engine

## Overall Progress

Phase 1: 🟡
Phase 2: 🔴
Phase 3: 🔴
Phase 4: 🔴
Phase 5: 🔴
Phase 6: 🔴
Phase 7: 🔴

## Completed

- [ ] Repository initialized
- [ ] PostgreSQL/DuckDB configured
- [ ] SQLAlchemy schema extraction
- [ ] Schema representation
- [ ] Sample value extraction
- [ ] Schema filtering
- [ ] Prompt construction
- [ ] Ambiguity detection

## Current Implementation

Nothing implemented yet.

## Next Milestone

Implement SQLAlchemy-based schema extraction.

## Important Constraints

- Never execute generated SQL before guardrails.
- Database execution user must be read-only.
- Application guardrails are defense-in-depth, not the only protection.
- Generated SQL must be validated before execution.
- Do not claim confidence without validation signals.

## Known Problems

None.

## Last Verified State

Not implemented yet.

-----------------------------

2. CURRENT_TASK.md
This is the file model should care about most when I start a new session.

here is the example of the file:

# Current Task

## Objective

Implement database schema extraction using SQLAlchemy.

## Context

Project DBcraWler is a Text-to-SQL system.

The LLM needs a structured representation of:

- tables
- columns
- types
- primary keys
- foreign keys
- sample categorical values

## Current Files

src/schema/models.py
src/schema/extractor.py
tests/schema/test_extractor.py

## Completed

- Created SchemaTable model.
- Created SchemaColumn model.
- Implemented table discovery.
- Implemented column type extraction.

## Current Problem

Foreign-key relationships are not yet represented correctly
for composite relationships.

## Next Step

Inspect SQLAlchemy relationship metadata and implement FK extraction.

## Constraints

Do not introduce a second ORM.

Do not expose SQLAlchemy-specific objects outside the schema
extraction infrastructure.

## Verification

Current tests:

8 passed

Last command:

pytest tests/schema/

-------------------------------------

3. DECISIONS.md

This project will accumulate a lot of decisions.
For example:

# Architectural Decisions

## ADR-001 — Database

Decision:
Use PostgreSQL.

Reason:
Production-like relational database with EXPLAIN,
permissions, transactions and realistic SQL behavior.

---

## ADR-002 — SQL Parsing

Decision:
Use sqlglot for SQL parsing and validation.

Reason:
Need structural SQL analysis rather than relying only
on string matching.

---

## ADR-003 — Database Safety

Decision:
Use both application-level guardrails and a read-only
database role.

Reason:
Defense in depth.

Application validation can fail.
Database permissions provide the final safety boundary.

---

## ADR-004 — LLM Output

Decision:
LLM must return structured output rather than raw SQL.

Fields:

- sql
- explanation
- confidence
- tables
- columns

Reason:
Makes downstream validation deterministic and observable.

Notice something important:

Don't rewrite old decisions casually.

If a decision changes, append:

## ADR-009 — Supersedes ADR-002

...

-------------------------------------

4. CONTRACTS.md
Example:
# System Contracts

## GeneratedSQL

```json
{
  "sql": "string",
  "explanation": "string",
  "confidence": "number",
  "tables": ["string"],
  "columns": ["string"]
}

GuardrailResult
{
  "allowed": "boolean",
  "violations": ["string"],
  "warnings": ["string"]
}

QueryResult

Must contain:

rows
row_count
execution_time_ms
explain_plan
validation
confidence
API

POST /v1/query

Input:

{
"question": "string"
}

Output:

{
"sql": "string",
"results": [],
"confidence": {},
"warnings": []
}

This prevents llm model from accidentally changing an interface I established three sessions ago.

--------------------------------------

# 5. `EVALUATION.md`

This is another thing I would **definitely** persist.

For example:

```md
# Evaluation

## Dataset

Golden queries: 50

Last evaluation:

2026-09-20

## Metrics

Execution accuracy: 82%

SQL exact match: 61%

Unsafe queries blocked: 100%

Hallucination detection: 76%

## Known Failures

1. Nested aggregation
2. Date range interpretation
3. Revenue ambiguity
4. LEFT JOIN vs INNER JOIN
5. NULL aggregation

## Regression Cases

Added:
- test_023
- test_031
- test_044

-----------------------------------

6. AGENTS.md

Something like:

# Project Instructions

## Before Starting Work

Read:

1. docs/memory/PROJECT_STATE.md
2. docs/memory/CURRENT_TASK.md
3. docs/memory/DECISIONS.md
4. docs/memory/CONTRACTS.md

Only read EVALUATION.md when working on evaluation,
generation accuracy, prompts, or validation.

## Before Making Changes

Verify the memory against the actual code.

Never blindly trust the memory ledger.

The source of truth for implementation is the code.

## Safety

Generated SQL must never be executed before guardrails.

Never weaken database permissions.

Never remove a guardrail merely to make a test pass.

Never bypass validation without explicitly documenting
the reason.

## After Meaningful Work

Update CURRENT_TASK.md.

Update PROJECT_STATE.md if project progress changed.

Update DECISIONS.md if an architectural decision was made.

Update CONTRACTS.md if an API/interface contract changed.

Update EVALUATION.md when evaluation results change.

Keep memory concise.

Do not record conversational history.

Record state, decisions, constraints, failures,
and next actions.