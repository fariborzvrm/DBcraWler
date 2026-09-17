# Project 8 — Text-to-SQL Interface with Guardrails and Hallucination Detection

## What You’re Building

A natural-language interface that translates plain-English questions into SQL against a real database.

The system must:

- Generate SQL from natural-language questions.
- Execute queries safely with guardrails preventing destructive operations.
- Validate that generated SQL actually answers the user's question.
- Present results together with a confidence score.
- Detect likely hallucinations or incorrect intent translations before returning results.

The project demonstrates production-oriented Text-to-SQL with safety, validation, observability, and evaluation rather than simply calling an LLM to generate SQL.

---

# Tech Stack

- **Language:** Python 3.11+
- **LLM:** GPT-4o or Claude Sonnet
- **Database:** PostgreSQL or DuckDB
  - Real SQL engine, not a SQLite toy.
- **Schema Extraction:** SQLAlchemy
- **Guardrails:** Custom middleware
- **Validation:** LLM-as-judge + result checks
- **API:** FastAPI
- **Containerization:** Docker + docker-compose

---

# Phase 1 — Schema-Aware Prompt Engine

## Day 1–3

### 1. Auto-extract Database Schema

Use SQLAlchemy to extract:

- Tables
- Columns and their types
- Primary-key relationships
- Foreign-key relationships
- Sample values for categorical columns

The extracted schema becomes structured context for the LLM.

### 2. Dynamic Prompt Constructor

Construct prompts using the relevant schema rather than blindly including the entire database.

The prompt should include:

- Relevant schema
- Foreign-key relationships
- Sample values for disambiguation
- Column descriptions / business glossary
- 3–5 few-shot question → SQL examples specific to the schema

### 3. Schema Filtering

For large databases:

- Embed the user's question.
- Embed table/column descriptions.
- Select only tables above a similarity threshold.
- Provide the focused schema to the LLM.

The goal is to improve SQL generation accuracy by reducing irrelevant context.

### 4. Explicit Ambiguity Handling

If a question can map to multiple interpretations, do not guess.

Example:

> "What is our revenue?"

Possible interpretations:

- Gross revenue
- Net revenue

Return a structured clarification request containing the possible interpretations and example queries.

---

# Phase 2 — SQL Generation and Safety Layer

## Day 3–6

### 1. Structured Output

Use Instructor or function calling to produce structured output containing:

- SQL query
- Natural-language explanation
- Confidence score
- Accessed tables
- Accessed columns

Validate SQL syntax using `sqlparse`.

### 2. Guardrail Middleware

Guardrails must run **before execution**.

The middleware should:

- Block all DDL:
  - `CREATE`
  - `ALTER`
  - `DROP`
- Block all DML writes:
  - `INSERT`
  - `UPDATE`
  - `DELETE`
- Enforce a row limit, e.g. `LIMIT 1000`, when one is not specified.
- Reject subqueries deeper than 3 levels.
- Block queries estimated to scan more than a configurable number of rows using `EXPLAIN`.
- Make each rule configurable.
- Log every blocked query together with the reason.

### 3. Query Sandboxing

Use multiple layers of protection:

1. Execute generated queries in a read-only transaction that rolls back automatically.
2. Use a database user with SELECT-only permissions.

Database permissions provide a second defense if the application-level guardrail layer misses something.

### 4. Execution Layer

Execute validated SQL and capture:

- Results as a DataFrame
- Raw results capped at the configured row limit
- Execution time
- Number of rows returned
- EXPLAIN plan

Log the execution information for auditability.

---

# Phase 3 — Hallucination Detection System

## Day 6–9

### 1. SQL-to-Question Verification

Send the generated SQL back to the LLM with a request equivalent to:

> What question does this SQL query answer?

Then compare the back-translated question against the original user question.

If there is significant divergence:

- Treat it as a likely intent mismatch.
- Score the alignment.
- Flag low-confidence translations.

### 2. Result Sanity Checking

Check whether the returned results are plausible.

Examples:

- Are aggregated values within a plausible magnitude?
- Are counts within an expected range?
- Are date ranges within the actual data timespan?
- Are there unusually many NULL values that could indicate a bad JOIN?

Flag anomalies with specific explanations.

### 3. Multi-Query Validation

For complex questions:

- Generate two independent SQL approaches.
- Use different JOIN / aggregation strategies where appropriate.
- Execute both.
- Compare the results.

If the results match:

- Increase confidence.

If they diverge:

- Flag the discrepancy.
- Present both results and explanations.

### 4. Confidence Score

Combine signals such as:

- SQL syntax validity
- SQL-to-question back-translation alignment
- Result sanity pass rate
- Multi-query agreement
- Schema coverage
  - Did the query use the expected tables and columns?

Display the confidence score prominently.

---

# Phase 4 — Query Interface

## Day 9–11

## API Endpoints

### `POST /v1/query`

