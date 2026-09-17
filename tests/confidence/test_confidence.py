from dbcrawler.confidence import compute_confidence, schema_coverage
from dbcrawler.generated_sql import GeneratedSQL
from dbcrawler.validation.sanity import SanityResult


def gen(confidence=0.9, tables=("customers",)):
    return GeneratedSQL(
        sql="SELECT 1",
        explanation="x",
        confidence=confidence,
        tables=list(tables),
        columns=["id"],
    )


def test_full_signals_high_confidence():
    result = compute_confidence(
        gen(),
        SanityResult(),
        intent_alignment=1.0,
        coverage=1.0,
        multiquery_agreement=True,
    )
    assert result.final > 0.9
    assert result.multiquery_agreement is True


def test_disagreeing_multiquery_lowers_confidence():
    agree = compute_confidence(
        gen(),
        SanityResult(),
        intent_alignment=1.0,
        coverage=1.0,
        multiquery_agreement=True,
    )
    disagree = compute_confidence(
        gen(),
        SanityResult(),
        intent_alignment=1.0,
        coverage=1.0,
        multiquery_agreement=False,
    )
    assert disagree.final < agree.final


def test_low_alignment_lowers_confidence():
    high = compute_confidence(gen(), SanityResult(), intent_alignment=1.0, coverage=1.0)
    low = compute_confidence(gen(), SanityResult(), intent_alignment=0.1, coverage=1.0)
    assert low.final < high.final


def test_coverage_without_multiquery_renormalizes():
    result = compute_confidence(
        gen(), SanityResult(), intent_alignment=0.9, coverage=1.0
    )
    assert 0.0 <= result.final <= 1.0


def test_coverage_hallucinated_table_fails():
    assert schema_coverage(["ghost_table"], {"ghost_table"}, {"customers"}) == 0.0
    assert schema_coverage(["customers"], {"customers"}, {"customers"}) == 1.0
    assert schema_coverage(["customers"], set(), {"customers", "orders"}) == 0.0
