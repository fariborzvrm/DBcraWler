"""Embedding-based schema filtering.

Index-time: embed a one-line description per table, cache by content hash.
Query-time: embed the question, rank tables by cosine similarity, keep
tables above the threshold, then add FK neighbors so joins stay valid.

Output contract: SchemaFilterSelection (docs/memory/CONTRACTS.md).
"""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field

from dbcrawler.config.settings import Settings
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.schema.models import SchemaRepresentation, SchemaTable


class SchemaFilterSelection(BaseModel):
    selected_tables: list[str] = Field(default_factory=list)
    threshold: float = 0.3
    scores: dict[str, float] = Field(default_factory=dict)


def _table_summary(table: SchemaTable) -> str:
    cols = ", ".join(f"{c.name} {c.type}" for c in table.columns)
    return f"{table.name}: {cols}"


def _cache_path(settings: Settings) -> Path:
    return Path(".schema_embeddings_cache.json")


def get_table_embeddings(
    schema: SchemaRepresentation, client: OpenRouterClient, settings: Settings
) -> dict[str, list[float]]:
    cache_file = _cache_path(settings)
    cache: dict[str, object] = {}
    if cache_file.exists():
        cache = json.loads(cache_file.read_text(encoding="utf-8"))

    table_names = [t.name for t in schema.tables]
    summaries = {t.name: _table_summary(t) for t in schema.tables}
    missing = [
        name
        for name in table_names
        if hashlib.sha1((name + summaries[name]).encode()).hexdigest() not in cache
    ]

    if missing:
        vectors = client.embed([summaries[name] for name in missing])
        cache.update(
            {
                hashlib.sha1((name + summaries[name]).encode()).hexdigest(): v
                for name, v in zip(missing, vectors)
            }
        )
        cache_file.write_text(json.dumps(cache), encoding="utf-8")

    result = {}
    for name in table_names:
        result[name] = cache[
            hashlib.sha1((name + summaries[name]).encode()).hexdigest()
        ]
    return result


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def filter_tables(
    schema: SchemaRepresentation,
    question: str,
    client: OpenRouterClient,
    settings: Settings | None = None,
) -> SchemaFilterSelection:
    settings = settings or Settings()
    table_vecs = get_table_embeddings(schema, client, settings)
    query_vec = client.embed_query(question)

    scores = {name: _cosine(query_vec, vec) for name, vec in table_vecs.items()}
    above = [
        name for name, score in scores.items() if score >= settings.similarity_threshold
    ]

    return SchemaFilterSelection(
        selected_tables=sorted(set(above)),
        threshold=settings.similarity_threshold,
        scores=scores,
    )


def expand_fk_neighbors(schema: SchemaRepresentation, selected: list[str]) -> list[str]:
    """FK-side expansion: any table structurally joined to a selected table."""
    names = set(selected)
    for rel in schema.relationships:
        if rel.from_table in names and rel.to_table not in names:
            names.add(rel.to_table)
        if rel.to_table in names and rel.from_table not in names:
            names.add(rel.from_table)
    return sorted(names)


def subselect_schema(
    schema: SchemaRepresentation, selection: SchemaFilterSelection
) -> SchemaRepresentation:
    if not selection.selected_tables:
        # Fallback: nothing cleared the threshold - never feed the LLM an
        # empty schema. Better too much context than none.
        return schema
    keep = set(expand_fk_neighbors(schema, selection.selected_tables))
    tables = [t for t in schema.tables if t.name in keep]
    rels = [
        r for r in schema.relationships if r.from_table in keep and r.to_table in keep
    ]
    return SchemaRepresentation(tables=tables, relationships=rels)
