from collections.abc import Sequence
from dataclasses import asdict

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.products.enums import ProductSort
from app.products.models import Product, ProductScore, TrendSnapshot
from app.products.schemas import ProductPage, ProductQuery, ProductRead
from app.scoring.schemas import ScoreResult
from app.scraping.amazon import ScrapedProduct
from app.scraping.trends import TrendResult

# Columns a re-scrape is allowed to overwrite; identity columns stay put.
REFRESHED_COLUMNS = (
    "title",
    "category",
    "price",
    "rating",
    "reviews_count",
    "url",
    "image_url",
    "bestseller_rank",
)


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_scraped(self, items: Sequence[ScrapedProduct]) -> int:
        """ASIN is the natural key, so a re-run refreshes rows instead of duplicating them."""
        deduplicated = deduplicate_by_asin(items)
        if not deduplicated:
            return 0

        statement = insert(Product).values([asdict(item) for item in deduplicated])
        statement = statement.on_conflict_do_update(
            index_elements=[Product.asin],
            set_={column: statement.excluded[column] for column in REFRESHED_COLUMNS}
            | {"updated_at": func.now()},
        )
        await self._session.execute(statement)
        await self._session.commit()
        return len(deduplicated)

    async def list_page(self, query: ProductQuery) -> ProductPage:
        total = await self._session.scalar(
            select(func.count()).select_from(_filtered(select(Product.id), query).subquery())
        )

        statement = (
            _filtered(select(Product), query)
            .options(selectinload(Product.trends), selectinload(Product.score))
            .order_by(*_ordering(query.sort))
            .limit(query.limit)
            .offset(query.offset)
        )
        products = (await self._session.scalars(statement)).unique().all()
        return ProductPage(
            items=[ProductRead.from_product(product) for product in products],
            total=total or 0,
            limit=query.limit,
            offset=query.offset,
        )

    async def categories(self) -> list[str]:
        statement = select(Product.category).distinct().order_by(Product.category)
        return list(await self._session.scalars(statement))

    async def select_for_trends(self, limit: int) -> list[Product]:
        """Highest-ranked products with the oldest trend reading — the queue never starves."""
        latest = (
            select(
                TrendSnapshot.product_id.label("product_id"),
                func.max(TrendSnapshot.created_at).label("collected_at"),
            )
            .group_by(TrendSnapshot.product_id)
            .subquery()
        )
        statement = (
            select(Product)
            .outerjoin(latest, latest.c.product_id == Product.id)
            .order_by(latest.c.collected_at.asc().nulls_first(), Product.bestseller_rank.asc())
            .limit(limit)
        )
        return list(await self._session.scalars(statement))

    async def record_trend(self, product_id: int, result: TrendResult) -> None:
        self._session.add(
            TrendSnapshot(
                product_id=product_id,
                keyword=result.keyword,
                direction=result.direction,
                latest_value=result.latest_value,
                avg_first_half=result.avg_first_half,
                avg_second_half=result.avg_second_half,
                points_count=result.points_count,
            )
        )
        await self._session.commit()

    async def load_for_scoring(self, only_stale: bool = True) -> list[Product]:
        """Stale-only by default: LLM free-tier quota is the binding constraint here."""
        statement = select(Product).options(
            selectinload(Product.trends), selectinload(Product.score)
        )
        products = list((await self._session.scalars(statement)).unique())
        return [p for p in products if _needs_rescore(p)] if only_stale else products

    async def save_scores(self, results: Sequence[tuple[int, ScoreResult, float]]) -> None:
        if not results:
            return

        statement = insert(ProductScore).values(
            [
                {
                    "product_id": product_id,
                    "score": result.score,
                    "reasoning": result.reasoning,
                    "boost_score": boost_points,
                    "source": result.source,
                }
                for product_id, result, boost_points in results
            ]
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ProductScore.product_id],
            set_={
                "score": statement.excluded.score,
                "reasoning": statement.excluded.reasoning,
                "boost_score": statement.excluded.boost_score,
                "source": statement.excluded.source,
                "updated_at": func.now(),
            },
        )
        await self._session.execute(statement)
        await self._session.commit()


def _filtered(statement: Select, query: ProductQuery) -> Select:
    """Score lives in a one-to-one table, so filtering and sorting both need it joined."""
    statement = statement.outerjoin(ProductScore, ProductScore.product_id == Product.id)
    if query.category:
        statement = statement.where(Product.category == query.category)
    if query.search:
        statement = statement.where(Product.title.ilike(f"%{query.search}%"))
    if query.min_score is not None:
        statement = statement.where(ProductScore.score >= query.min_score)
    return statement


def deduplicate_by_asin(items: Sequence[ScrapedProduct]) -> list[ScrapedProduct]:
    """A product can chart in two categories at once, and Postgres refuses to let one
    ON CONFLICT statement touch the same row twice. First occurrence wins: categories
    are scraped in configured order, so the earlier one is the more relevant listing.
    """
    by_asin: dict[str, ScrapedProduct] = {}
    for item in items:
        by_asin.setdefault(item.asin, item)
    return list(by_asin.values())


def _needs_rescore(product: Product) -> bool:
    """A stored verdict stays valid until the facts behind it move."""
    if product.score is None:
        return True
    if product.score.updated_at < product.updated_at:
        return True
    latest_trend = product.trends[0] if product.trends else None
    return latest_trend is not None and product.score.updated_at < latest_trend.created_at


def _ordering(sort: ProductSort) -> tuple:
    match sort:
        case ProductSort.SCORE:
            # Unscored products must not outrank scored ones on the default view.
            return (ProductScore.score.desc().nulls_last(), Product.bestseller_rank.asc())
        case ProductSort.RANK:
            return (Product.bestseller_rank.asc().nulls_last(),)
        case ProductSort.RECENT:
            return (Product.updated_at.desc(),)
