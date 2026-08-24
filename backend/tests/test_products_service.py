from datetime import UTC, datetime
from unittest.mock import AsyncMock

from app.products.service import TREND_REFRESH_AGE, ProductService, deduplicate_by_asin
from app.scraping.amazon import ScrapedProduct


def scraped(asin: str, category: str) -> ScrapedProduct:
    return ScrapedProduct(
        asin=asin,
        title="Bug Zapper",
        category=category,
        price=33.29,
        rating=4.4,
        reviews_count=30_158,
        url=f"https://www.amazon.com/dp/{asin}",
        image_url="https://example.com/image.jpg",
        bestseller_rank=27,
    )


def test_a_product_charting_in_two_categories_is_upserted_once():
    items = [scraped("B09PQF39PG", "home-garden"), scraped("B09PQF39PG", "lawn-garden")]

    deduplicated = deduplicate_by_asin(items)

    assert len(deduplicated) == 1
    assert deduplicated[0].category == "home-garden"


def test_distinct_products_are_kept_in_scrape_order():
    items = [scraped("B000000001", "kitchen"), scraped("B000000002", "kitchen")]

    assert [item.asin for item in deduplicate_by_asin(items)] == ["B000000001", "B000000002"]


async def test_trends_selection_only_includes_missing_or_stale_snapshots() -> None:
    session = type("Session", (), {"scalars": AsyncMock(return_value=[])})()
    before = datetime.now(UTC)

    assert await ProductService(session).select_for_trends(8) == []
    after = datetime.now(UTC)

    statement = session.scalars.await_args.args[0]
    cutoff = next(
        value for value in statement.compile().params.values() if isinstance(value, datetime)
    )
    assert "collected_at IS NULL" in str(statement)
    assert before - TREND_REFRESH_AGE <= cutoff <= after - TREND_REFRESH_AGE
    assert 8 in statement.compile().params.values()
