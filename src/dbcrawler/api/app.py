"""FastAPI query interface (Phase 4, plan.md Day 9-11).

Endpoints:
    POST /v1/query    natural-language question -> SQL + results + confidence
    GET  /v1/schema   database schema representation
    GET  /v1/history  session query history (newest first)
    POST /v1/feedback/{query_id}  mark a result correct/incorrect

Guardrails always run before any execution; the DB user is read-only.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from dbcrawler.api.history import (
    HistoryEntry,
    InMemoryHistory,
    build_history_entry,
)
from dbcrawler.api.service import (
    check_question_ambiguity,
    execute_generated_sql,
    generate_sql,
)
from dbcrawler.config.settings import get_settings
from dbcrawler.llm.client import OpenRouterClient
from dbcrawler.schema.extractor import extract_schema_url

logger = logging.getLogger("dbcrawler.api")


class AppContext:
    def __init__(self, settings, client, schema, history):
        self.settings = settings
        self.client = client
        self.schema = schema
        self.history = history


def build_context() -> AppContext:
    settings = get_settings()
    client = OpenRouterClient(settings)
    schema = extract_schema_url(settings.db_url, settings)
    return AppContext(settings, client, schema, InMemoryHistory())


@asynccontextmanager
async def lifespan(app: FastAPI):
    if getattr(app.state, "ctx", None) is None:
        logger.info("Loading settings, OpenRouter client and database schema")
        app.state.ctx = build_context()
    yield


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    id: str
    status: str
    question: str
    sql: str | None = None
    explanation: str | None = None
    results: list[dict] | None = None
    row_count: int | None = None
    truncated: bool | None = None
    execution_time_ms: float | None = None
    confidence: dict[str, Any] | None = None
    sanity: list[dict] | None = None
    intent: dict[str, Any] | None = None
    multiquery: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    ambiguity: list[dict] | None = None


class FeedbackRequest(BaseModel):
    correct: bool
    comment: str = ""


def create_app(ctx: AppContext | None = None) -> FastAPI:
    app = FastAPI(
        title="DBcraWler",
        version="0.1.0",
        description="Text-to-SQL with guardrails, validation and confidence. "
        "Generated SQL is never executed before passing guardrails.",
        lifespan=lifespan,
    )
    if ctx is not None:
        app.state.ctx = ctx

    @app.post("/v1/query", response_model=QueryResponse)
    def post_query(payload: QueryRequest) -> QueryResponse:
        question = payload.question.strip()
        ctx = app.state.ctx
        entry_id = ctx.history.new_id()
        timestamp = ctx.history.now()

        ambiguity = check_question_ambiguity(ctx.client, ctx.settings, ctx.schema, question)
        if ambiguity.is_ambiguous:
            entry = build_history_entry(
                entry_id,
                timestamp,
                question,
                "clarification_needed",
                generated=None,
                results={},
                confidence=None,
                warnings=[],
            )
            ctx.history.record(entry)
            return QueryResponse(
                id=entry.id,
                status=entry.status,
                question=question,
                ambiguity=list(ambiguity.interpretations),
            )

        try:
            generated = generate_sql(ctx.client, ctx.settings, ctx.schema, question)
        except Exception as exc:  # noqa: BLE001 - LLM failure must not 500
            logger.warning("SQL generation failed: %s", exc)
            entry = HistoryEntry(
                id=entry_id,
                timestamp=timestamp,
                question=question,
                status="generation_failed",
                warnings=[f"sql generation unavailable: {exc}"],
            )
            ctx.history.record(entry)
            return QueryResponse(
                id=entry.id,
                status=entry.status,
                question=question,
                warnings=entry.warnings,
            )
        outcome = execute_generated_sql(
            ctx.client, ctx.settings, ctx.schema, question, generated
        )
        entry = build_history_entry(
            entry_id,
            timestamp,
            question,
            outcome["status"],
            generated=generated,
            results=outcome,
            confidence=outcome["confidence"],
            warnings=outcome["warnings"],
        )
        ctx.history.record(entry)
        return QueryResponse(
            id=entry.id,
            status=entry.status,
            question=question,
            sql=generated.sql,
            explanation=generated.explanation,
            results=entry.results,
            row_count=entry.row_count,
            truncated=entry.truncated,
            execution_time_ms=entry.execution_time_ms,
            confidence=(
                outcome["confidence"].model_dump()
                if outcome["confidence"] is not None
                else None
            ),
            sanity=(
                [f.model_dump() for f in outcome["sanity"].findings]
                if outcome["sanity"] is not None
                else None
            ),
            intent=(
                outcome["intent"].model_dump() if outcome["intent"] is not None else None
            ),
            multiquery=(
                outcome["multiquery"].model_dump()
                if outcome["multiquery"] is not None
                else None
            ),
            warnings=outcome["warnings"],
        )

    @app.get("/v1/schema")
    def get_schema() -> dict[str, Any]:
        return app.state.ctx.schema.model_dump()

    @app.get("/v1/history")
    def get_history(limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, app.state.ctx.history.max_entries))
        return [entry.model_dump() for entry in app.state.ctx.history.list(limit)]

    @app.post("/v1/feedback/{entry_id}")
    def post_feedback(entry_id: str, payload: FeedbackRequest) -> dict[str, Any]:
        ctx = app.state.ctx
        entry = ctx.history.set_feedback(entry_id, payload.correct, payload.comment)
        if entry is None:
            raise HTTPException(status_code=404, detail="history entry not found")
        return {"id": entry.id, "feedback": entry.feedback.model_dump()}

    return app
