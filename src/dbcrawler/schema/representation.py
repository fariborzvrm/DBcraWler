"""Render a SchemaRepresentation as compact text for LLM prompts."""


def render_table(table) -> str:
    lines = [
        f"TABLE {table.name}"
        + (f" -- {table.description}" if table.description else "")
    ]
    for col in table.columns:
        flags = []
        if col.primary_key:
            flags.append("PK")
        for fk in col.foreign_keys:
            flags.append(f"FK -> {fk.references_table}.{fk.references_column}")
        if not col.nullable:
            flags.append("NOT NULL")
        sample = ""
        if col.sample_values:
            vals = ", ".join(col.sample_values)
            sample = f" SAMPLE: {vals}"
        flags_str = (" [" + ", ".join(flags) + "]") if flags else ""
        lines.append(f"  {col.name} {col.type}{flags_str}{sample}")
    return "\n".join(lines)


def render_schema_text(schema) -> str:
    parts = [render_table(t) for t in schema.tables]
    if schema.relationships:
        rels = "\n".join(
            f"{r.from_table}.{r.from_column} -> {r.to_table}.{r.to_column}"
            for r in schema.relationships
        )
        parts.append("RELATIONSHIPS (child.fk -> parent):\n" + rels)
    return "\n\n".join(parts)
