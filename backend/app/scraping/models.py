from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Entity
from app.scraping.enums import RunKind, RunStatus


class AmazonCategory(Entity):
    __tablename__ = "amazon_categories"

    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)


class ScrapeRun(Entity):
    """Journal of every scraping run — tells "found nothing" apart from "got blocked".

    `created_at` is the start of the run; `finished_at` stays null while it runs.
    """

    __tablename__ = "scrape_runs"

    kind: Mapped[RunKind] = mapped_column(String(16), index=True)
    status: Mapped[RunStatus] = mapped_column(String(16), index=True)
    items_collected: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
