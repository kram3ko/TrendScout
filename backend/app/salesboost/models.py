from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Entity


class PastProduct(Entity):
    """One of our past winners — the source of the Internal Sales Boost."""

    __tablename__ = "past_products"

    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(128), index=True)
    keywords: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str | None] = mapped_column(Text)