Accepts:

- Natural-language question

Returns:

- Generated SQL
- Execution results
- Confidence score
- Guardrail warnings

### `GET /v1/schema`

Returns:

- Database schema

### `GET /v1/history`

Returns:

- Past queries
- Past results for the session

## Frontend

Use Streamlit or React.

The UI should contain:

- Natural-language question input
- Generated SQL with syntax highlighting
- Editable SQL for power users
- Sortable result table
- Confidence score
- Confidence breakdown
- Query history panel

## Feedback Loop

Allow the user to mark a result as:

- Correct
- Incorrect

Store the feedback alongside the query.

Use feedback to create a flywheel:

```text
Incorrect result
      ↓
New evaluation test case
      ↓
Regression suite

Correct result
      ↓
New few-shot example
      ↓
Improved future generation
```

---

# Phase 5 — Evaluation Suite

## Day 11–13

### 1. Golden Query Dataset

Create at least 50 natural-language questions with:

- Verified correct SQL
- Expected results

The dataset should include:

- Simple lookups
- Multi-table JOINs
- GROUP BY aggregations
- Date-range filters
- Ambiguous phrasing
- Questions the database cannot answer

This becomes the regression suite.

### 2. Automated Evaluations

Measure:

#### SQL Exact Match

Compare generated SQL against the golden SQL.

#### Execution Match

Check whether generated SQL produces the expected results, even when the SQL structure differs.

#### Hallucination Detection Rate

Measure whether bad queries are correctly flagged.

#### Guardrail Effectiveness

Measure whether dangerous queries are blocked.

---

# Phase 6 — Containerization and Documentation

## Day 13–14

Use Docker Compose with:

- PostgreSQL seeded with sample data
- FastAPI service
- Frontend

The README should report evaluation numbers such as:

- Execution accuracy
- Hallucination detection rate
- Number of unsafe queries blocked

Example framing from the project guide:

> X% execution accuracy, Y% hallucination detection rate, zero unsafe queries across Z tests.

These are reporting examples, not required target values.

---

# Phase 7 — Portfolio Polish

## Demo

Keep the demo under 4 minutes.

Show:

1. Natural language → SQL
2. Guardrail blocking a dangerous query
3. Hallucination detector catching a bad translation
4. Multi-query validation resolving a discrepancy

## Portfolio Narrative

A possible framing is:

> I built a Text-to-SQL system with a X% accuracy rate that blocks 100% of destructive operations and detects Y% of hallucinated queries before they reach the user.

The project guide emphasizes leading with safety because production systems need to avoid destructive or unsafe behavior, not merely generate accurate SQL.

---

# Overall Architecture

```text
User
  │
  ▼
Natural-Language Question
  │
  ▼
Ambiguity Detection
  │
  ├── Ambiguous → Clarification
  │
  ▼
Schema Filtering
  │
  ▼
Relevant Schema
  │
  ▼
Prompt Constructor
  │
  ▼
LLM
  │
  ▼
Structured SQL + Metadata
  │
  ▼
SQL Syntax Check
  │
  ▼
Guardrails
  │
  ├── Block → Log reason → Return warning
  │
  ▼
Read-Only Database User
  │
  ▼
SQL Execution
  │
  ▼
Validation
  │
  ├── SQL → Question verification
  ├── Result sanity checks
  ├── Multi-query validation
  └── Schema coverage
  │
  ▼
Confidence Score
  │
  ▼
Results + SQL + Warnings
  │
  ▼
User Feedback
  │
  ├── Incorrect → Evaluation Dataset
  │
  └── Correct → Few-Shot Examples
```

---

# Core Mental Model

This project is **not**:

```text
Question → LLM → SQL → Database
```

It is:

```text
Question
   ↓
Understand Schema
   ↓
Understand Intent
   ↓
Generate SQL
   ↓
Prove It Is Safe
   ↓
Execute Safely
   ↓
Check Whether It Answered the Intent
   ↓
Check Result Sanity
   ↓
Cross-Check Complex Queries
   ↓
Calculate Confidence
   ↓
Return Result
   ↓
Learn From Feedback
   ↓
Regression Testing
```

The key idea is that Text-to-SQL should be treated as a **guarded and validated pipeline**, not as a single LLM generation step.

---

# Project Outcome

By the end of Project 8, the system should demonstrate:

- Schema-aware SQL generation
- Dynamic schema filtering
- Explicit ambiguity handling
- Structured LLM output
- SQL syntax validation
- Destructive-operation protection
- Query cost / scan protection
- Read-only database isolation
- SQL-to-question verification
- Result sanity checking
- Multi-query validation
- Confidence scoring
- Query history
- User feedback
- Golden evaluation datasets
- Automated regression evaluation
- Dockerized deployment

The project guide presents this as a **14-day blueprint**. It describes the components and implementation goals; implementation details and engineering decisions are left to the developer.
