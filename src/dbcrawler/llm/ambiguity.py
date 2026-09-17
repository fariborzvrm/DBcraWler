"""Explicit ambiguity handling (plan.md Phase 1 §4).

If a question maps to multiple plausible SQL interpretations,
return a structured clarification request instead of guessing.

Contract: AmbiguityResult (docs/memory/CONTRACTS.md).
"""

from pydantic import BaseModel, Field

from dbcrawler.llm.client import OpenRouterClient

AMBIGUITY_SCHEMA = {
    "type": "object",
    "properties": {
        "is_ambiguous": {"type": "boolean"},
        "interpretations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "example_sql": {"type": "string"},
                },
                "required": ["description", "example_sql"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["is_ambiguous", "interpretations"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You analyze a natural-language question about a database,
given the actual database schema.

Mark is_ambiguous=true ONLY when the question maps to materially different
measurable outcomes on this schema (e.g. "revenue" without gross/net
qualification, or an actor/date that exists in multiple tables).
Do NOT mark ambiguous for:
- SQL dialect or syntax choices (LIMIT vs TOP vs FETCH FIRST)
- alternative column names or naming guesses
- different but equivalent formulations of the same answer

If ambiguous, list each possible interpretation with an example SELECT-only
SQL query that uses only tables and columns from the provided schema.
If not ambiguous, return is_ambiguous=false with an empty interpretations list.
"""


class AmbiguityResult(BaseModel):
    is_ambiguous: bool = False
    interpretations: list[dict] = Field(default_factory=list)


def check_ambiguity(
    question: str, client: OpenRouterClient, schema_text: str = ""
) -> AmbiguityResult:
    user_prompt = f"DATABASE SCHEMA:\n{schema_text}\n\nQuestion: {question}\n\nIs this question ambiguous on this schema?"
    payload = client.generate_structured(
        SYSTEM_PROMPT, user_prompt, AMBIGUITY_SCHEMA, "ambiguity"
    )
    return AmbiguityResult.model_validate(payload)
