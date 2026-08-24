from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.scraping.enums import RunKind, RunStatus

RECENT_RUNS_LIMIT = 20


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: RunKind
    status: RunStatus
    items_collected: int
    detail: str | None
    started_at: datetime = Field(validation_alias="created_at")
    finished_at: datetime | None


class RunTriggered(BaseModel):
    task_id: str
    kind: RunKind


class AmazonCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    enabled: bool


class AmazonCategorySelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slugs: list[str] = Field(max_length=100)
