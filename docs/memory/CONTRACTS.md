# System Contracts

## SchemaRepresentation

The structured schema extracted from the database.
Locked contract for Phase 1; all later phases consume this.

```json
{
  "tables": [
    {
      "name": "string",
      "description": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "nullable": "boolean",
          "primary_key": "boolean",
          "foreign_keys": [
            {
              "references_table": "string",
              "references_column": "string"
            }
          ],
          "sample_values": ["string"]
        }
      ]
    }
  ],
  "relationships": [
    {
      "from_table": "string",
      "from_column": "string",
      "to_table": "string",
      "to_column": "string"
    }
  ]
}
```

## AmbiguityResult

Phase 1 ambiguity detection output.

```json
{
  "is_ambiguous": "boolean",
  "interpretations": [
    {
      "description": "string",
      "example_sql": "string"
    }
  ]
}
```

## SchemaFilterSelection

Phase 1 schema filtering output.

```json
{
  "selected_tables": ["string"],
  "threshold": "number",
  "scores": { "table_name": "number" }
}
```

FK-neighbors of selected tables are always included so joins remain valid.

## GeneratedSQL

Phase 2 structured LLM output. Pydantic model
`dbcrawler.generated_sql.GeneratedSQL`, built from raw LLM dict via
`GeneratedSQL.from_llm(payload)` (raises `ValueError` with a clear message
for malformed payloads).

```json
{
  "sql": "string",
  "explanation": "string",
  "confidence": 0.0,
  "tables": ["string"],
  "columns": ["string"]
}
```

Constraints: `0.0 <= confidence <= 1.0`.

## SQLValidationResult

Phase 2 output of `dbcrawler.guardrails.validator.validate_sql(sql, dialect)`.
Dialect defaults to `postgres` (ADR-001).

```json
{
  "is_valid": "boolean",
  "errors": ["string"],
  "statements": ["string"]
}
```

`statements` contains re-rendered SQL for successfully parsed statements.

## GuardrailResult

Phase 2 output of `dbcrawler.guardrails.check_guardrails(sql, settings)`.
Fail-closed: unparseable, non-single-statement, unknown/non-SELECT, or
rule-violating SQL is blocked with logged reasons.

```json
{
  "allowed": "boolean",
  "violations": ["string"],
  "warnings": ["string"],
  "enforced_sql": "string"
}
```

`enforced_sql` is the executable variant (LIMIT injected/clamped to
`settings.guardrail_max_limit_rows` when missing or too large); empty when
not allowed.

## QueryResult

Phase 2 output of `dbcrawler.guardrails.executor.execute_sql`. Rows are
hard-capped at `settings.guardrail_max_limit_rows`.

```json
{
  "sql": "string",
  "rows": [{ "column": "value" }],
  "row_count": 0,
  "truncated": "boolean",
  "execution_time_ms": 0.0,
  "explain_plan": "string",
  "validation": { "GuardrailResult dump when enforced, else null" }
}
```

## IntentVerification

Phase 3 output of `dbcrawler.validation.backtranslator.verify_intent`.

```json
{
  "back_translated_question": "string",
  "alignment_score": 0.0,
  "explanation": "string"
}
```

## SanityResult

Phase 3 output of `dbcrawler.validation.sanity.check_result_sanity`
(deterministic, no LLM).

```json
{
  "findings": [{ "check": "string", "passed": true, "message": "string" }]
}
```

`pass_rate` = fraction of passed findings (1.0 when no findings).
Check ids: `has_rows`, `null_heavy`, `magnitude`.

## MultiQueryResult

Phase 3 output of `dbcrawler.validation.multiquery.compare_results`.

```json
{
  "ran": true,
  "agree": false,
  "first_sql": "string",
  "second_sql": "string",
  "detail": "string"
}
```

## ConfidenceBreakdown

Phase 3 output of `dbcrawler.confidence.compute_confidence`.
Final score in [0,1]; `llm_self_report` is only one weighted signal.
Neutral alignment (0.5) is used if back-translation is unavailable;
multiquery weight is dropped (renormalized) when it did not run.

```json
{
  "final": 0.0,
  "llm_self_report": 0.0,
  "intent_alignment": 0.0,
  "sanity_pass_rate": 0.0,
  "schema_coverage": 0.0,
  "multiquery_agreement": true
}
```

## VerifiedQuery

Phase 3 orchestration output (`dbcrawler.validation.runner.run_validation`):
bundles `query_result`, `sanity`, `intent`, `multiquery`, `confidence`,
`warnings`. Multi-query path executes the alternative SQL through the
same `check_guardrails` → `execute_sql` chain.

## Reserve (future phases — do not break)

API POST /v1/query (Phase 4): input {question}, output {sql, results, confidence, warnings}.
