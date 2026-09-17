from dbcrawler.pipeline.schema_filter import SchemaFilterSelection, subselect_schema
from dbcrawler.schema.models import Relationship, SchemaRepresentation, SchemaTable


def _schema() -> SchemaRepresentation:
    orders = SchemaTable(name="orders")
    customers = SchemaTable(name="customers")
    unrelated = SchemaTable(name="unrelated")
    tables = [customers, unrelated, orders]
    rels = [
        Relationship(
            from_table="orders",
            from_column="customer_id",
            to_table="customers",
            to_column="customer_id",
        )
    ]
    return SchemaRepresentation(tables=tables, relationships=rels)


def test_subselect_includes_fk_neighbors():
    schema = _schema()
    selection = SchemaFilterSelection(
        selected_tables=["orders"], threshold=0.3, scores={}
    )
    focused = subselect_schema(schema, selection)
    names = {t.name for t in focused.tables}
    assert names == {"orders", "customers"}
    assert len(focused.relationships) == 1


def test_subselect_drops_dangling_relationships():
    schema = _schema()
    selection = SchemaFilterSelection(
        selected_tables=["unrelated"], threshold=0.3, scores={}
    )
    focused = subselect_schema(schema, selection)
    names = {t.name for t in focused.tables}
    assert "unrelated" in names and "orders" not in names
    assert focused.relationships == []


def test_cosine_similarity_directional():
    from dbcrawler.pipeline.schema_filter import _cosine

    a = [1.0, 0.0]
    assert _cosine(a, a) == 1.0
    assert _cosine(a, [-1.0, 0.0]) == -1.0
    assert _cosine([0.0, 0.0], a) == 0.0


def test_subselect_empty_selection_returns_full_schema():
    schema = _schema()
    selection = SchemaFilterSelection(selected_tables=[], threshold=0.3, scores={})
    focused = subselect_schema(schema, selection)
    assert {t.name for t in focused.tables} == {"orders", "customers", "unrelated"}
    assert len(focused.relationships) == 1
