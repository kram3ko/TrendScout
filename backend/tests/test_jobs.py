from app.products.enums import TrendDirection
from app.tasks.jobs import _normalize_trend_direction


def test_scoring_input_normalizes_database_trend_direction() -> None:
    assert _normalize_trend_direction("rising") is TrendDirection.RISING
    assert _normalize_trend_direction(None) is TrendDirection.UNKNOWN
