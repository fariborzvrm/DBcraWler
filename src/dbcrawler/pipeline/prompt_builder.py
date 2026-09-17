"""Dynamic prompt construction from the relevant schema (plan.md Phase 1 §2).

Deterministic; the only LLM-relevant randomness is none - temperature 0 elsewhere.
"""

import json
from pathlib import Path

FEW_SHOT_PATH = Path("data/few_shot/northwind.json")

SYSTEM_PROMPT = """You are a precise PostgreSQL query writer.
Rules:
- Generate SELECT-only PostgreSQL SQL.
- Reference only tables and columns present in the provided schema.
- Use schema-qualified joins based on the listed relationships only.
- Never invent columns or values.
- If an aggregation like "revenue" is ambiguous, the SQL must state its interpretation in the explanation.
- Validate output strictly against the JSON schema.
"""

PROMPT_HEADER = """Below is the relevant schema for the database.

{schema_text}

Owned business glossary:
- revenue := SUM(unit_price * quantity * (1 - discount)) over order_details joined to orders (gross, before freight).
- segment := customers.segment, one of Retail / Wholesale / Restaurant / Distribution.

"""

PROMPT_TASK = """Question: {question}

Write one PostgreSQL SELECT query answering the question with the schema above.
"""


def load_few_shot(path: Path = FEW_SHOT_PATH) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("examples", [])


def build_prompt(
    schema_text: str,
    question: str,
    max_few_shot: int = 5,
    few_shot_path: Path = FEW_SHOT_PATH,
) -> str:
    examples = load_few_shot(few_shot_path)[:max_few_shot]
    few_shot_block = []
    for ex in examples:
        few_shot_block.append(
            f"Example question: {ex['question']}\nExample SQL:\n{ex['sql']}"
        )
    few_shot_str = "\n\n".join(few_shot_block)
    return (
        PROMPT_HEADER.format(schema_text=schema_text)
        + "\n"
        + ("FEW-SHOT EXAMPLES:\n" + few_shot_str + "\n\n" if few_shot_str else "")
        + PROMPT_TASK.format(question=question)
    )
