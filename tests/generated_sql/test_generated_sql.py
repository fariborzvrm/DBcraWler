from dbcrawler.generated_sql import GeneratedSQL


def test_from_llm_valid():
    model = GeneratedSQL.from_llm(
        {
            "sql": "SELECT 1",
            "explanation": "a",
            "confidence": 0.9,
            "tables": ["t"],
            "columns": ["c"],
        }
    )
    assert model.sql == "SELECT 1"


def test_from_llm_confidence_out_of_range():
    import pytest

    with pytest.raises(ValueError):
        GeneratedSQL.from_llm(
            {"sql": "SELECT 1", "explanation": "a", "confidence": 2.0}
        )


def test_from_llm_missing_fields():
    import pytest

    with pytest.raises(ValueError) as exc:
        GeneratedSQL.from_llm({"sql": "SELECT 1"})
    assert "malformed" in str(exc.value).lower()
