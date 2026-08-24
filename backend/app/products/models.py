from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Entity
from app.products.enums import TrendDirection


class Product(Entity):
    """A product from Amazon Best Sellers. ASIN is the natural key for deduplication."""

    __tablename__ = "products"

    asin: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(128), index=True)
    price: Mapped[float | None] = mapped_column(Float)
    rating: Mapped[float | None] = mapped_column(Float)
    reviews_count: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text)
    bestseller_rank: Mapped[int | None] = mapped_column(Integer)

    trends: Mapped[list[TrendSnapshot]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(TrendSnapshot.created_at)",
    )
    score: Mapped[ProductScore | None] = relationship(
        back_populates="product", cascade="all, delete-orphan", uselist=False
    )


class TrendSnapshot(Entity):
    """One Google Trends reading for a product keyword; `created_at` is the reading time."""

    __tablename__ = "trend_snapshots"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    keyword: Mapped[str] = mapped_column(String(255))
    direction: Mapped[TrendDirection] = mapped_column(String(16))
    latest_value: Mapped[int | None] = mapped_column(Integer)
    avg_first_half: Mapped[float | None] = mapped_column(Float)
    avg_second_half: Mapped[float | None] = mapped_column(Float)
    points_count: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Product] = relationship(back_populates="trends")


class ProductScore(Entity):
    """Final verdict for a product; `updated_at` is when it was last scored."""

    __tablename__ = "product_scores"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True
    )
    score: Mapped[int] = mapped_column(Integer, index=True)
    reasoning: Mapped[str] = mapped_column(Text)
    boost_score: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(32))

    product: Mapped[Product] = relationship(back_populates="score")
