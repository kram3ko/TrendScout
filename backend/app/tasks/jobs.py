import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqEvents, TaskiqState

from app.core.config import Settings, get_settings
from app.core.db import SessionFactory
from app.products.enums import TrendDirection
from app.products.keywords import trends_keyword
from app.products.models import Product
from app.products.service import ProductService
from app.salesboost.service import SalesBoostService
from app.scoring.boost import BoostCalculator
from app.scoring.engine import ScoringEngine
from app.scoring.fallback import DeterministicScorer
from app.scoring.llm.factory import build_scorer
from app.scoring.schemas import ScoringInput
from app.scraping.amazon import BlockedError, ScrapedProduct, scrape_category
from app.scraping.amazon import discover_categories as scrape_categories
from app.scraping.browser import browser_context
from app.scraping.category_service import AmazonCategoryService
from app.scraping.enums import RunKind, RunStatus
from app.scraping.models import AmazonCategory, ScrapeRun
from app.scraping.service import RunService
from app.scraping.trends import TrendsRateLimitedError, TrendsScraper
from app.tasks.broker import SCRAPE_CRON, broker

logger = logging.getLogger(__name__)

SCRAPE_SCHEDULE = [{"cron": SCRAPE_CRON}]


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def close_abandoned_runs(_: TaskiqState) -> None:
    async with SessionFactory() as session:
        closed = await RunService(session).close_abandoned()
    if closed:
        logger.warning("Closed %d abandoned browser run(s)", closed)


@broker.task(task_name="scrape_amazon", schedule=SCRAPE_SCHEDULE)
async def scrape_amazon() -> None:
    """Refresh the catalogue from Amazon Best Sellers, then rescore what changed."""
    settings = get_settings()
    async with SessionFactory() as session:
        runs = RunService(session)
        run = await runs.start(RunKind.AMAZON)
        categories = await AmazonCategoryService(session).enabled()
        if not categories:
            await runs.finish(
                run,
                RunStatus.BLOCKED,
                detail="Select at least one Amazon category in the dashboard",
            )
            return
        try:
            collected = await _scrape_all_categories(settings, categories)
            stored = await ProductService(session).upsert_scraped(collected)
        except BlockedError as error:
            await runs.finish(run, RunStatus.BLOCKED, detail=str(error))
            return
        except Exception as error:
            logger.exception("Amazon scrape failed")
            await runs.finish(run, RunStatus.FAILED, detail=_short(error))
            return

        await runs.finish(run, RunStatus.SUCCESS, items_collected=stored)

    await score_products.kiq()


@broker.task(task_name="discover_amazon_categories")
async def discover_amazon_categories() -> None:
    async with SessionFactory() as session:
        runs = RunService(session)
        run = await runs.start(RunKind.CATEGORIES)
        try:
            async with browser_context() as context:
                discovered = await scrape_categories(context)
            if not discovered:
                await runs.finish(
                    run, RunStatus.BLOCKED, detail="Amazon returned no category links"
                )
                return
            stored = await AmazonCategoryService(session).replace_discovered(discovered)
        except BlockedError as error:
            await runs.finish(run, RunStatus.BLOCKED, detail=str(error))
            return
        except Exception as error:
            logger.exception("Amazon category discovery failed")
            await runs.finish(run, RunStatus.FAILED, detail=_short(error))
            return
        await runs.finish(run, RunStatus.SUCCESS, items_collected=stored)


@broker.task(task_name="collect_trends")
async def collect_trends() -> None:
    """Read Google Trends for the products the panel is most likely to show."""
    settings = get_settings()
    async with SessionFactory() as session:
        products = await ProductService(session).select_for_trends(
            settings.trends_max_products_per_run
        )
        runs = RunService(session)
        run = await runs.start(RunKind.TRENDS)
        if not products:
            await runs.finish(run, RunStatus.SUCCESS, detail="no products to check yet")
            return

        try:
            collected = await _collect_trends_for(session, products, settings)
        except TrendsRateLimitedError as error:
            await runs.finish(run, RunStatus.BLOCKED, detail=str(error))
            return
        except Exception as error:
            logger.exception("Trends collection failed")
            await runs.finish(run, RunStatus.FAILED, detail=_short(error))
            return

        await _finish_trends_run(runs, run, collected, len(products))

    await score_products.kiq()


@broker.task(task_name="score_products")
async def score_products(rescore_all: bool = False) -> None:
    """Score everything whose facts moved since the last verdict."""
    settings = get_settings()
    async with SessionFactory() as session:
        products = await ProductService(session).load_for_scoring(only_stale=not rescore_all)
        if not products:
            return

        calculator = BoostCalculator(await SalesBoostService(session).list_all())
        inputs = [_to_scoring_input(product, calculator) for product in products]

        engine = ScoringEngine(
            fallback=DeterministicScorer(),
            scorer=build_scorer(settings),
            provider=settings.llm_provider.value,
            batch_size=settings.llm_batch_size,
        )
        results = await engine.score(inputs)

        by_asin = {product.asin: product.id for product in products}
        boost_by_asin = {item.asin: item.boost.points for item in inputs}
        await ProductService(session).save_scores(
            [(by_asin[result.asin], result, boost_by_asin[result.asin]) for result in results]
        )


async def _scrape_all_categories(
    settings: Settings, categories: Sequence[AmazonCategory]
) -> list[ScrapedProduct]:
    async with browser_context() as context:
        collected: list[ScrapedProduct] = []
        for category in categories:
            collected.extend(
                await scrape_category(
                    context,
                    category.slug,
                    settings.amazon_max_items_per_category,
                    category.name,
                )
            )
        return collected


async def _collect_trends_for(
    session: AsyncSession, products: Sequence[Product], settings: Settings
) -> int:
    keyword_by_product = {product.id: trends_keyword(product.title) for product in products}
    async with browser_context() as context:
        scraper = TrendsScraper(context, settings.trends_geo)
        results = await scraper.collect(sorted(set(keyword_by_product.values())))

    service = ProductService(session)
    stored = 0
    for product_id, keyword in keyword_by_product.items():
        result = results.get(keyword)
        if result is None:
            continue
        await service.record_trend(product_id, result)
        stored += 1
    return stored


async def _finish_trends_run(
    runs: RunService, run: ScrapeRun, collected: int, requested: int
) -> None:
    if collected:
        await runs.finish(run, RunStatus.SUCCESS, items_collected=collected)
        return
    await runs.finish(
        run,
        RunStatus.BLOCKED,
        detail=f"Google Trends returned no data for {requested} keyword(s)",
    )


def _to_scoring_input(product: Product, calculator: BoostCalculator) -> ScoringInput:
    latest_trend = product.trends[0] if product.trends else None
    return ScoringInput(
        asin=product.asin,
        title=product.title,
        category=product.category,
        price=product.price,
        rating=product.rating,
        reviews_count=product.reviews_count,
        bestseller_rank=product.bestseller_rank,
        trend_direction=_normalize_trend_direction(
            latest_trend.direction if latest_trend else None
        ),
        trend_latest_value=latest_trend.latest_value if latest_trend else None,
        boost=calculator.evaluate(product.title, product.category),
    )


def _normalize_trend_direction(direction: TrendDirection | str | None) -> TrendDirection:
    return TrendDirection(direction) if direction is not None else TrendDirection.UNKNOWN


def _short(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"[:500]
