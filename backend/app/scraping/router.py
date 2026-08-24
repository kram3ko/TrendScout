from fastapi import APIRouter, HTTPException, status

from app.auth.deps import CurrentUser
from app.scraping.deps import RunServiceDep
from app.scraping.enums import RunKind
from app.scraping.schemas import RECENT_RUNS_LIMIT, RunRead, RunTriggered
from app.tasks.jobs import collect_trends, discover_amazon_categories, scrape_amazon

router = APIRouter(prefix="/runs", tags=["runs"])

_JOB_BY_KIND = {
    RunKind.AMAZON: scrape_amazon,
    RunKind.CATEGORIES: discover_amazon_categories,
    RunKind.TRENDS: collect_trends,
}
_RUN_LABEL = {
    RunKind.AMAZON: "Amazon product collection",
    RunKind.CATEGORIES: "Amazon category discovery",
    RunKind.TRENDS: "Google Trends collection",
}


@router.get("", response_model=list[RunRead])
async def list_runs(user: CurrentUser, runs: RunServiceDep) -> list[RunRead]:
    recent = await runs.recent(RECENT_RUNS_LIMIT)
    return [RunRead.model_validate(run) for run in recent]


@router.post("/{kind}", status_code=status.HTTP_202_ACCEPTED, response_model=RunTriggered)
async def trigger_run(kind: RunKind, user: CurrentUser, runs: RunServiceDep) -> RunTriggered:
    """Queues the job and returns immediately — the browser work never blocks the API."""
    active = await runs.active()
    if active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{_RUN_LABEL[active.kind]} is already in progress",
        )
    task = await _JOB_BY_KIND[kind].kiq()
    return RunTriggered(task_id=task.task_id, kind=kind)
