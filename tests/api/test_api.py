from fastapi.testclient import TestClient

from dbcrawler.api.app import AppContext, create_app
from dbcrawler.api.history import InMemoryHistory
from dbcrawler.confidence import ConfidenceBreakdown
from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.guardrails.executor import QueryResult
from dbcrawler.schema.models import SchemaRepresentation
from dbcrawler.validation.sanity import SanityFinding, SanityResult


class FakeClient:
    pass


def make_schema() -> SchemaRepresentation:
    return SchemaRepresentation(tables=[])


def fake_ctx(schema=None) -> AppContext:
    return AppContext(
        settings=settings_stub,
        client=FakeClient(),
        schema=schema if schema is not None else make_schema(),
        history=InMemoryHistory(),
    )


class FakeSettings:
    db_url = "postgresql+psycopg://app_readonly:x@localhost:5433/x"


settings_stub = FakeSettings()


def generated() -> GeneratedSQL:
    return GeneratedSQL(
        sql="SELECT count(*) AS customers FROM customers",
        explanation="counts customers",
        confidence=0.9,
        tables=["customers"],
        columns=["customer_id"],
    )


def outcome_ok():
    return {
        "status": "ok",
        "query_result": QueryResult(
            sql="SELECT count(*) AS customers FROM customers LIMIT 1000",
            rows=[{"customers": 6}],
            row_count=1,
            truncated=False,
            execution_time_ms=1.5,
            explain_plan="Seq Scan",
        ),
        "sanity": SanityResult(
            findings=[SanityFinding(check="has_rows", passed=True, message="ok")]
        ),
        "intent": None,
        "multiquery": None,
        "confidence": ConfidenceBreakdown(
            final=0.8,
            llm_self_report=0.9,
            intent_alignment=0.75,
            sanity_pass_rate=1.0,
            schema_coverage=1.0,
        ),
        "warnings": [],
    }


def patch_service(monkeypatch, **kwargs):
    import dbcrawler.api.app as app_module

    ambiguity = kwargs.get("ambiguity", False)
    outcome = kwargs.get("outcome", outcome_ok())
    gen = kwargs.get("generated", generated())

    monkeypatch.setattr(
        app_module,
        "check_question_ambiguity",
        lambda *a, **k: _FakeAmbiguity(ambiguity),
    )
    monkeypatch.setattr(app_module, "generate_sql", lambda *a, **k: gen)
    monkeypatch.setattr(
        app_module, "execute_generated_sql", lambda *a, **k: outcome.copy()
    )


class _FakeAmbiguity:
    def __init__(self, is_ambiguous: bool):
        self.is_ambiguous = is_ambiguous
        self.interpretations = [
            {"description": "net revenue", "example_sql": "SELECT 1"}
        ]


def test_query_ok(monkeypatch):
    patch_service(monkeypatch)
    app = create_app(fake_ctx())
    with TestClient(app) as client:
        response = client.post(
            "/v1/query", json={"question": "How many customers in Germany?"}
        )
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["sql"].startswith("SELECT count")
    assert body["confidence"]["final"] == 0.8
    assert body["results"] == [{"customers": 6}]
    assert body["row_count"] == 1


def test_query_ambiguous(monkeypatch):
    patch_service(monkeypatch, ambiguity=True)
    schema = SchemaRepresentation(
        tables=[], relationships=[]
    )
    ctx = fake_ctx(schema)
    app = create_app(ctx)
    with TestClient(app) as client:
        response = client.post("/v1/query", json={"question": "What is revenue?"})
    body = response.json()
    assert body["status"] == "clarification_needed"
    assert body["ambiguity"][0]["example_sql"] == "SELECT 1"
    assert body["sql"] is None
    assert len(ctx.history.list()) == 1


def test_query_blocked(monkeypatch):
    outcome = outcome_ok()
    outcome["status"] = "blocked"
    outcome["query_result"] = None
    outcome["warnings"] = ["DML blocked"]
    patch_service(monkeypatch, outcome=outcome)
    ctx = fake_ctx()
    app = create_app(ctx)
    with TestClient(app) as client:
        response = client.post("/v1/query", json={"question": "delete everything"})
    body = response.json()
    assert body["status"] == "blocked"
    assert body["warnings"] == ["DML blocked"]
    assert body["results"] is None


def test_schema_endpoint():
    schema = SchemaRepresentation(
        tables=[], relationships=[]
    )
    app = create_app(fake_ctx(schema))
    with TestClient(app) as client:
        response = client.get("/v1/schema")
    assert response.status_code == 200
    assert response.json() == {"tables": [], "relationships": []}


def test_history_and_feedback(monkeypatch):
    patch_service(monkeypatch)
    ctx = fake_ctx()
    app = create_app(ctx)
    with TestClient(app) as client:
        first = client.post(
            "/v1/query", json={"question": "How many customers in Germany?"}
        ).json()
        second = client.post("/v1/query", json={"question": "How many orders?"}).json()

        history = client.get("/v1/history").json()
        assert [entry["id"] for entry in history] == [second["id"], first["id"]]
        assert history[0]["question"] == "How many orders?"

        missing = client.post(
            f"/v1/feedback/{first['id']}1", json={"correct": True}
        )
        assert missing.status_code == 404

        feedback = client.post(
            f"/v1/feedback/{first['id']}", json={"correct": False, "comment": "bad"}
        ).json()
        assert feedback["feedback"] == {"correct": False, "comment": "bad"}

        stated = client.get("/v1/history").json()
        by_id = {entry["id"]: entry for entry in stated}
        assert by_id[first["id"]]["feedback"]["correct"] is False
        assert by_id[second["id"]]["feedback"] is None


def test_query_generation_failed(monkeypatch):
    import dbcrawler.api.app as app_module

    monkeypatch.setattr(
        app_module,
        "check_question_ambiguity",
        lambda *a, **k: _FakeAmbiguity(False),
    )
    monkeypatch.setattr(
        app_module,
        "generate_sql",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("model returned non-JSON")),
    )

    def boom(*a, **k):
        raise AssertionError("must not execute when generation failed")

    monkeypatch.setattr(app_module, "execute_generated_sql", boom)
    ctx = fake_ctx()
    app = create_app(ctx)
    with TestClient(app) as client:
        response = client.post("/v1/query", json={"question": "anything at all"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "generation_failed"
    assert "model returned non-JSON" in body["warnings"][0]
    assert body["results"] is None
    assert len(ctx.history.list()) == 1


def test_query_validates_input():
    app = create_app(fake_ctx())
    with TestClient(app) as client:
        assert client.post("/v1/query", json={"question": "hi"}).status_code == 422
