from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.products.enums import TrendDirection
from app.scraping.enums import RunStatus
from app.scraping.trends import TrendsRateLimitedError
from app.tasks.jobs import _finish_trends_run, _normalize_trend_direction


def test_scoring_input_normalizes_database_trend_direction() -> None:
    assert _normalize_trend_direction("rising") is TrendDirection.RISING
    assert _normalize_trend_direction(None) is TrendDirection.UNKNOWN


async def test_empty_trends_run_is_reported_as_blocked() -> None:
    runs = SimpleNamespace(finish=AsyncMock())
    run = SimpleNamespace()

    await _finish_trends_run(runs, run, collected=0, requested=20)

    runs.finish.assert_awaited_once_with(
        run,
        RunStatus.BLOCKED,
        detail="Google Trends returned no data for 20 keyword(s)",
    )


def test_rate_limit_error_has_actionable_message() -> None:
    error = TrendsRateLimitedError("Google Trends rate limit; retry later")

    assert str(error) == "Google Trends rate limit; retry later"
