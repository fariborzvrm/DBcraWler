"""SQLAlchemy inspector -> SchemaRepresentation.

This is the only boundary where SQLAlchemy objects are used; everything
downstream (prompt builder, filtering, ambiguity detection) works with
the SchemaRepresentation contract (docs/memory/CONTRACTS.md).
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from dbcrawler.config.settings import Settings
from dbcrawler.schema.models import (
    ForeignKeyRef,
    Relationship,
    SchemaColumn,
    SchemaRepresentation,
    SchemaTable,
)
from dbcrawler.schema.sampler import sample_categorical_values


def _normalized_type(sa_type: object) -> str:
    return str(sa_type).upper()


def _extract_table(conn, inspector, table_name: str) -> SchemaTable:
    pk_cols = set(inspector.get_pk_constraint(table_name)["constrained_columns"] or [])
    fks = inspector.get_foreign_keys(table_name)
    fk_by_column: dict[str, list[ForeignKeyRef]] = {}
    for fk in fks:
        src_cols = fk["constrained_columns"]
        dst_cols = fk["referred_columns"]
        ref_table = fk["referred_table"]
        dst_repeated = [ref_table] * len(src_cols)
        for src, dst, table in zip(src_cols, dst_cols, dst_repeated, strict=False):
            fk_by_column.setdefault(src, []).append(
                ForeignKeyRef(references_table=table, references_column=dst)
            )
    columns = [
        SchemaColumn(
            name=col["name"],
            type=_normalized_type(col["type"]),
            nullable=col.get("nullable", True),
            primary_key=col["name"] in pk_cols,
            foreign_keys=fk_by_column.get(col["name"], []),
        )
        for col in inspector.get_columns(table_name)
    ]
    return SchemaTable(name=table_name, description="", columns=columns)


def extract_schema(
    engine: Engine, settings: Settings | None = None
) -> SchemaRepresentation:
    settings = settings or Settings()
    inspector = inspect(engine)
    table_names = sorted(inspector.get_table_names())
    with engine.connect():
        pass  # fail fast with a clear connection error before iteration below
    tables = [_extract_table(engine, inspector, name) for name in table_names]

    relationships = [
        Relationship(
            from_table=table.name,
            from_column=col.name,
            to_table=ref.references_table,
            to_column=ref.references_column,
        )
        for table in tables
        for col in table.columns
        for ref in col.foreign_keys
    ]

    schema = SchemaRepresentation(tables=tables, relationships=relationships)
    return schema


def extract_schema_url(
    url: str, settings: Settings | None = None
) -> SchemaRepresentation:
    engine = create_engine(url)
    try:
        schema = extract_schema(engine, settings)
        sample_categorical_values(engine, schema.tables, settings)
        return schema
    finally:
        engine.dispose()
