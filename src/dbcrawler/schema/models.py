from pydantic import BaseModel, Field


class ForeignKeyRef(BaseModel):
    references_table: str
    references_column: str


class SchemaColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool = False
    foreign_keys: list[ForeignKeyRef] = Field(default_factory=list)
    sample_values: list[str] = Field(default_factory=list)


class SchemaTable(BaseModel):
    name: str
    description: str = ""
    columns: list[SchemaColumn] = Field(default_factory=list)


class Relationship(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str


class SchemaRepresentation(BaseModel):
    tables: list[SchemaTable] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
