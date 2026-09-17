"""Text-to-SQL service used by both the CLI demo and the Phase 4 API.

Shared pipeline: schema extraction -> filtering -> ambiguity check ->
SQL generation -> guardrails -> guarded execution + validation.
Execution never happens before guardrails (AGENTS.md).
"""

from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.guardrails import check_guardrails
from dbcrawler.llm.ambiguity import AmbiguityResult, check_ambiguity
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.pipeline.prompt_builder import SYSTEM_PROMPT, build_prompt
from dbcrawler.pipeline.schema_filter import filter_tables, subselect_schema
from dbcrawler.schema.representation import render_schema_text
from dbcrawler.validation.runner import run_validation

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


def generate_sql(
    client: OpenRouterClient,
    settings,
    schema,
    question: str,
) -> GeneratedSQL:
    selection = filter_tables(schema, question, client, settings)
    focused = subselect_schema(schema, selection)
    prompt = build_prompt(render_schema_text(focused), question)
    return GeneratedSQL.from_llm(
        client.generate_structured(
            SYSTEM_PROMPT, prompt, SQL_GEN_SCHEMA, "generated_sql"
        )
    )


def check_question_ambiguity(
    client: OpenRouterClient,
    settings,
    schema,
    question: str,
) -> AmbiguityResult:
    selection = filter_tables(schema, question, client, settings)
    focused = subselect_schema(schema, selection)
    return check_ambiguity(question, client, render_schema_text(focused))


def execute_generated_sql(
    client: OpenRouterClient,
    settings,
    schema,
    question: str,
    generated: GeneratedSQL,
):
    """Guardrail gate -> guarded execution -> validation signals."""
    guardrail = check_guardrails(generated.sql, settings)
    if not guardrail.allowed:
        return {
            "status": "blocked",
            "query_result": None,
            "sanity": None,
            "intent": None,
            "multiquery": None,
            "confidence": None,
            "warnings": list(guardrail.violations),
        }
    verified = run_validation(
        client,
        settings,
        question,
        generated,
        guardrail.enforced_sql,
        schema,
    )
    status = "ok" if verified.query_result is not None else "execution_error"
    return {
        "status": status,
        "query_result": verified.query_result,
        "sanity": verified.sanity,
        "intent": verified.intent,
        "multiquery": verified.multiquery,
        "confidence": verified.confidence,
        "warnings": list(verified.warnings),
    }
