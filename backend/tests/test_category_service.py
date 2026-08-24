from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.scraping.amazon import DiscoveredCategory
from app.scraping.category_service import AmazonCategoryService, UnknownCategoryError


class FakeSession:
    def __init__(self, scalar_results=None) -> None:
        self.scalar_results = list(scalar_results or [])
        self.added = []
        self.execute = AsyncMock()
        self.commit = AsyncMock()

    async def scalars(self, statement):
        return self.scalar_results.pop(0)

    def add(self, value) -> None:
        self.added.append(value)


def category(slug: str, name: str, enabled: bool = False):
    return SimpleNamespace(slug=slug, name=name, enabled=enabled, available=True)


async def test_discovery_updates_existing_and_disables_missing_categories() -> None:
    kept = category("home-garden", "Old name", enabled=True)
    missing = category("missing", "Missing", enabled=True)
    session = FakeSession([[kept, missing]])
    service = AmazonCategoryService(session)

    count = await service.replace_discovered(
        [
            DiscoveredCategory(slug="home-garden", name="Home & Kitchen"),
            DiscoveredCategory(slug="beauty", name="Beauty"),
        ]
    )

    assert count == 2
    assert kept.name == "Home & Kitchen"
    assert missing.available is False
    assert missing.enabled is False
    assert session.added[0].slug == "beauty"
    session.commit.assert_awaited_once()


async def test_selection_rejects_unknown_category_without_writes() -> None:
    session = FakeSession([[category("beauty", "Beauty")]])
    service = AmazonCategoryService(session)

    with pytest.raises(UnknownCategoryError, match="missing"):
        await service.set_enabled(["missing"])

    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_selection_replaces_enabled_categories() -> None:
    available = [category("beauty", "Beauty"), category("home-garden", "Home & Kitchen")]
    session = FakeSession([available, available])
    service = AmazonCategoryService(session)

    result = await service.set_enabled(["beauty"])

    assert result == available
    assert session.execute.await_count == 2
    session.commit.assert_awaited_once()


async def test_enabled_returns_available_selected_rows() -> None:
    selected = [category("beauty", "Beauty", enabled=True)]
    service = AmazonCategoryService(FakeSession([selected]))

    assert await service.enabled() == selected
