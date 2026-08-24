from unittest.mock import AsyncMock

from app.products.enums import TrendDirection
from app.scraping import trends
from app.scraping.trends import TrendResult, TrendsScraper


async def test_batch_waits_between_keywords_but_not_before_first(monkeypatch) -> None:
    page = type(
        "Page",
        (),
        {
            "goto": AsyncMock(),
            "wait_for_timeout": AsyncMock(),
            "close": AsyncMock(),
        },
    )()
    context = type("Context", (), {"new_page": AsyncMock(return_value=page)})()
    scraper = TrendsScraper(context, "US")
    result = TrendResult("item", TrendDirection.FLAT, 50, 50.0, 50.0, 52)
    scraper._collect_one = AsyncMock(return_value=result)
    monkeypatch.setattr(trends.random, "randint", lambda _minimum, _maximum: 4_250)

    collected = await scraper.collect(["first", "second", "third"])

    assert list(collected) == ["first", "second", "third"]
    assert [call.args[0] for call in page.wait_for_timeout.await_args_list] == [
        trends.WARMUP_SETTLE_MS,
        4_250,
        4_250,
    ]
