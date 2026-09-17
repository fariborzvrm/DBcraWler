from datetime import date

import pytest
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    insert,
)

from dbcrawler.schema.extractor import extract_schema
from dbcrawler.schema.models import SchemaRepresentation


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite://")
    metadata = MetaData()
    Table(
        "customers",
        metadata,
        Column("customer_id", String, primary_key=True),
        Column("company_name", String, nullable=False),
        Column("city", String),
    )
    orders = Table(
        "orders",
        metadata,
        Column("order_id", Integer, primary_key=True),
        Column("order_date", Date, primary_key=True),
        Column("customer_id", String, ForeignKey("customers.customer_id")),
        Column("freight", Numeric),
    )
    Table(
        "order_details",
        metadata,
        Column("order_id", Integer),
        Column("product_id", Integer),
        Column("quantity", Integer, nullable=False),
    )
    metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(
            insert(orders).values(
                order_id=1, order_date=date(2024, 1, 1), customer_id=None, freight=None
            )
        )
        conn.commit()
    return engine


def test_extract_tables(sqlite_engine):
    schema = extract_schema(sqlite_engine)
    names = [t.name for t in schema.tables]
    assert names == ["customers", "order_details", "orders"]


def test_columns_and_types(sqlite_engine):
    schema = extract_schema(sqlite_engine)
    customers = next(t for t in schema.tables if t.name == "customers")
    types = {c.name: c.type for c in customers.columns}
    assert types["customer_id"] == "VARCHAR"
    assert customers.columns[0].primary_key is True
    assert customers.columns[2].nullable is True


def test_foreign_keys_and_relationships(sqlite_engine):
    schema = extract_schema(sqlite_engine)
    orders = next(t for t in schema.tables if t.name == "orders")
    cid = next(c for c in orders.columns if c.name == "customer_id")
    assert cid.foreign_keys[0].references_table == "customers"
    assert cid.foreign_keys[0].references_column == "customer_id"
    rels = [(r.from_table, r.to_table) for r in schema.relationships]
    assert ("orders", "customers") in rels


def test_composite_pk(sqlite_engine):
    schema: SchemaRepresentation = extract_schema(sqlite_engine)
    orders = next(t for t in schema.tables if t.name == "orders")
    pks = [c.name for c in orders.columns if c.primary_key]
    assert set(pks) == {"order_id", "order_date"}


def test_text_renderer_basic(sqlite_engine):
    from dbcrawler.schema.representation import render_schema_text

    schema = extract_schema(sqlite_engine)
    text_out = render_schema_text(schema)
    assert "customers" in text_out and "customer_id" in text_out
