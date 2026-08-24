from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.products.enums import ProductSort, TrendDirection
from app.products.models import Product

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class TrendRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    keyword: str
    direction: TrendDirection
    latest_value: int | None
    points_count: int
    collected_at: datetime = Field(validation_alias="created_at")


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: int
    reasoning: str
    boost_score: float
    source: str
    scored_at: datetime = Field(validation_alias="updated_at")


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asin: str
    title: str
    category: str
    price: float | None
    rating: float | None
    reviews_count: int | None
    url: str
    image_url: str
    bestseller_rank: int | None
    updated_at: datetime
    score: ScoreRead | None
    trend: TrendRead | None

    @classmethod
    def from_product(cls, product: Product) -> ProductRead:
        """`trends` is ordered newest-first, so the head is the current reading."""
        latest = product.trends[0] if product.trends else None
        return cls(
            id=product.id,
            asin=product.asin,
            title=product.title,
            category=product.category,
            price=product.price,
            rating=product.rating,
            reviews_count=product.reviews_count,
            url=product.url,
            image_url=product.image_url,
            bestseller_rank=product.bestseller_rank,
            updated_at=product.updated_at,
            score=ScoreRead.model_validate(product.score) if product.score else None,
            trend=TrendRead.model_validate(latest) if latest else None,
        )


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
    limit: int
    offset: int


class ProductQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    min_score: int | None = Field(default=None, ge=0, le=100)
    search: str | None = Field(default=None, max_length=128)
    sort: ProductSort = ProductSort.SCORE
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    offset: int = Field(default=0, ge=0)
