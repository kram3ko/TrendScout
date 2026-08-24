from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.amazon import DiscoveredCategory
from app.scraping.models import AmazonCategory


class UnknownCategoryError(ValueError):
    pass


class AmazonCategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_available(self) -> list[AmazonCategory]:
        statement = (
            select(AmazonCategory)
            .where(AmazonCategory.available.is_(True))
            .order_by(AmazonCategory.name)
        )
        return list(await self._session.scalars(statement))

    async def enabled(self) -> list[AmazonCategory]:
        statement = select(AmazonCategory).where(
            AmazonCategory.available.is_(True), AmazonCategory.enabled.is_(True)
        )
        return list(await self._session.scalars(statement))

    async def replace_discovered(self, items: Sequence[DiscoveredCategory]) -> int:
        existing = {
            category.slug: category
            for category in await self._session.scalars(select(AmazonCategory))
        }
        discovered_slugs = {item.slug for item in items}

        for category in existing.values():
            category.available = category.slug in discovered_slugs
            if not category.available:
                category.enabled = False

        for item in items:
            category = existing.get(item.slug)
            if category is None:
                self._session.add(AmazonCategory(slug=item.slug, name=item.name))
            else:
                category.name = item.name
                category.available = True

        await self._session.commit()
        return len(items)

    async def set_enabled(self, slugs: Sequence[str]) -> list[AmazonCategory]:
        requested = set(slugs)
        available = {category.slug for category in await self.list_available()}
        unknown = requested - available
        if unknown:
            raise UnknownCategoryError(", ".join(sorted(unknown)))

        await self._session.execute(update(AmazonCategory).values(enabled=False))
        if requested:
            await self._session.execute(
                update(AmazonCategory)
                .where(AmazonCategory.slug.in_(requested))
                .values(enabled=True)
            )
        await self._session.commit()
        return await self.list_available()
