from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.enums import RunKind, RunStatus
from app.scraping.models import ScrapeRun

# A worker killed mid-run leaves its row in RUNNING forever; past this age the
# panel must let a buyer start a new run rather than stay locked out.
STALE_RUN_AFTER = timedelta(minutes=30)


class RunService:
    """Owns the lifecycle of a scraping run so the dashboard can explain a quiet result."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start(self, kind: RunKind) -> ScrapeRun:
        run = ScrapeRun(kind=kind, status=RunStatus.RUNNING)
        self._session.add(run)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def finish(
        self, run: ScrapeRun, status: RunStatus, items_collected: int = 0, detail: str | None = None
    ) -> ScrapeRun:
        run.status = status
        run.items_collected = items_collected
        run.detail = detail
        run.finished_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def recent(self, limit: int) -> list[ScrapeRun]:
        statement = select(ScrapeRun).order_by(ScrapeRun.created_at.desc()).limit(limit)
        return list(await self._session.scalars(statement))

    async def active(self) -> ScrapeRun | None:
        """Guards the panel button: a second browser run would only fight for RAM."""
        statement = (
            select(ScrapeRun)
            .where(
                ScrapeRun.status == RunStatus.RUNNING,
                ScrapeRun.created_at > datetime.now(UTC) - STALE_RUN_AFTER,
            )
            .order_by(ScrapeRun.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def close_abandoned(self) -> int:
        """DML always yields a CursorResult; the generic Result type hides `rowcount`."""
        statement = (
            update(ScrapeRun)
            .where(ScrapeRun.status == RunStatus.RUNNING)
            .values(
                status=RunStatus.FAILED,
                detail="Worker restarted before the run completed",
                finished_at=datetime.now(UTC),
            )
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        await self._session.commit()
        return result.rowcount
