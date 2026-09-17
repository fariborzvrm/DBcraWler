"""SQL syntax/structure validation via sqlglot (ADR-011).

Parses the dialect we actually execute against (postgres); failures
are reported per statement and never raise.
"""

import sqlglot
from pydantic import BaseModel, Field, PrivateAttr
from sqlglot import exp


class SQLValidationResult(BaseModel):
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    statements: list[str] = Field(default_factory=list)

    _parsed: list[exp.Expression | None] = PrivateAttr(default_factory=list)

    @property
    def parsed(self) -> list[exp.Expression | None]:
        """Parse trees aligned 1:1 with `statements`/errors order."""
        return self._parsed


def validate_sql(sql: str, dialect: str = "postgres") -> SQLValidationResult:
    """Parse SQL and report syntax errors without raising."""
    stripped = (sql or "").strip()
    if not stripped:
        return SQLValidationResult(is_valid=False, errors=["SQL is empty"])

    try:
        nodes = sqlglot.parse(stripped, dialect=dialect)
    except sqlglot.errors.ParseError as exc:
        return SQLValidationResult(is_valid=False, errors=[f"SQL syntax error: {exc}"])

    errors: list[str] = []
    statements: list[str] = []
    for index, node in enumerate(nodes, start=1):
        if node is None:
            errors.append(f"statement {index}: could not be parsed")
            continue
        statements.append(node.sql(dialect=dialect))

    result = SQLValidationResult(
        is_valid=not errors, errors=errors, statements=statements
    )
    result._parsed = list(nodes)
    return result
