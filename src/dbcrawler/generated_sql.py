"""GeneratedSQL contract (Phase 2).

Structured LLM output for SQL generation. Raw LLM payloads must pass
through `GeneratedSQL.from_llm` so malformed output fails loudly instead
of crashing later in the guardrail/execution pipeline.
"""

from pydantic import BaseModel, Field, ValidationError


class GeneratedSQL(BaseModel):
    sql: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    tables: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)

    @classmethod
    def from_llm(cls, payload: dict) -> "GeneratedSQL":
        """Validate a raw LLM payload dict, raising ValueError on malformation."""
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            missing = [f"{err['loc'][0]} ({err['type']})" for err in exc.errors()]
            raise ValueError(
                f"LLM returned malformed GeneratedSQL payload: {missing}"
            ) from exc
