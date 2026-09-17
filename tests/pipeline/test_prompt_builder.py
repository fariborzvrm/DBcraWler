from dbcrawler.pipeline.prompt_builder import build_prompt, load_few_shot


def test_load_few_shot_from_data():
    examples = load_few_shot()
    assert len(examples) >= 3
    assert "sql" in examples[0] and "question" in examples[0]


def test_prompt_contains_schema_and_question_and_examples():
    schema_text = "TABLE customers\n  customer_id TEXT [PK]"
    prompt = build_prompt(schema_text, "How many customers?")
    assert "How many customers?" in prompt
    assert "customers" in prompt
    assert "glossary" in prompt
    assert "Example SQL:" in prompt
