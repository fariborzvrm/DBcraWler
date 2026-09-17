"""Phase 1+2 end-to-end demo.

Usage:
    uv run python -m dbcrawler.demo "How many customers in Germany?"
    uv run python -m dbcrawler.demo "What is our revenue?"   # ambiguous -> clarification
    uv run python -m dbcrawler.demo "How many customers in Germany?" --execute
"""

import sys

from dbcrawler.config.settings import get_settings
from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.guardrails import ExecutionBlocked, check_guardrails, execute_sql
from dbcrawler.llm.ambiguity import check_ambiguity
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.pipeline.prompt_builder import SYSTEM_PROMPT, build_prompt
from dbcrawler.pipeline.schema_filter import filter_tables, subselect_schema
from dbcrawler.schema.extractor import extract_schema_url
from dbcrawler.schema.representation import render_schema_text

SQL_GEN_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "explanation": {"type": "string"},
        "confidence": {"type": "number"},
        "tables": {"type": "array", "items": {"type": "string"}},
        "columns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sql", "explanation", "confidence", "tables", "columns"],
    "additionalProperties": False,
}


def main() -> None:
    execute_mode = "--execute" in sys.argv[1:]
    question = (
        " ".join(arg for arg in sys.argv[1:] if arg != "--execute")
        or "How many customers are registered in Germany?"
    )
    settings = get_settings()
    client = OpenRouterClient(settings)

    print(
        f"\n[1/5] Extracting schema via SQLAlchemy (read-only user: {settings.db_url.split('//')[1].split('@')[0]})"
    )
    schema = extract_schema_url(settings.db_url, settings)

    print("[2/5] Filtering schema with nemotron embeddings")
    selection = filter_tables(schema, question, client, settings)
    focused = subselect_schema(schema, selection)
    top = sorted(selection.scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
    print(
        f"      selected={selection.selected_tables}  top_scores={[(n, round(s, 3)) for n, s in top]}"
    )

    print("[3/5] Ambiguity check")
    ambiguity = check_ambiguity(question, client, render_schema_text(focused))
    if ambiguity.is_ambiguous:
        print("      AMBIGUOUS - clarification request:")
        for inter in ambiguity.interpretations:
            print(
                f"        - {inter['description']}\n          e.g. {inter['example_sql'][:120]}..."
            )
        return

    prompt = build_prompt(render_schema_text(focused), question)
    print("[4/5] Generating SQL (LLM call)")
    generated = GeneratedSQL.from_llm(
        client.generate_structured(
            SYSTEM_PROMPT, prompt, SQL_GEN_SCHEMA, "generated_sql"
        )
    )

    print()
    print(generated.sql)
    print(f"\nexplanation: {generated.explanation}")
    print(
        f"confidence: {generated.confidence}  tables: {generated.tables}"
        f"  columns: {generated.columns[:8]}"
    )

    print("[5/5] Guardrails")
    guardrail = check_guardrails(generated.sql, settings)
    if not guardrail.allowed:
        print("      BLOCKED:")
        for violation in guardrail.violations:
            print(f"        - {violation}")
        return
    print(f"      allowed, enforced_sql: {guardrail.enforced_sql}")

    if not execute_mode:
        return

    print("[exec] Read-only sandboxed execution")
    try:
        query_result = execute_sql(
            guardrail.enforced_sql, settings, validation=guardrail.model_dump()
        )
    except (ExecutionBlocked, ValueError, OSError) as exc:
        print(f"      execution blocked/failed: {exc}")
        return
    print(f"      plan: {query_result.explain_plan}")
    print(
        f"      rows: {query_result.row_count}{' (truncated)' if query_result.truncated else ''}"
        f"  time: {query_result.execution_time_ms}ms"
    )
    for row in query_result.rows[:10]:
        print(f"        {row}")


if __name__ == "__main__":
    main()
