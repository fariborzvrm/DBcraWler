"""SQL-to-question verification (plan.md Phase 3 §1).

Back-translate the generated SQL into a natural-language question and
have the LLM compare it with the user's original question. Divergence
signals an intent mismatch (hallucinated translation).
"""

from pydantic import BaseModel, ValidationError

from dbcrawler.llm.client import OpenRouterClient

BACKTRANSLATE_SCHEMA = {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"],
    "additionalProperties": False,
}

ALIGNMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "explanation": {"type": "string"},
    },
    "required": ["score", "explanation"],
    "additionalProperties": False,
}

BACKTRANSLATE_PROMPT = """You read one SQL SELECT query and answer with the
one natural-language question this query answers. Describe the *outcome*,
not the mechanics (avoid words like "query", "column", "row"). Question only.
"""


class IntentVerification(BaseModel):
    back_translated_question: str
    alignment_score: float
    explanation: str


def verify_intent(
    client: OpenRouterClient, question: str, sql: str
) -> IntentVerification:
    translated = client.generate_structured(
        "Restate this SQL SELECT query as the single natural-language "
        "question a user would have asked to get exactly this answer.",
        f"SQL:\n{sql}",
        BACKTRANSLATE_SCHEMA,
        "backtranslation",
    )
    if isinstance(translated, dict) and "question" in translated:
        back_question = str(translated["question"])
    else:
        return IntentVerification(
            back_translated_question="",
            alignment_score=0.0,
            explanation="malformed back-translation payload",
        )

    payload = client.generate_structured(
        SYSTEM_PROMPT,
        f"USER QUESTION: {question}\n\nBACK-TRANSLATED QUESTION: {back_question}",
        ALIGNMENT_SCHEMA,
        "alignment",
    )
    try:
        result = IntentVerification.model_validate(
            {
                "back_translated_question": back_question,
                "alignment_score": payload["score"],
                "explanation": payload.get("explanation", ""),
            }
        )
    except (KeyError, ValidationError, TypeError) as exc:
        return IntentVerification(
            back_translated_question=back_question,
            alignment_score=0.0,
            explanation=f"malformed alignment payload: {exc}",
        )
    return result


SYSTEM_PROMPT = """You compare a user's question with a question that was
back-translated from generated SQL.
score = 1.0 means the two questions request the same answer.
score = 0.0 means completely different intents.
Penalize (below 0.5) any divergence in: metric (count/sum/avg), measured
entity, filter conditions, time ranges, grouping.
Briefly explain any divergence in one sentence.
"""
