"""Sample value extraction for categorical columns.

Only queries text columns that are likely low-cardinality / categorical
and caps the number of returned values with LIMIT.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from dbcrawler.config.settings import Settings
from dbcrawler.schema.models import SchemaTable

# Rows scanned when collecting distinct candidates before LIMIT.
# Small, fixed scan cap so sampling never becomes a full-table job.


def _candidates(table: SchemaTable) -> list[str]:
    out = []
    for col in table.columns:
        t = col.type.lower()
        if ("char" in t or "text" in t) and not col.primary_key:
            out.append(col.name)
    return out


def sample_categorical_values(
    engine: Engine,
    tables: list[SchemaTable],
    settings: Settings | None = None,
) -> None:
    settings = settings or Settings()
    limit = settings.sample_values_per_column
    with engine.connect() as conn:
        for table in tables:
            for col_name in _candidates(table):
                query = text(
                    f"SELECT DISTINCT {col_name} "
                    f"FROM {table.name} WHERE {col_name} IS NOT NULL LIMIT {int(limit)}"
                )
                values = [row[0] for row in conn.execute(query)]
                for col in table.columns:
                    if col.name == col_name:
                        col.sample_values = [str(v) for v in values]
